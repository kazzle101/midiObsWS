
from asyncio.log import logger
import sys
from urllib import response
import mido
import time
import json
import os
from time import time
import asyncio
import simpleobsws

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

import midiObsJSONsetup as obsJSONsetup

# https://github.com/obsproject/obs-websocket/blob/4.x-current/docs/generated/protocol.md

class ObsControls(object):
    def __init__(self, config, midiObsJSON):
        # fileSettings =  obsJSONsetup.JsonFileSettings(config["scriptLogging"])

        self.connectError = ""
        # self.log = fileSettings.getLogger("midiObsWS")
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.scriptLogging = config["scriptLogging"]
        self.obsSocket = None
        self.midiObsJSON = midiObsJSON
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

        request = simpleobsws.Request(requestType, requestData)  # ('GetVersion') # Build a Request object

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


    # def getScenes(self):

    #     try:
    #         name = input("What's your name? ")
    #         yield from websocket.send(name)
    #         print("> {}".format(name))

    #         greeting = yield from websocket.recv()
    #         print("< {}".format(greeting))

    #     finally:
    #         yield from websocket.close()

    #     return 

    # def getSources(self):
    #     # https://github.com/obsproject/obs-websocket/blob/4.x-current/docs/generated/protocol.md#getmediasourceslist


    #     query = ({"action": "{\"request-type\": \"GetSourceTypesList\", \"statusCheckFlag\": \"false\"}", "request": "ToggleSourceVisibility", "target": j["item"]})

    #     try:
    #         yield from websocket.send(query)
    #         print("> {}".format())

    #         greeting = yield from websocket.recv()
    #         print("< {}".format(greeting))

    #     finally:
    #         yield from websocket.close()

    #     return 

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
            
        print(json.dumps(reqData, indent=4, sort_keys=False))
        return

    def setInputTypes(self, inputList):

        # print(json.dumps(self.midiObsJSON, indent=4, sort_keys=False))

        audio = []
        for a in self.midiObsJSON["inputKinds"]["audio"]:
            audio.append(a["name"])

        video = []
        for v in self.midiObsJSON["inputKinds"]["video"]:
            video.append(v["name"])

        for i in inputList:
            if i["inputKind"] in audio:
                i["inputType"] = "audio"
                continue
            if i["inputKind"] in video:
                i["inputType"] = "video"
                continue
            i["inputType"] = "unknown"

        return inputList

    def getCurrentInputsAndScenes(self):
        # GetInputList - input devices
        # GetSceneList - list of scenes

        request = ["GetInputList", "GetSceneList"]

        self.websocketConnect()
        loop = asyncio.get_event_loop()

        try:
            data = loop.run_until_complete(self.makeWebSocketSingleRequestBatch(request))
        except:
            return True, "cannot connect"

        if not data:
            return True, self.connectError

        if "inputs" in data["GetInputList"]:
            data["GetInputList"]["inputs"] = self.setInputTypes(data["GetInputList"]["inputs"])
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




    # def getInputKinds(self):
    #     self.websocketConnect()
    #     loop = asyncio.get_event_loop()

    #     data = loop.run_until_complete(self.makeWebSocketSingleRequest("GetInputList"))

    #     if self.connectError:
    #         return

    #     if "inputs" in data:
    #         data["inputs"] = self.setInputTypes(data["inputs"])
    #         print(json.dumps(data, indent=4, sort_keys=False))

    #     return

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