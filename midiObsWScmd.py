from asyncio.log import logger
import sys
from urllib import response
import json
from time import time
import asyncio
import simpleobsws

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

import midiObsJSONsetup as obsJSONsetup
import midiObsControls as obsControls

# https://github.com/obsproject/obs-websocket/blob/release/5.0.0/docs/generated/protocol.md

class ObsWScmd(object):

    def __init__(self, config, obsSocket):
        self.config = config
        # self.midiObsJSON = midiObsJSON
        # self.midiObsData = midiObsData
        self.obsSocket = obsSocket
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.scriptLogging = config["scriptLogging"]

    # def websocketConnect(self, wsAddress, wsPort, wsPassword):

    #     parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False)         
    #     cs = "ws://{0}:{1}".format(wsAddress, wsPort)
    #     obsSocket = simpleobsws.WebSocketClient(url = cs, password = wsPassword, 
    #                                             identification_parameters = parameters)

    #     return obsSocket

    async def websocketDisconnect(self):
        await self.obsSocket.disconnect() 
        return "ok"


    # https://www.theamplituhedron.com/articles/How-to-replicate-the-Arduino-map-function-in-Python-for-Raspberry-Pi/
    def rangeMap(self, x, in_min, in_max, out_min, out_max):
        if x < in_min:
            x = in_min
        if x > in_max:
            x = in_max

        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    def boolToInt(self, b):

        if type(b) is bool:
            if b is False:
                return 0
            if b is True:
                return 1

        these = ["1", "true", "yes"]
        b = str(b).lower()
        if b in these:
            return 1
        
        return 0


    async def makeRequest(self, rType, rData=None):
        response = None

        if not rData==None:
            # print(json.dumps(rData, indent=4, sort_keys=False))
            request = simpleobsws.Request(rType, rData)
        else:
            request = simpleobsws.Request(rType)

        # print(request)

        ret = await self.obsSocket.call(request)
        if ret.ok():             
            response = ret.responseData
        else:
            error = "single request failed, response data: {}".format(ret.responseData)
            print(error)
            print(str(request))

        # await self.obsSocket.disconnect() # Disconnect from the websocket server cleanly

        # print(json.dumps(response, indent=4, sort_keys=False))
        return response

    async def getInputVolume(self, source, db=True):    
        rType = "GetInputVolume"
        rData = {"inputName": source} 

        r = await self.makeRequest(rType, rData)

        if db:
            v = int(r["inputVolumeDb"])
            volume = self.rangeMap(v, -100, 26, 0, 127)
        else:
            v = int(r["inputVolumeMul"])
            volume = self.rangeMap(v, 0, 20, 0, 127)

        return volume


    async def setInputVolume(self, source, volume, db=True):
        rData = {}
        rData["inputName"] = source

        if db:
            v = self.rangeMap(volume, 0, 127, -100, 26)
            rData["inputVolumeDb"] = v
        else:
            v = self.rangeMap(volume, 0, 127, 0, 20)
            rData["inputVolumeMul"] = v

        rType = "SetInputVolume"
        r = await self.makeRequest(rType, rData)
    
        return r

    async def getInputList(self):

        rType = "GetInputList"
        rData = None
        r = await self.makeRequest(rType, rData)

        return r

    async def makeToggleRequest(self, action, rData=None):

        rType = action
        r = await self.makeRequest(rType, rData)
        return r

    async def doButtonAction(self, midiData, midiVal):
        response = None
        # print("-- doButtonAction pressed --")
        # print(json.dumps(midiData, indent=4, sort_keys=False))

        if midiData["section"] == "controls":
            response = await self.makeToggleRequest(midiData["action"])

        if midiData["section"] == "sources" and midiData["deviceType"] == "audio":
            response = await self.makeToggleRequest("ToggleInputMute", {"inputName": midiData["name"]})

        if midiData["section"] == "scenes":
            response = await self.makeToggleRequest("SetCurrentProgramScene", {"sceneName": midiData["name"] })

        return str(response)

    async def doChangeAction(self, midiData, midiVal):
        response = None
        # print("-- doChangeAction twiddled --")
        # print(json.dumps(midiData, indent=4, sort_keys=False))

        if midiData["deviceType"] == "audio":
            response = await self.setInputVolume(midiData["name"], midiData["changeValue"], db=True)

        return str(response)

    async def getCurrentValues(self, midiConfig):

        for m in midiConfig:
            if m["deviceType"] == "audio":
                volume = await self.getInputVolume(m["name"])
                m["changeValue"] = volume

                mute = await self.makeToggleRequest("GetInputMute", {"inputName": m["name"]})
                # print(str(mute))
                m["buttonValue"] = self.boolToInt(mute["inputMuted"])

                # print(json.dumps(m, indent=4, sort_keys=False))

        return midiConfig 