
import sys
import asyncio
import simpleobsws
import json

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

# import midiObsWS.midiObsJSONsetup as obsJSONsetup

# https://github.com/IRLToolkit/simpleobsws

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

class ObsControls(object):
    def __init__(self, config):
        self.connectError = ""
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.obsSocket = None
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
            print("webSocketTestConnect ERROR")
            print("{}".format(sys.exc_info()[1]))
            print(obsSocket)
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

    async def makeWebSocketSingleRequestBatch(self, request):

        response = {}
        try:
            await self.obsSocket.connect() # Make the connection to obs-websocket
            await self.obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            print("{}".format(sys.exc_info()[1]))
            error = "Cannot connect to OBS (RequestBatch): {}".format(sys.exc_info()[1])
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
            return True, "cannot connect to OBS WebSocket"

        if not data:
            return True, self.connectError

        return False, data
