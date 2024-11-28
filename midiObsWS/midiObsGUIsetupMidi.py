import FreeSimpleGUI as sg
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
# from midiObsWS.midiObsFiles import ObsFiles
from midiObsWS.midiObsGUIcommon import ObsGUIcommon
from midiObsWS.midiObsDatabase import ObsDatabase

class ObsGUIsetupMidi(object):

    def __init__(self, guiTheme, guiMinSize, scriptDir):
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        self.scriptDir = scriptDir
        return

    def updateAllNamesMidiID(self, allNames, newValues):
        
        for a in allNames:
            for n in newValues:
                if n["name"] == a["name"] and a["midiID"] != n["midiID"]:
                    a["midiID"] = n["midiID"]
                    a["changed"] = True
                    break
        
        return allNames

    def showMidiSetupGUI(self, config):
        db = ObsDatabase(self.scriptDir)
        guiCommon = ObsGUIcommon(config)
        midiSetup = ObsMidiSettings(config)

        wsControls = db.getControlsList()
        userInputs = db.getInputsList()
        userScenes = db.getScenesList()

        sg.theme(self.guiTheme)

        layout = [[sg.Text(f"SELECT MIDI INPUTS FOR: {config['midiIn']}")]]

        allNames = []
        controls, names = guiCommon.makeSectionControls(sg, wsControls)
        allNames = guiCommon.setAllnames(allNames, names)
        scenes, names = guiCommon.makeSectionScenes(sg, userScenes)
        allNames = guiCommon.setAllnames(allNames, names)
        sourcesBtn, names = guiCommon.makeSectionSourcesBtn(sg, userInputs)
        allNames = guiCommon.setAllnames(allNames, names)
        sourcesRot, names = guiCommon.makeSectionSourcesRot(sg, userInputs)
        allNames = guiCommon.setAllnames(allNames, names)

        # print(json.dumps(sourcesBtn, indent=4, sort_keys=False))

        column1 = sg.Column([
            [sg.Frame("1. Controls (buttons)", controls, vertical_alignment='top', element_justification='c', border_width=2)],
        ], element_justification='c', vertical_alignment='top')

        column2 = sg.Column([
            [sg.Frame("2. Scenes (button to switch to scene)", scenes, vertical_alignment='top', element_justification='c', border_width=2)]
        ], element_justification='c', vertical_alignment='top')

        column3 = sg.Column([
            [sg.Frame("3. Sources (button to toggle)", sourcesBtn, vertical_alignment='top', element_justification='c', border_width=2)],
            [sg.Frame("4. Sources (rotary/slider for volume or fades)", sourcesRot, vertical_alignment='top', element_justification='c', border_width=2)]
        ], element_justification='c', vertical_alignment='top')

        layout.append([column1, column2, column3])
        layout.append([sg.Button('Save and Close'), sg.Button('Close'), sg.Button("Server Settings")])

        window = sg.Window('MIDI-OBS - Setup', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)

        for name in allNames:
            # print(name)
            window[name['name']].bind('<Enter>', ' +MOUSE OVER+')
            window[name['name']].bind('<Leave>', ' +MOUSE AWAY+')
            window[name['name']].bind("<FocusIn>", " +INPUT FOCUS+")
            window[name['name']].update(value=guiCommon.setDefaultValue(name['midiID']))

        exitAction = ""
        focus = None
        exitFromMidi = False

        with mido.open_input(config["midiIn"]) as inMidi:
            ## clear anything already in the midi input buffer
            while inMidi.receive(block=False) is not None:
                pass

            while True:
                time.sleep(0.05)

                ## read the midi device
                for msg in inMidi.iter_pending():
                    midiVal = midiSetup.midiToObj(msg)
                    window.Element(focus).update(value=guiCommon.stringNumbersOnly(str(midiVal.control)))

                if exitFromMidi:
                    break

                ## window operations
                event, values = window.read(timeout = 100)

                if event == sg.WIN_CLOSED: # if user closes window
                    exitAction = "exit"
                    break

                if event == 'Close':
                    exitAction = ""
                    break

                if event == "Server Settings":
                    exitAction = "host"
                    break

                if event == "Save and Close":
                    newMidiIDs = []
                    for key, value in values.items():                        
                        if value == "" or not value:
                            midiID = -1
                        else:
                            midiID = int(value)                        
                        newMidiIDs.append({"name": key, "midiID": midiID})
                        
                    allNames = self.updateAllNamesMidiID(allNames, newMidiIDs)
                    db.updateTablesWithMidiValues(allNames)
                    db.setAllConfigured(1)
                    break
                
                keyValues = values.keys()
                if event in keyValues:
                    window.Element(event).update(value=guiCommon.stringNumbersOnly(values[event]))                

                if window.FindElementWithFocus() != None:
                    focus = window.FindElementWithFocus().Key

        window.close()
        return exitAction, ""