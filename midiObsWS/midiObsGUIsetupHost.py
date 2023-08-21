import PySimpleGUI as sg
import sys
import mido
import os
import time

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
# from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsWScmd import ObsWScmd
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsFiles import ObsFiles
# from midiObsWS.midiObsGUIcommon import ObsGUIcommon

class ObsGUIsetupHost(object):
    
    def __init__(self, guiTheme, guiMinSize, config):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        self.config = config
        self.scriptDir = config["scriptDir"]
        return

    async def showHostSetupGUI(self, midiObsConfigFile, midiObsDataFile, config):
        # fileSettings = obsJSONsetup.JsonFileSettings(self.scriptLogging)
        obsFiles = ObsFiles()
        obsMidi = ObsMidiSettings(None)
   
        filename = os.path.join(self.scriptDir, midiObsDataFile)
        error, midiObsData = obsFiles.loadJsonFile(filename)
        if error:
            exitAction = "error"
            return exitAction, midiObsData, None

        filename = os.path.join(self.scriptDir, midiObsConfigFile)
        error, obsConfig = obsFiles.loadJsonFile(filename)
        if error:
            exitAction = "error"
            return exitAction, obsConfig, None

        # config = obsConfig["config"]
        # config["scriptLogging"] = None
        obsCmd = ObsWScmd(config, None, None)
        
        updated = False

        err, midiInputs = obsMidi.listMidiDevices()
        err, midiOutputs = obsMidi.listMidiOutputDevices()

        midiOutputs.insert(0, "not set")

        # print("--- midiObsJson ---")
        # print(json.dumps(midiObsJSON, indent=4, sort_keys=False))
        # print("---config 1 ---")
        # print(json.dumps(config, indent=4, sort_keys=False))


        frameSize = (650,190)
        sg.theme(self.guiTheme)
        layout = []

        hostLayout = []
        hostLayout.append([sg.Text('OBS should be running and obs-websockets setup already.')])
        hostLayout.append([sg.Text("Server IP:", size=(15)), sg.In(key="wsAddress", enable_events=True, size=(30))])        
        hostLayout.append([sg.Text("Server Port:", size=(15)), sg.In(key="wsPort", enable_events=True, size=(30))])        
        hostLayout.append([sg.Text("Server Password:", size=(15)), sg.In(key="wsPassword", enable_events=True, size=(30))]) 
        hostLayout.append([sg.Text("", size=(15)), sg.Button("Test OBS Connection")])      
        hostLayout.append([sg.Text("", key="obsTestInfo")])

        layout.append([
          [sg.Frame('OBS Websocket Host Settings', hostLayout, font='Any 12', title_color='blue', size=frameSize)],
        ])

        midiLayout = []
        midiLayout.append([sg.Text('The Midi Device should be plugged in beforehand.')])
        midiLayout.append([sg.Text("Midi In:", size=(15)), sg.Combo(key="midiIn", enable_events=True, size=(30), values=midiInputs)])  
        midiLayout.append([sg.Text("Midi Out:", size=(15)), sg.Combo(key="midiOut", enable_events=True, size=(30), values=midiOutputs)])  
        midiLayout.append([sg.Text('Midi Out is used to add some feedback to your Midi Device, light up the button LEDs')])
        midiLayout.append([
            sg.Text("Midi Channel:", size=(15)), sg.In(key="midiChannel", enable_events=True, size=(5)),
            sg.Button("Set Midi Channel"),
            sg.Text("", key="midiChannelInfo")
        ]) 
        midiLayout.append([sg.Text('The Midi Channel is used with Midi Out, for general devices this is normally 10')]) 

        layout.append([
          [sg.Frame('Midi Device Settings', midiLayout, font='Any 12', title_color='blue', size=frameSize)],
        ])

        layout.append([sg.Button('Save and Close'), sg.Button('Close')]) #, sg.Button('Exit Program')])

        window = sg.Window('MIDI-OBS - Settings ', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)

        window.Element("wsAddress").update(value=config["wsAddress"])
        window.Element("wsPort").update(value=config["wsPort"])
        window.Element("wsPassword").update(value=config["wsPassword"])

        if not "midiDevice" in midiObsData or midiObsData["midiDevice"] == "":
            window.find_element("midiIn").update(value=midiInputs[0])
        else:      
            window.find_element("midiIn").update(value=midiObsData["midiDevice"])

        if not "midiOutputDevice" in midiObsData or midiObsData["midiOutputDevice"] == "":
            window.find_element("midiOut").update(value=midiOutputs[0])
        else:
            window.find_element("midiOut").update(value=midiObsData["midiOutputDevice"])

        window.Element("midiChannel").update(disabled=False)
        window.Element("midiChannel").update(value=midiObsData["midiChannel"])
        window.Element("midiChannel").update(disabled=True)

        while True:
            event, values = window.read(timeout = 100)

            if event == "Test OBS Connection":
                window.Element("obsTestInfo").update("")
                wsAddress = values["wsAddress"].strip()
                wsPort = values["wsPort"].strip()
                wsPassword = values["wsPassword"].strip()
                error, response = await obsCmd.obsTest(wsAddress, wsPort, wsPassword)
                window.Element("obsTestInfo").update(value=str(response))
                continue

            if event == "Set Midi Channel":
                channelSelected = False
                midiIn = values["midiIn"]
                channel = int(values["midiChannel"])
                if not midiIn or midiIn == "":
                    continue

                window.Element("midiChannelInfo").update(value="press any button on the midi device")
                with mido.open_input(midiIn) as inMidi:
                    ## clear anything already in the midi input buffer
                    while inMidi.receive(block=False) is not None:
                        pass

                    while True:                        
                        time.sleep(0.05)
                        ## read the midi device
                        for msg in inMidi.iter_pending():
                            
                            if msg:
                                channelSelected = True
                                channel = msg.channel
                                break
                        
                        if channelSelected:
                            window.Element("midiChannel").update(disabled=False)
                            window.Element("midiChannel").update(value=str(channel))
                            window.Element("midiChannel").update(disabled=True)
                            print(f"Midi Channel set to {channel}")
                            break

                        mevent, mvalues = window.read(timeout = 100)
                        if mevent == "Set Midi Channel":        
                            break

                    window.Element("midiChannelInfo").update(value="")

            if event == sg.WIN_CLOSED:
                exitAction = "exit"
                break

            if event == "Close":
                exitAction = "setup"
                break

            if event == "Save and Close":
                exitAction = "setup"
                updated = True
                config["wsAddress"] = values["wsAddress"].strip()
                config["wsPort"] = values["wsPort"].strip()
                config["wsPassword"] = values["wsPassword"].strip()

                midiObsData["midiDevice"] = values["midiIn"]
                if values["midiOut"] == "not set":
                    midiObsData["midiOutputDevice"] = ""
                else:
                    midiObsData["midiOutputDevice"] = values["midiOut"]

                midiObsData["midiChannel"] = int(values["midiChannel"])
                midiObsData["midiConfigured"] = 0 # this gets set to 1 when some button actions have been setup in showMidiSetupGUI
                break

            # window.Element("midiChannel").update(value=guiCommon.limitMidiChannels(str(values["midiChannel"])))
    
        window.close()

        # print("--- config ---")
        # print(json.dumps(config, indent=4, sort_keys=False))

        if updated:
            obsConfig["config"] = {}
            obsConfig["config"]["hostSet"] = 1
            obsConfig["config"]["wsAddress"] = config["wsAddress"]
            obsConfig["config"]["wsPort"] = config["wsPort"]
            obsConfig["config"]["wsPassword"] = config["wsPassword"]
            obsConfig["config"]["midiObsPath"] = self.config["midiObsPath"]
            obsConfig["config"]["midiObsDataFile"] = self.config["midiObsDataFile"]

            error, message = obsFiles.saveJSONfile(self.scriptDir, midiObsConfigFile, obsConfig)
            if error:
                exitAction = "error"
                config = message

            error, message = obsFiles.saveJSONfile(self.scriptDir, midiObsDataFile, midiObsData)
            if error:
                exitAction = "error"
                config = message            


        config["midiObsPath"] = self.config["midiObsPath"]
        config["midiObsDataFile"] = self.config["midiObsDataFile"]
        return exitAction, config, midiObsData
