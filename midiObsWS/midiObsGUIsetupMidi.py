import FreeSimpleGUI as sg
import sys
import mido
import time
import datetime 
import os
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

from midiObsWS.midiObsMidiSettings import ObsMidiSettings
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

    def readMidiValues(self, values):
     
        mIDlist = []
        duplicates = []
        duplicatesText = ""
        duplicatesError = False

        newMidiIDs = []
        for key, value in values.items():                        
            if value == "" or not value:
                midiID = -1
            else:
                midiID = int(value)                        
            newMidiIDs.append({"name": key, "midiID": midiID})
                            
            if midiID in mIDlist and midiID > 0:
                duplicates.append(midiID)                            
            mIDlist.append(midiID)
                            
        duplicates = sorted(list(set(duplicates)))  ## make list distinct  
        if len(duplicates) > 0:
            dups = ", ".join(str(d) for d in duplicates) 
            s = "s" if len(duplicates) > 1 else ""
            duplicatesText = f"Duplicate Midi Value{s} found [{dups}], please check."
            duplicatesError = True
                
        return newMidiIDs, duplicatesText, duplicatesError
        
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
        
        duplicates = {"Text": "", "Error": False, "Time" : datetime.datetime.now()}
        
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
        layout.append([sg.Text(duplicates["Text"], size=(100), key="duplicatesTextInfo", font=("Arial", 10, "bold"))])

        window = sg.Window('MIDI-OBS - Setup', layout, return_keyboard_events=True, 
                           resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)
        window.force_focus()

        for name in allNames:
            # print(name)
            window[name['name']].bind('<Enter>', ' +MOUSE OVER+')
            window[name['name']].bind('<Leave>', ' +MOUSE AWAY+')
            window[name['name']].bind("<FocusIn>", " +INPUT FOCUS+")
            window[name['name']].update(value=guiCommon.setDefaultValue(name['midiID']))

        try:
            window[allNames[0]['name']].Widget.focus()
            print(f"Focus set to: {allNames[0]['name']}")
        except Exception as e:
            print(f"Error setting focus: {e}")

        exitAction = ""
        focus = None
        exitFromMidi = False

        with mido.open_input(config["midiIn"], backend='mido.backends.rtmidi') as inMidi:
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
                    window.Element("duplicatesTextInfo").update(value=str(""))
                    newMidiIDs, duplicates["Text"], duplicates["Error"] = self.readMidiValues(values)
                        
                    if duplicates["Error"]:
                        duplicates["Time"] = datetime.datetime.now() + datetime.timedelta(seconds=30)
                        window.Element("duplicatesTextInfo").update(value=str(duplicates["Text"]))
                        continue
                          
                    allNames = self.updateAllNamesMidiID(allNames, newMidiIDs)
                    db.updateTablesWithMidiValues(allNames)
                    db.setAllConfigured(1)
                    break
        
                if duplicates["Error"] and datetime.datetime.now() > duplicates["Time"]:
                    duplicates["Error"] = False
                    duplicates["Text"] = ""
                    window.Element("duplicatesTextInfo").update(value=str(duplicates["Text"]))
        
                keyValues = values.keys()
                if event in keyValues:
                    window.Element(event).update(value=guiCommon.stringNumbersOnly(values[event]))                

                if window.FindElementWithFocus() != None:
                    focus = window.FindElementWithFocus().Key

        window.close()
        return exitAction, ""