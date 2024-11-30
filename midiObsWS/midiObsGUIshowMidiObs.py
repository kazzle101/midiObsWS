import FreeSimpleGUI as sg
import sys
import mido
import time
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsDatabase import ObsDatabase
from midiObsWS.midiObsWScmd import ObsWScmd
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsGUIcommon import ObsGUIcommon

class ObsGUIshowMidiObs(object):
    
    def __init__(self, guiTheme, guiMinSize, scriptDir):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        self.scriptDir = scriptDir
        return

    async def showMidiObsGUI(self, config):
        db = ObsDatabase(self.scriptDir)
        guiCommon = ObsGUIcommon(config)
        obsControls = ObsControls(config)
        midiSetup = ObsMidiSettings(config)

        midiIn = config["midiIn"]
        buttonStatus = []

        wsControls = db.getControlsList(True)
        userInputs = db.getInputsList(True, True)
        userScenes = db.getScenesList(True)

        allInputs = []
        data, names = guiCommon.makeSectionControls(None, wsControls)
        allInputs = guiCommon.setAllnames(allInputs, names)
        data, names = guiCommon.makeSectionScenes(None, userScenes)
        allInputs = guiCommon.setAllnames(allInputs, names)
        data, names = guiCommon.makeSectionSourcesBtn(None, userInputs)
        allInputs = guiCommon.setAllnames(allInputs, names)
        data, names = guiCommon.makeSectionSourcesRot(None, userInputs)
        allInputs = guiCommon.setAllnames(allInputs, names)

        # print(json.dumps(allInputs, indent=4, sort_keys=False)
        
        obsSocket = obsControls.websocketConnect()     # send the connection string

        try:
            await obsSocket.connect()               # Make the connection to obs-websocket
            await obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            return "error", "Cannot connect to OBS: {}".format(sys.exc_info()[1])

        exitAction = "close"        
        obsCmd = ObsWScmd(config, self.scriptDir, obsSocket)
        allInputs = await obsCmd.setCurrentValues(allInputs)
        
        exitFromMidi = False
        lastIndex = -1
        lastName = None
        response = None

        sg.theme(self.guiTheme)
        layout = [[sg.Text(f'USING MIDI INPUT: {midiIn}')]]

        layout.append([sg.Text("Midi input:", size=(15)), sg.In(key="midiIn", readonly=True, enable_events=False, size=(3))])        
        layout.append([sg.Text("Midi value:", size=(15)), sg.In(key="midiVal", readonly=True, enable_events=False, size=(3))])
        layout.append([sg.Text("Midi type:", size=(15)), sg.In(key="midiType", readonly=True, enable_events=False, size=(20))])
        layout.append([sg.Text(" ")])
        layout.append([sg.Text("OBS action:", size=(15)), sg.In(key="obsAction", readonly=True, enable_events=False, size=(50))])
        layout.append([sg.Text("OBS value:", size=(15)), sg.In(key="obsValue", readonly=True,  enable_events=False, size=(20))])

        layout.append([sg.vtop([sg.Text("OBS response:", size=(15)), 
                       sg.Multiline(key="obsResponse", disabled=True, enable_events=False, font=("Courier New", 10), size=(60,10))])])

        layout.append([sg.Button('Setup'), sg.Button('Exit Program')]) #, sg.Button('Close')

        window = sg.Window('MIDI-OBS', layout, return_keyboard_events=True, 
                           resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)
        window.force_focus()

        with mido.open_input(midiIn) as inMidi:
            ## clear anything already in the midi input buffer
            while inMidi.receive(block=False) is not None:
                pass

            while True:
                time.sleep(0.05)

                ## read the midi device
                for msg in inMidi.iter_pending():
                    midiVal = midiSetup.midiToObj(msg)

                    # print("showMidiInputGUI  ID: {: >2}, status: {}, value: {: >3}"
                    #     .format(midiVal.control, midiVal.status, midiVal.value))

                    window.Element("midiIn").update(value=guiCommon.stringNumbersOnly(str(midiVal.control)))
                    window.Element("midiVal").update(str(midiVal.value))
                    window.Element("midiType").update(midiVal.status)

                    action, allInputs, midiData = await guiCommon.setObsDataValue(midiVal, allInputs)
                    if not action:
                        continue

                    if lastName != midiData["name"]:                        
                        window.Element("obsAction").update(" ")
                        window.Element("obsValue").update(" ")
                        window.Element("obsResponse").update(" ")

                    if midiData: #  index >= 0:
                        # midiData = allInputs[index]
                        # print(f"obsDataValue {index}")
                        # print(json.dumps(midiData, indent=4, sort_keys=False))
    
                        if midiVal.status == "button":
                            if midiData["section"] == "scenes":                                    
                                response, buttonStatus = await obsCmd.doSceneChange(allInputs, midiData, buttonStatus)
                            elif midiData["section"] == "sourcesBtn" and midiData["type"] == "video":
                                response, buttonStatus = await obsCmd.playMediaSource(midiData, buttonStatus)
                            else:
                                response, buttonStatus = await obsCmd.doButtonAction(midiData, buttonStatus)
                                                                                        
                        if midiVal.status == "change":
                            response, buttonStatus = await obsCmd.doChangeAction(midiData, buttonStatus)
                            allInputs = guiCommon.updateAllInputByName(allInputs, midiData, midiData["name"]) #  allInputs[index] = midiData

                        window.Element("obsAction").update(midiData["title"])
                        window.Element("obsValue").update(str(midiData["value"]))
                        window.Element("obsResponse").update(response)
                        
                    lastName = midiData["name"] 
                    if exitFromMidi:
                        break
                
                if exitFromMidi:
                    break

                ## window operations
                event, values = window.read(timeout = 100)

                if event == sg.WIN_CLOSED: 
                    exitAction = "exit"
                    break
                
                if event == "Exit Program":
                    exitAction = "close"
                    break

                if event == "Setup":
                    exitAction = "setup"
                    break

        window.close()
        await obsSocket.disconnect()
        return exitAction, ""