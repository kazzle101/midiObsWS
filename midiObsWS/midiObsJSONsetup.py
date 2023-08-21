import sys
import json

if __name__ == "__main__":
    print("this python script only works from: midi-obs-ws.py")
    sys.exit(0)


class ObsJSONsetup(object):
    def __init__(self, scriptLogging):
        self.scriptLogging = scriptLogging
        return

    # I couldn't find anything useful to do with the video devices directly
    # switching between video feeds is done with scenes
    def filterOutVideoDevices(self, data):

        cfg = []

        # print("--- filterOutVideoDevices ---")
        # print(json.dumps(data, indent=4, sort_keys=False))

        if "deviceType" in data[0]:
            for d in data:
                if d["deviceType"] != "video":
                    cfg.append(d)
            return cfg

        if "inputType" in data[0]:
            for d in data:
                if d["inputType"] != "video":
                    cfg.append(d)
            return cfg

        return data

    ## create the midiObsData.json midiConfiguration from the inputsAndScenes
    def makeDefaultMidiObsData(self, midiObsData, midiObsConfig, inputsAndScenes):

        # print("XXXXXX makeDefaultMidiObsData")
        # print(json.dumps(midiObsData, indent=4, sort_keys=False))

        # if midiObsData["midiConfiguration"]:
        #     return midiObsData

        if midiObsData["midiConfigured"] == 1:
            return midiObsData

        # midiObsData = {}
        # midiObsData["midiDevice"] = midiDevices[0]
        # midiObsData["midiOutputDevice"] = ""
        # midiObsData["midiChannel"] = 10
        midiObsData["midiConfigured"] = 0

        # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))

        midiConfig = []
        for b in midiObsConfig["buttons"]:
            data = {"section": "controls",
                    "action": b["name"],
                    "name": b["display"],
                    # "control": "button",
                    "buttonID": -1,
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": "" }
            midiConfig.append(data)

        for s in inputsAndScenes["GetInputList"]["inputs"]:
            data =  {"section": "sources",
                    "action": s["inputName"],
                    "name": s["inputName"],
                    # "control": "",
                    "buttonID": -1,
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": s["inputType"] }
            midiConfig.append(data)

        for s in inputsAndScenes["GetSceneList"]["scenes"]:
            data =  {"section": "scenes",
                    "action": s["sceneName"],
                    "name": s["sceneName"],
                    # "control": "",
                    "buttonID": -1,
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": "" }
            midiConfig.append(data)

        midiObsData["midiConfiguration"] = midiConfig

        return midiObsData

    # for the midiObsConfig.json file
    def createDefaultConfigData(self, scriptDir):

        config = { "hostSet": 0, "wsAddress": "localhost", "wsPort": "4455",
                   "wsPassword": "", "midiObsPath": scriptDir, 
                   "midiObsDataFile": "midiObsData.json"
                }
        buttons = [
            { "name": "StartRecord", "display": "Start Recording" },
            { "name": "StopRecord",  "display": "Stop Recording" },
            { "name": "PauseRecord",  "display": "Pause Recording" },
            { "name": "ToggleRecord",  "display": "Toggle Recording" },
            { "name": "ToggleRecordPause",  "display": "Toggle Pause Recording" },
            { "name": "ResumeRecord", "display": "Resume Recording" },
            { "name": "StartVirtualCam", "display": "Start Virtual Camera" },
            { "name": "StopVirtualCam", "display": "Stop Virtual Camera" },
            { "name": "ToggleVirtualCam",  "display": "Toggle Virtual Camera" },
            { "name": "StartStream", "display": "Start Streaming" },
            { "name": "StopStream", "display": "Stop Streaming" },
            { "name": "ToggleStream",  "display": "Toggle Streaming" },
            { "name": "SetStudioModeEnabled",  "display": "Toggle Studio Mode" }
        ]

        inputAudio = [
            { "name": "wasapi_input_capture", "display": "wasapi input capture" },
            { "name": "wasapi_output_capture", "display": "wasapi output capture" },
            { "name": "coreaudio_input_capture", "display": "coreaudio input capture" },
            { "name": "coreaudio_output_capture", "display": "coreaudio output capture" },
            { "name": "pulse_input_capture", "display": "pulse input capture" },
            { "name": "pulse_output_capture", "display": "pulse output capture" }
        ]
        inputVideo =  [
            { "name": "dshow_input", "display": "dshow input" },
            { "name": "ffmpeg_source", "display": "ffmpeg source" },
            { "name": "monitor_capture", "display": "monitor capture" },
            { "name": "window_capture", "display": "window capture" },
            { "name": "av_capture_input", "display": "av capture input" },
            { "name": "v4l2_input", "display": "v4l2 input" }
        ]

        outputAudio = [
            { "name": "ffmpeg_muxer", "display": "simple_file_output" }
        ]

        outputVideo = [
            { "name": "virtualcam_output", "display": "virtualcam_output" }
        ]

        data = {}
        data["config"] = config
        data["buttons"] = buttons
        data["inputKinds"] = {}
        data["inputKinds"]["audio"] = inputAudio
        data["inputKinds"]["video"] = inputVideo
        data["outputKinds"] = {}
        data["outputKinds"]["audio"] = outputAudio
        data["outputKinds"]["video"] = outputVideo

        return data

    # for the midiObsData.json file
    def createDefaultData(self):

        data = {}
        data["midiDevice"] = ""
        data["midiOutput"] = ""
        data["midiChannel"] = 10
        data["midiConfigured"] = 0
        data["midiOutputDevice"] = ""
        data["midiConfiguration"] = []

        return data