import sys
import simpleobsws
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsMidiSettings import ObsMidiSettings

# https://github.com/obsproject/obs-websocket/blob/release/5.0.0/docs/generated/protocol.md

class ObsWScmd(object):

    def __init__(self, config, scriptDir, obsSocket):
        self.config = config
        self.obsSocket = obsSocket
        self.wsAddress = config["wsAddress"]
        self.wsPort = config["wsPort"]
        self.wsPassword = config["wsPassword"]
        self.scriptDir = scriptDir

    # https://www.theamplituhedron.com/articles/How-to-replicate-the-Arduino-map-function-in-Python-for-Raspberry-Pi/
    def rangeMap(self, x, in_min, in_max, out_min, out_max):
        if x < in_min:
            x = in_min
        if x > in_max:
            x = in_max

        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    def varToBool(self, b):
        if isinstance(b, bool):
            return b
        
        these =  {"1", "true", "yes", "ja"}
        return str(b).strip().lower() in these

    async def makeRequest(self, obsSocket, rType, rData):
        response = None

        if rData is not None:
            request = simpleobsws.Request(rType, rData)
        else:
            request = simpleobsws.Request(rType)

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

    async def makeToggleRequest(self, rType, rData=None, byName=False):

        # print(rType)

        e, r = await self.makeRequest(self.obsSocket, rType, rData)
        return r

    async def getInputVolume(self, source, db=True, byName=False):

        if byName:
            rData = {"inputName": source}
        else:
            rData = {"inputUuid": source}

        e, r = await self.makeRequest(self.obsSocket, "GetInputVolume", rData)
        if db:
            v = int(r["inputVolumeDb"])
            volume = self.rangeMap(v, -100, 26, 0, 127)
        else:
            v = int(r["inputVolumeMul"])
            volume = self.rangeMap(v, 0, 20, 0, 127)

        return volume

    async def setInputVolume(self, source, volume, db=True, byName=False):
        rData = {}
        if byName:
            rData = {"inputName": source}
        else:
            rData = {"inputUuid": source}
            
        if db:
            v = self.rangeMap(volume, 0, 127, -100, 26)
            rData["inputVolumeDb"] = v
        else:
            v = self.rangeMap(volume, 0, 127, 0, 20)
            rData["inputVolumeMul"] = v

        e, r = await self.makeRequest(self.obsSocket, "SetInputVolume", rData)
        return r
    
    async def getCurrentProgramSceneName(self):
        rData = None
        e, r = await self.makeRequest(self.obsSocket, "GetCurrentProgramScene", rData)
        return r
    
    async def playMediaSource(self, midiData, buttonStatus):
        midi = ObsMidiSettings(None)
        midiOut = self.config["midiOut"]
        midiChannel = self.config["midiChannel"]
    
        rData = {
            'inputUuid': midiData["uuid"],
            'mediaAction': 'OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART'
        }
        e, response = await self.makeRequest(self.obsSocket, "TriggerMediaInputAction", rData)
        buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, midiData["midiID"], buttonStatus, "on")
        
        if response is None:
            response = "OK"
        
        return str(response), buttonStatus

    async def doSceneChange(self, allInputs, midiData, buttonStatus):
        midi = ObsMidiSettings(None)
        midiOut = self.config["midiOut"]
        midiChannel = self.config["midiChannel"]

        # turn all scenes LEDs off
        for o in allInputs:
            if o["section"] == "scenes" and o["midiID"] >= 0:
                buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, o["midiID"], buttonStatus, "off")

        ## turn only the selected scene LED on
        response = await self.makeToggleRequest("SetCurrentProgramScene", {"sceneUuid": midiData["uuid"] })
        buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, midiData["midiID"], buttonStatus, "on")

        if response is None:
            response = "OK"

        return str(response), buttonStatus


    async def doButtonAction(self, allInput, buttonStatus):
        midi = ObsMidiSettings(None)
        midiOut = self.config["midiOut"]
        midiChannel = self.config["midiChannel"]   
        midiID = allInput["midiID"]
        
        response = False
        val = self.varToBool(allInput["value"])
        if allInput["section"] == "controls":
            if allInput["uuid"] == "SetStudioModeEnabled":
                response = await self.makeToggleRequest(allInput["uuid"], {'studioModeEnabled': val})                
            else:
                response = await self.makeToggleRequest(allInput["uuid"])
                
            if response is None or not "ouputActive" in response:
                response = {}

            buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, 
                                        midiID, buttonStatus, response.get("outputActive", val))

        elif allInput["section"] == "sourcesBtn":
            if allInput["type"] == "audio":
                response = await self.makeToggleRequest("SetInputMute", {"inputMuted": val, "inputUuid": allInput["uuid"]})                
                buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, midiID, buttonStatus, val)
            else:
                response = await self.makeToggleRequest(allInput["uuid"])
                buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, midiID, buttonStatus, val)
            
        if response is None or len(response) == 0:
            response = f"OK: {val}"
                
        return str(response), buttonStatus

    async def doChangeAction(self, allInput, buttonStatus):
        midi = ObsMidiSettings(None)
        midiOut = self.config["midiOut"]
        midiChannel = self.config["midiChannel"]    
        
        response = False
        if allInput["type"] == "audio":
            response = await self.setInputVolume(allInput["uuid"], allInput["value"], db=True)
            buttonStatus = await midi.setMidiDeviceChangeValue(midiOut, midiChannel, allInput["midiID"], buttonStatus, allInput["value"])
     
        if response is None:
            response = f"OK: {allInput['value']}"
     
        return str(response), buttonStatus

    def toggleToGet(self, toggleAction):

        if "Record" in toggleAction:
            return "GetRecordStatus"

        if "StudioMode" in toggleAction:
            return "GetStudioModeEnabled"

        if "Stream" in toggleAction:
            return "GetStreamStatus"

        if "Virtual" in toggleAction:
            return "GetVirtualCamStatus"
        
        return False

    ## sets the LED's on the MidiOut Device with the current values in OBS
    async def setCurrentValues(self, allInputs):
        midi = ObsMidiSettings(None)
        
        if not self.config["midiOut"] or self.config["midiOut"] == "":
            print("midiOut not set")
            return allInputs

        midiOut = self.config["midiOut"]
        midiChannel = self.config["midiChannel"]
        midi.midiReset(midiOut)
        
        buttonStatus = []
        currentSceneUuid = None
        currentProgramSceneName = await self.getCurrentProgramSceneName()
        if "currentProgramSceneName" in currentProgramSceneName:
            currentSceneUuid = str(currentProgramSceneName["sceneUuid"])
            
        for a in allInputs:
            section, id, type = a["name"].split("_", 2)
                        
            if a["section"] == "controls":
                action = self.toggleToGet(a["uuid"])
                if action:
                    response = await self.makeToggleRequest(action)
                    if "outputActive" in response:
                        buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, a["midiID"], buttonStatus, response["outputActive"]) 
                    elif "studioModeEnabled" in response:
                        buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, a["midiID"], buttonStatus, response["studioModeEnabled"])
                        
            elif a["section"] == "scenes":
                if a["uuid"] == currentSceneUuid:
                    buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, a["midiID"], buttonStatus, "on")
                else:
                    buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, a["midiID"], buttonStatus, "off")
                    
            ## just turn the buttons LED on
            elif a["section"] == "sourcesBtn":
                buttonStatus = await midi.setMidiDeviceKeyOnOrOff(midiOut, midiChannel, a["midiID"], buttonStatus, "on")
                                
            elif a["section"] == "sourcesRot":
                volume = await self.getInputVolume(a["uuid"])                
                buttonStatus = await midi.setMidiDeviceChangeValue(midiOut, midiChannel, a["midiID"], buttonStatus, volume)
        
        return allInputs

    async def obsTest(self, wsAddress, wsPort, wsPassword):

        obs = ObsControls(self.config)

        err, obsSocket = obs.websocketTestConnect(wsAddress, wsPort, wsPassword)
        if err:
            return True, err
        
        try:
            await obsSocket.connect()               # Make the connection to obs-websocket
            await obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            print("Cannot connect to OBS (obsTest)")
            print("{}".format(sys.exc_info()[1]))
            return True, "error: Cannot connect to OBS: {}".format(sys.exc_info()[1])

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
