import sys
import simpleobsws
import ast
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsMidiSettings import ObsMidiSettings

# https://github.com/obsproject/obs-websocket/blob/release/5.0.0/docs/generated/protocol.md

class ObsWScmd(object):

    def __init__(self, config, obsSocket, midiDeviceInfo, scenesSectionData):
        self.config = config
        # self.midiObsJSON = midiObsJSON
        # self.midiObsData = midiObsData
        self.midiDeviceInfo = midiDeviceInfo
        self.obsSocket = obsSocket
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.scriptLogging = config["scriptLogging"]
        self.scenesSectionData = scenesSectionData

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


    async def makeRequest(self, obsSocket, rType, rData):
        response = None

        if not rData==None:
            # print(json.dumps(rData, indent=4, sort_keys=False))
            request = simpleobsws.Request(rType, rData)
        else:
            request = simpleobsws.Request(rType)

        # print(request)

        try:
            ret = await obsSocket.call(request)
            if ret.ok():
                response = ret.responseData
            else:
                error = "single request failed, response data: {}".format(ret.responseData)
                print(error)
                print(str(request))
                return True, error
        except Exception as e:
            print(e)
            return True, e


        # the response string is encapsulated with single quotes instead of doubles
        # so json.loads(response) won't work. ast.literal_eval fixes that.

        # response = ast.literal_eval(response)
        # print(json.dumps(response, indent=4, sort_keys=False))
        return False, response

    async def getInputVolume(self, source, db=True):
        rType = "GetInputVolume"
        rData = {"inputName": source}

        e, r = await self.makeRequest(self.obsSocket, rType, rData)

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
        e, r = await self.makeRequest(self.obsSocket, rType, rData)

        return r

    async def getInputList(self):

        rType = "GetInputList"
        rData = None
        e, r = await self.makeRequest(self.obsSocket, rType, rData)

        return r

    async def getCurrentProgramSceneName(self):

        rType = "GetCurrentProgramScene"
        rData = None
        e, r = await self.makeRequest(self.obsSocket, rType, rData)
        return r

    async def makeToggleRequest(self, action, rData=None):

        rType = action
        e, r = await self.makeRequest(self.obsSocket, rType, rData)
        return r

    async def doSceneChange(self, obsData, midiData, buttonStatus):
        midi = ObsMidiSettings(None)
        midiOutputDevice = self.midiDeviceInfo["midiOutputDevice"]
        midiChannel = self.midiDeviceInfo["midiChannel"]

        if midiOutputDevice is None:
            return obsData, buttonStatus

        if self.scenesSectionData is None:
            return obsData, buttonStatus

        # print("doSceneChange")
        # print(midiData)
        # print(buttonStatus)

        # turn all scenes LEDs off
        for o in obsData:
            if o["section"] == "scenes" and o["buttonID"] > 0:
                buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOutputDevice, midiChannel, o["buttonID"], buttonStatus, "off")

        ## turn only the selected scene LED on
        response = await self.makeToggleRequest("SetCurrentProgramScene", {"sceneName": midiData["name"] })
        buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOutputDevice, midiChannel, midiData["buttonID"], buttonStatus, "on")

        return str(response), buttonStatus

    async def doButtonAction(self, midiData, midiVal, buttonStatus):

        response = None
        if midiData["section"] == "controls":
            if midiData["action"] == "SetStudioModeEnabled":
                response = await self.makeToggleRequest("SetStudioModeEnabled", midiData["buttonValue"])
            else:
                response = await self.makeToggleRequest(midiData["action"])

        if midiData["section"] == "sources" and midiData["deviceType"] == "audio":
            response = await self.makeToggleRequest("ToggleInputMute", {"inputName": midiData["name"]})

        if midiData["section"] == "scenes":
            response = await self.makeToggleRequest("SetCurrentProgramScene", {"sceneName": midiData["name"] })

        buttonStatus = await self.setMidiOutputLED(midiVal, buttonStatus)

        return str(response), buttonStatus

    async def doChangeAction(self, midiData, midiVal, buttonStatus):
        response = None
        # print("-- doChangeAction twiddled --")
        # print(json.dumps(midiData, indent=4, sort_keys=False))

        if midiData["deviceType"] == "audio":
            response = await self.setInputVolume(midiData["name"], midiData["changeValue"], db=True)

        buttonStatus = await self.setMidiOutputLED(midiVal, buttonStatus)

        return str(response), buttonStatus

    async def setMidiOutputLED(self, midiVal, buttonStatus):
        midi = ObsMidiSettings(None)

        if self.midiDeviceInfo == None:
            return buttonStatus

        if midiVal == None:
            return buttonStatus

        midiOut = self.midiDeviceInfo["midiOutputDevice"]
        buttonStatus = await midi.setMidiDeviceKey(midiOut, midiVal, buttonStatus)
        return buttonStatus


    def toggleToGet(self, toggleAction):

        if "Record" in toggleAction:
            return "GetRecordStatus"

        if "StudioMode" in toggleAction:
            return "GetStudioModeEnabled"

        return False

    def getValFromResponse(self, data):
        # p = re.compile('(?<!\\\\)\'')

        # print("getValFromResponse")
        # print(type(data))
        # print(data)


        try:
            # response = p.sub('\"', response)
            # response.replace("False,","\"False\",")
            # response.replace("True,","\"True\",")
            # print(response)
            # data = json.loads(response)
            #if type(response) == str:
            data = ast.literal_eval(data)
            # print(json.dumps(data, indent=4, sort_keys=False))
        except Exception as e:
            print("error:")
            print(e)
            return False

        if type(data) != dict:
            return False

        if "outputActive" in data:
            return data["outputActive"]

        if "studioModeEnabled" in data:
            return data["studioModeEnabled"]

        if "inputMuted" in data:
            return data["inputMuted"]

        return False


    async def getCurrentValues(self, obsData, midiDeviceInfo):

        midi = ObsMidiSettings(None)
        buttonStatus = []
        changeStatus = []
        bs = []
        midiOutputDevice = midiDeviceInfo["midiOutputDevice"]
        midiChannel =  midiDeviceInfo["midiChannel"]

        midi.midiReset(midiDeviceInfo["midiOutputDevice"])

        # print("getCurrentValues")
        # print(json.dumps(obsData, indent=4, sort_keys=False))
        # print(json.dumps(midiDeviceInfo, indent=4, sort_keys=False))

        currentSceneName = None
        currentProgramSceneName = await self.getCurrentProgramSceneName()
        if "currentProgramSceneName" in currentProgramSceneName:
            currentSceneName = str(currentProgramSceneName["currentProgramSceneName"])

        for m in obsData:
            if m["section"] == "controls" and m["buttonID"] >= 0:

                # print(json.dumps(m, indent=4, sort_keys=False))

                action = self.toggleToGet(m["action"])
                if action:
                    data = { "section": m["section"], "name": m["name"],
                             "action": action, "deviceType": m["deviceType"],
                             "buttonValue": m["buttonValue"]}

                    val, bs = await self.doButtonAction(data, None, bs) # midiVal)

                    # print(json.dumps(data, indent=4, sort_keys=False))
                    # print(json.dumps(val, indent=4, sort_keys=False))

                    midiVal = midi.MIDIvalue()
                    midiVal.status = "button"
                    midiVal.channel = midiDeviceInfo["midiChannel"]
                    midiVal.control = m["buttonID"]
                    midiVal.value = self.getValFromResponse(val)
                    buttonStatus = await midi.setMidiDeviceKey(midiDeviceInfo["midiOutputDevice"], midiVal, buttonStatus)

            if m["section"] == "scenes" and m["buttonID"] >= 0:
                if m["name"] == currentSceneName:
                    buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOutputDevice, midiChannel, m["buttonID"], buttonStatus, "on")
                else:
                    buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOutputDevice, midiChannel, m["buttonID"], buttonStatus, "off")

            if m["deviceType"] == "audio":
                volume = await self.getInputVolume(m["name"])
                m["changeValue"] = volume

                midiVal = midi.MIDIvalue()
                midiVal.status = "change"
                midiVal.channel = midiChannel
                midiVal.control = m["changeID"]
                midiVal.value = volume
                changeStatus = await midi.setMidiDeviceKey(midiOutputDevice, midiVal, changeStatus)

                mute = await self.makeToggleRequest("GetInputMute", {"inputName": m["name"]})
                # print(str(mute))
                m["buttonValue"] = self.boolToInt(mute["inputMuted"])

                midiVal = midi.MIDIvalue()
                midiVal.status = "button"
                midiVal.channel = midiChannel
                midiVal.control = m["buttonID"]
                midiVal.value = mute["inputMuted"]
                buttonStatus = await midi.setMidiDeviceKey(midiOutputDevice, midiVal, buttonStatus)

        return buttonStatus, obsData

    async def obsTest(self, wsAddress, wsPort, wsPassword):

        obs = ObsControls(self.config, None, None)

        err, obsSocket = obs.websocketTestConnect(wsAddress, wsPort, wsPassword)
        if err:
            return True, err

        try:
            await obsSocket.connect()               # Make the connection to obs-websocket
            await obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            return True, "error: Cannot connect to OBS: {}".format(sys.exc_info()[1])

        # print(obsSocket)

        error, response = await self.makeRequest(obsSocket, "GetVersion", None)
        if error:
            return True, response

        if not "obsWebSocketVersion" in response:
            await obsSocket.disconnect()
            return True, "expected Websocket version not found in response"

        await obsSocket.disconnect()
        wsVersion = response["obsWebSocketVersion"]
        obsVersion = response["obsVersion"]
        return False, f"OK, OBS Version: {obsVersion}, obs-Websocket Version: {wsVersion}"
