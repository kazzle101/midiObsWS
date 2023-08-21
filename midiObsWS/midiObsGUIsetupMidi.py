import PySimpleGUI as sg
import sys
import mido
import time
import os
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
# from midiObsWS.midiObsControls import ObsControls
# from midiObsWS.midiObsWScmd import ObsWScmd
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsFiles import ObsFiles
from midiObsWS.midiObsGUIcommon import ObsGUIcommon

class ObsGUIsetupMidi(object):
    
    def __init__(self, guiTheme, guiMinSize, config, midiObsConfig):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        self.config = config
        self.midiObsConfig = midiObsConfig
        self.scriptDir = config["scriptDir"]
        return
    
    def showMidiSetupGUI(self, inputsAndScenes, midiDevices, midiObsData):
        guiCommon = ObsGUIcommon(self.config, self.midiObsConfig, midiObsData)
        midiSetup = ObsMidiSettings(self.config)
        obsFiles = ObsFiles()

        updatedMidiObsData = midiObsData
        # midiSetup = obsMidiSetup.MidiSettings(self.config)
        # obsJsonFile = obsJSONsetup.JsonFileSettings(self.config["scriptLogging"])

        if "midiDevice" not in midiObsData:
            midiDevice = midiDevices[0]
            midiObsData["midiDevice"] = midiDevice
        else:
            midiDevice = midiObsData["midiDevice"]

        allNames = guiCommon.getAllItemsNamesList(inputsAndScenes)

        sg.theme(self.guiTheme)

        fn = os.path.join(self.scriptDir, self.config["midiObsDataFile"])

        layout = [[sg.Text(f'SELECT MIDI INPUTS FOR: {midiDevice}')]]
        layout.append([sg.Text(f'Using JSON file: {fn}')])

        # if len(midiDevices) > 1:
        #     layout.append([
        #         sg.Text("Select Midi Input Device:", size=(35)),
        #         sg.Listbox(list(midiDevices), size=(30,1), enable_events=True, key='midiDevices')
        #         ])
                
        # print(json.dumps(midiObsData["midiConfiguration"], indent=4, sort_keys=False))
        # sys.exit()

        controls = guiCommon.makeInputText("controls", self.midiObsConfig["buttons"], sg, "_b")
        sourcesButton = guiCommon.makeInputText("sources", inputsAndScenes["GetInputList"]["inputs"], sg, "_b")
        sourcesRotary = guiCommon.makeInputText("sources", inputsAndScenes["GetInputList"]["inputs"], sg, "_c")
        scenes = guiCommon.makeInputText("scenes",inputsAndScenes["GetSceneList"]["scenes"], sg, "_b")

        column1 = sg.Column([
            [sg.Frame("1. Controls (buttons)", controls, vertical_alignment='top', element_justification='c', border_width=2)],
        ], element_justification='c', vertical_alignment='top')

        column2 = sg.Column([
            [sg.Frame("2. Scenes (button to switch to scene)", scenes, vertical_alignment='top', element_justification='c', border_width=2)]
        ], element_justification='c', vertical_alignment='top')

        column3 = sg.Column([
            [sg.Frame("3. Sources (button to toggle)", sourcesButton, vertical_alignment='top', element_justification='c', border_width=2)],
            [sg.Frame("4. Sources (rotary/slider for volume or fades)", sourcesRotary, vertical_alignment='top', element_justification='c', border_width=2)]
        ], element_justification='c', vertical_alignment='top')

        layout.append([column1, column2, column3])
        layout.append([sg.Button('Save and Close'), sg.Button('Close'), sg.Button("Server Settings")])

        window = sg.Window('MIDI-OBS - Setup', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)

        for name in allNames:
            window[name].bind('<Enter>', ' +MOUSE OVER+')
            window[name].bind('<Leave>', ' +MOUSE AWAY+')
            window[name].bind("<FocusIn>", " +INPUT FOCUS+")
            window[name].update(value=guiCommon.setDefaultValue(midiObsData["midiConfiguration"],name))

        lastFocus = ""
        exitAction = ""
        focus = None
        exitFromMidi = False
        midiConfig = midiObsData["midiConfiguration"]

        with mido.open_input(midiDevice) as inMidi:
            ## clear anything already in the midi input buffer
            while inMidi.receive(block=False) is not None:
                pass

            while True:
                time.sleep(0.05)

                ## read the midi device
                for msg in inMidi.iter_pending():
                    midiVal = midiSetup.midiToObj(msg)

                    # print("Midi ID: {: >2}, status: {}, value: {: >3}, focus: {}"
                    #     .format(midiVal.control, midiVal.status, midiVal.value, focus))

                    midiConfig = midiSetup.setMidiObsValue(focus, midiVal, midiConfig)

                    # self.setMidiObsValue(focus, midiVal.control, midiVal.status)
                    window.Element(focus).update(value=guiCommon.stringNumbersOnly(str(midiVal.control)))

                
                if exitFromMidi:
                    break

                ## window operations
                event, values = window.read(timeout = 100)

                if event == sg.WIN_CLOSED: # if user closes window or clicks cancel
                    exitAction = "exit"
                    break

                if event == 'Close':
                    exitAction = ""
                    break
                    
                if event == "Save and Close":
                    exitAction = ""
                    updatedMidiObsData["midiConfigured"] = 1
                    updatedMidiObsData["midiDevice"] = midiDevice
                    updatedMidiObsData["midiConfiguration"] = midiConfig
                    # print(json.dumps(updatedMidiObsData, indent=4, sort_keys=False))
                    error, message = obsFiles.saveJSONfile(self.scriptDir, self.config["midiObsDataFile"], updatedMidiObsData)
                    if error:
                        exitAction = "error"
                        updatedMidiObsData = message
                    break                    

                if event == "Server Settings":
                    exitAction = "host"
                    break          

                # if event == "midiDevices":
                #     continue

                keyValues = values.keys()
                if event in keyValues:
                    # print(f"event in keyValues:::: e: {event},v: {values}")
                    window.Element(event).update(value=guiCommon.stringNumbersOnly(values[event]))
                    midiConfig = midiSetup.setMidiKeyValue(event, values, midiConfig)

                if window.FindElementWithFocus() != None:
                    focus = window.FindElementWithFocus().Key
                    if lastFocus != focus:
                        # print(f"==== Focus: {focus}")
                        lastFocus = focus

        window.close()
        return exitAction, updatedMidiObsData