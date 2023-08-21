
from asyncio.log import logger
import sys
from urllib import response
from time import time
import asyncio
import simpleobsws
import json

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

# import midiObsWS.midiObsJSONsetup as obsJSONsetup

# https://github.com/IRLToolkit/simpleobsws

# https://github.com/obsproject/obs-websocket/blob/4.x-current/docs/generated/protocol.md

class ObsControls(object):
    def __init__(self, config, midiObsData, midiObsConfig):
        # fileSettings =  obsJSONsetup.JsonFileSettings(config["scriptLogging"])

        self.connectError = ""
        # self.log = fileSettings.getLogger("midiObsWS")
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.scriptLogging = config["scriptLogging"]
        self.obsSocket = None
        self.midiObsData = midiObsData
        self.midiObsConfig = midiObsConfig
        self.config = config
        return

    def websocketTestConnect(self, wsAddress, wsPort, wsPassword):
        parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False)         
        cs = "ws://{0}:{1}".format(wsAddress, wsPort)
        try:
            obsSocket = simpleobsws.WebSocketClient(url = cs, 
                                    password = wsPassword, 
                                    identification_parameters = parameters)
        except:
            return True, "cannot make socket client connection string"

        return False, obsSocket

    def websocketConnect(self):

        parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False)         
        cs = "ws://{0}:{1}".format(self.wsAddress, self.wsPort)
        obsSocket = simpleobsws.WebSocketClient(url = cs, 
                                    password = self.wsPassword, 
                                    identification_parameters = parameters)

        # print(obsSocket)

        self.obsSocket = obsSocket
        return obsSocket

    async def websocketDisconnect(self):
        await self.obsSocket.disconnect() 
        return "ok"

    async def obsConnect(self, obsSocket):

        try:
            await obsSocket.connect() # Make the connection to obs-websocket
            await obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            error = "Cannot connect to OBS: {}".format(sys.exc_info()[1])
            return False, error

        self.obsSocket = obsSocket
        return True, obsSocket


    async def obsWebsocketRequest(self, obsSocket, request):

        response = None
        error = ""

        request = simpleobsws.Request(request)  # ('GetVersion') # Build a Request object
        ret = await obsSocket.call(request)
        if ret.ok():             
            response = ret.responseData
        else:
            error = "request failed, response data: {}".format(ret.responseData)

        return response, error


    async def makeWebSocketSingleRequest(self, requestType, requestData=None):

        response = None
        try:
            await self.obsSocket.connect() # Make the connection to obs-websocket
            await self.obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            error = "Cannot connect to OBS: {}".format(sys.exc_info()[1])
            self.connectError = str(error)
            return None
        
        request = simpleobsws.Request(requestType, requestData) # Build a Request object

        # print(request)

        ret = await self.obsSocket.call(request)
        if ret.ok():             
            response = ret.responseData
        else:
            error = "single request failed, response data: {}".format(ret.responseData)
            print(error)
            self.connectError = error

        await self.obsSocket.disconnect() # Disconnect from the websocket server cleanly

        return response

    async def makeWebSocketSingleRequestBatch(self, request):

        response = {}
        try:
            await self.obsSocket.connect() # Make the connection to obs-websocket
            await self.obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            error = "Cannot connect to OBS: {}".format(sys.exc_info()[1])
            self.connectError = str(error)
            return None

        requests = []
        for r in request:
            requests.append(simpleobsws.Request(r)) # Build a Request object, then append it to the batch

        ret = await self.obsSocket.call_batch(requests, halt_on_failure = False) # Perform the request batch

        c=0
        for result in ret:
            if result.ok(): # Check if the request succeeded
                response[request[c]] = result.responseData
            else:                                 
                error = "batch request failed, response data: {}".format(ret.responseData)
                print(error)
                self.connectError = error
                response[request[c]] = result.responseData

            c+=1

        await self.obsSocket.disconnect()

        return response

    def listRequestTypes(self, versionData, reqType):

        if versionData is None:
            return

        reqData = []
        reqType = reqType.lower()
        data = versionData["availableRequests"]
        for d in data:
            c = d.lower()
            if c.startswith(reqType):
                reqData.append(d)
            
        # print(json.dumps(reqData, indent=4, sort_keys=False))
        return

    def setInputTypes(self, inputList):
    
        hasUnknown = False
        audio = []
        for a in self.midiObsConfig["inputKinds"]["audio"]:
            audio.append(a["name"])

        video = []
        for v in self.midiObsConfig["inputKinds"]["video"]:
            video.append(v["name"])

        for i in inputList:
            if i["inputKind"] in audio:
                i["inputType"] = "audio"
                continue
            if i["inputKind"] in video:
                i["inputType"] = "video"
                continue
            i["inputType"] = "unknown"
            hasUnknown = True

        # print("--- setInputTypes ---")
        # print(json.dumps(inputList, indent=4, sort_keys=False))

        return inputList, hasUnknown
    
    def setOutputTypes(self, outputList):

        hasUnknown = False
        audio = []
        for a in self.midiObsConfig["outputKinds"]["audio"]:
            audio.append(a["name"])

        video = []
        for v in self.midiObsConfig["outputKinds"]["video"]:
            video.append(v["name"])

        output = []

        for o in outputList:
            op = {}
            op["outputKind"] = o["outputKind"]
            op["outputName"] = o["outputName"]

            af = o["outputFlags"]["OBS_OUTPUT_AUDIO"]
            vf = o["outputFlags"]["OBS_OUTPUT_VIDEO"]

            if o["outputKind"] in audio:
                op["inConfigAudio"] = True
            if o["outputKind"] in video:
                op["inConfigVideo"] = True                

            if af and vf :
                op["outputType"] = "audio, video"
            elif af:
                op["outputType"] = "audio"
            elif vf:
                op["outputType"] = "video"
            else:
                op["outputType"] = "unknown"
                hasUnknown = True

            output.append(op)

        return output, hasUnknown

    def getCurrentInputsAndScenes(self, wsConfig=None):
        # GetInputList - input devices
        # GetSceneList - list of scenes

        request = ["GetInputList", "GetSceneList"]

        if wsConfig is not None and "Password" in wsConfig:
            self.wsAddress = wsConfig["Address"]
            self.wsPort = wsConfig["Port"]
            self.wsPassword = wsConfig["Password"]
        
        self.websocketConnect()
        loop = asyncio.get_event_loop()

        try:
            data = loop.run_until_complete(self.makeWebSocketSingleRequestBatch(request))
        except:
            return True, "cannot connect"

        if not data:
            return True, self.connectError

        if "inputs" in data["GetInputList"]:
            data["GetInputList"]["inputs"], hasUnkown = self.setInputTypes(data["GetInputList"]["inputs"])
        else:
            data["GetInputList"]["inputs"] = []

        if not "scenes" in data["GetSceneList"]:
            data["GetSceneList"]["scenes"] = []

        return False, data

    # def sliderControls(self):
    #     ## also includes twiddly knobs
    #     return

    # def makeGetSetList(self):
    #     self.websocketConnect()
    #     loop = asyncio.get_event_loop()

    #     data = loop.run_until_complete(self.makeWebSocketSingleRequest("GetVersion"))

    #     if self.connectError:
    #         return

    #     getOpts = []
    #     setOpts = []
    #     otherOpts = []

    #     for d in data["availableRequests"]:

    #         if d.lower().startswith('get'):
    #             getOpts.append(d)
    #         elif d.lower().startswith('set'):
    #             setOpts.append(d)
    #         else:
    #             otherOpts.append(d)

    #     getOpts.sort()
    #     setOpts.sort()
    #     otherOpts.sort()

    #     requests = {}
    #     requests["GetRequests"] = getOpts
    #     requests["SetRequests"] = setOpts
    #     requests["OtherRequests"] = otherOpts

    #     print(json.dumps(requests, indent=4, sort_keys=False))

    #     requests

    def getInputKinds(self):
        self.websocketConnect()
        loop = asyncio.get_event_loop()

        #data = loop.run_until_complete(self.obsWebsocketRequest(self.obsConnect, "GetSourcesList"))

        dataInputs = loop.run_until_complete(self.makeWebSocketSingleRequest("GetInputList"))
        # dataOutput = loop.run_until_complete(self.makeWebSocketSingleRequest("GetOutputList"))

        # data = {"dinput": dataInput, "dOutput": dataOutput}

        # print(json.dumps(data["inputs"], indent=4, sort_keys=False))

        if self.connectError:
            return

        unknownInput = False
        unknownOutput = False

        # if "outputs" in dataOutput:
        #     dataOutput["outputs"], unknownOutput = self.setOutputTypes(dataOutput["outputs"])
        #     print(json.dumps(dataOutput, indent=4, sort_keys=False))


        if "inputs" in dataInputs:
            dataInputs["inputs"], unknownInput = self.setInputTypes(dataInputs["inputs"])
            print(json.dumps(dataInputs, indent=4, sort_keys=False))

        if unknownOutput or unknownInput:
            cFile = self.config["midiObsConfigFile"]
            print("One or more unknown input kind is on the list above, please examine ")
            print("to see if it is audio or video and add to the inputKinds list in the ")
            print(f"{cFile} as appropriate.")

        return

    # def getWSversion(self):
    #     self.websocketConnect()
    #     loop = asyncio.get_event_loop()

    #     request = "GetVersion"

    #     data = loop.run_until_complete(self.makeWebSocketSingleRequest(request))

    #     print(json.dumps(data, indent=4, sort_keys=False))

    #     return

    # def testOBSstuff(self):
    #     self.websocketConnect()
    #     loop = asyncio.get_event_loop()

    #     request = "SaveSourceScreenshot"

    #     data = loop.run_until_complete(self.makeWebSocketSingleRequest(request))

    #     print(json.dumps(data, indent=4, sort_keys=False))

    #     return