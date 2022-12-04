

from faulthandler import disable
import sys
import mido
import time
import json
import os
import time
import re
import PySimpleGUI as sg
import asyncio

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
_guiTheme = "SandyBeach"
_guiMinSize = (720,480)

import midiObsJSONsetup as obsJSONsetup
import midiObsControls as obsControls
import midiObsWScmd as obsWScmd
import midiObsMidiSetup as obsMidiSetup

class ObsDisplay(object):
    
    def __init__(self, config, midiObsJSON, midiObsData, obsSocket):
        self.config = config
        self.midiObsJSON = midiObsJSON
        self.midiObsData = midiObsData
        self.scriptLogging = config["scriptLogging"]
        self.obsSocket = obsSocket

    def makeInputText(self, section, data, sg, type):

        # print(json.dumps(data, indent=4, sort_keys=False))

        i=1
        textList = []
        for s in data:


            if section == "controls":
                title = f'{i}. {s["display"]}'
                name = self.setKeyName("controls", s["name"]+type)
            elif section == "sources":
                if s["inputType"] == "video":
                    continue

                title = f'{i}. {s["inputName"]} ({s["inputType"]})'
                name = self.setKeyName("sources", s["inputName"]+type)
            elif section == "scenes":
                title = f'{i}. {s["sceneName"]}'
                name = self.setKeyName("scenes", s["sceneName"]+type)

            textList.append([sg.Text(title, size=(30)), sg.In(key=name, enable_events=True, size=(3))])            
            i+=1

        return textList

    def stringNumbersOnly(self, value):
        regex = re.compile('[^0-9]')
        value = regex.sub('', value)

        if not value:
            return ""
        if len(value) >= 2:
            return value[0:2]
        if int(value) < 0:
            return ""

        return value

    def setDefaultValue(self, midiConfigData, sname):

        # print(json.dumps(midiConfigData, indent=4, sort_keys=False))

        section, action, type = sname.split("_",2)
        id = -1
        for d in midiConfigData:
            # if d["deviceType"] -- "video":
            #     continue

            if d["section"] == section and d["action"] == action:
                if type == "c":
                    id = d["changeID"]
                elif type == "b":
                    id = d["buttonID"]
                break

        if id < 0:
            return ""

        return str(id)

    def setObsDataValue(self, midiVal, midiConfigData):

        # print(midiVal)

        # print("showMidiInputGUI  ID: {: >2}, status: {}, value: {: >3}"
        #         .format(midiVal.control, midiVal.status, midiVal.value))        

        midi = {}
        idx = 0
        for m in midiConfigData:
            if m["buttonID"] == midiVal.control and midiVal.status == "button":
                midi = m
                break
        
            if m["changeID"] == midiVal.control and midiVal.status == "change":
                midi = m
                break
            idx+=1

        if not midi:
            return midiConfigData, -1

        # if not "lastValue" in midi:
        #     midi["lastValue"] = -1

        # if not "lastValue" in midi:
        #     midi["lastValue"] = midi["value"]

        if midiVal.status == "button":  
            if not "buttonLastVal" in midi:
               midi["buttonLastVal"] = midi["buttonValue"]

            if midiVal.value == 0:     ## button released
                midi["buttonValue"] = 1 #int(not midi["buttonValue"])
            if midiVal.value == 127:   ## button pressed
                midi["buttonValue"] = 0
        elif midiVal.status == "change":  
            if not "changelastVal" in midi:
               midi["changeLastVal"] = midi["changeValue"]    
               midi["changeValue"] = midiVal.value

            # midi["value"] = midiVal.value
 
        # print(json.dumps(midi, indent=4, sort_keys=False))
        midiConfigData[idx] = midi
        return midiConfigData, idx

    def setKeyName(self, section, name):
        return section+"_"+name

    def getAllItemsNamesList(self, inputsAndScenes):

        nameList=[]
        for b in self.midiObsJSON["buttons"]:
            nameList.append(self.setKeyName("controls",b["name"]+"_b"))

        if "inputs" in inputsAndScenes["GetInputList"]:
            for i in inputsAndScenes["GetInputList"]["inputs"]:
                nameList.append(self.setKeyName("sources",i["inputName"]+"_b"))
                nameList.append(self.setKeyName("sources",i["inputName"]+"_c"))

        if "scenes" in inputsAndScenes["GetSceneList"]:
            for s in inputsAndScenes["GetSceneList"]["scenes"]:
                nameList.append(self.setKeyName("scenes",s["sceneName"]+"_b"))

        return nameList


    # I couldn't find anything useful to do with the video devices directly
    # switching between video feeds is done with scenes
    # def filterOutVideoDevices(self,midiConfiguration):

    #     cfg = []
    #     for m in midiConfiguration:
    #         if m["deviceType"] != "video":
    #             cfg.append(m)
            
    #     print(json.dumps(cfg, indent=4, sort_keys=False))

    #     return cfg

    def updateObsResponse(self, midiData, window, response, error):

        if error:
            jsonResponse = error
        else:
            jsonResponse = json.dumps(response, indent=4, sort_keys=False)

        window.Element("obsAction").update(midiData["action"])
        window.Element("obsResponse").update(disabled=False)
        window.Element("obsResponse").update(str(jsonResponse))
        window.Element("obsResponse").update(disabled=True)

        return window

    def showMidiSetupGUI(self, inputsAndScenes, midiDevices, midiObsData):

        updatedMidiObsData = midiObsData
        midiSetup = obsMidiSetup.MidiSettings(self.config)
        obsJsonFile = obsJSONsetup.JsonFileSettings(self.config["scriptLogging"])

        if "midiDevice" not in midiObsData:
            midiDevice = midiDevices[0]
            midiObsData["midiDevice"] = midiDevice
        else:
            midiDevice = self.midiObsData["midiDevice"]

        allNames = self.getAllItemsNamesList(inputsAndScenes)

        sg.theme(_guiTheme)

        fn = os.path.join(self.config["midiObsPath"], self.config["midiObsFile"])

        layout = [[sg.Text(f'SELECT MIDI INPUTS FOR: {midiDevice}')]]
        layout.append([sg.Text(f'Using JSON file: {fn}')])

        # if len(midiDevices) > 1:
        #     layout.append([
        #         sg.Text("Select Midi Input Device:", size=(35)),
        #         sg.Listbox(list(midiDevices), size=(30,1), enable_events=True, key='midiDevices')
        #         ])
                
        # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))
        # sys.exit()

        controls = self.makeInputText("controls", self.midiObsJSON["buttons"], sg, "_b")
        sourcesButton = self.makeInputText("sources", inputsAndScenes["GetInputList"]["inputs"], sg, "_b")
        sourcesRotary = self.makeInputText("sources", inputsAndScenes["GetInputList"]["inputs"], sg, "_c")
        scenes = self.makeInputText("scenes",inputsAndScenes["GetSceneList"]["scenes"], sg, "_b")

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
        window.set_min_size(_guiMinSize)

        for name in allNames:
            window[name].bind('<Enter>', ' +MOUSE OVER+')
            window[name].bind('<Leave>', ' +MOUSE AWAY+')
            window[name].bind("<FocusIn>", " +INPUT FOCUS+")
            window[name].update(value=self.setDefaultValue(midiObsData["midiConfiguration"],name))

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

                    print("Midi ID: {: >2}, status: {}, value: {: >3}, focus: {}"
                        .format(midiVal.control, midiVal.status, midiVal.value, focus))

                    midiConfig = midiSetup.setMidiObsValue(focus, midiVal, midiConfig)

                    # self.setMidiObsValue(focus, midiVal.control, midiVal.status)
                    window.Element(focus).update(value=self.stringNumbersOnly(str(midiVal.control)))

                    if exitFromMidi:
                        break
                
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
                    error, message = obsJsonFile.saveJSONfile(self.config["midiObsPath"], self.config["midiObsFile"], updatedMidiObsData)
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
                    # print(f"e: {event},v: {values}")
                    window.Element(event).update(value=self.stringNumbersOnly(values[event]))

                if window.FindElementWithFocus() != None:
                    focus = window.FindElementWithFocus().Key
                    if lastFocus != focus:
                        # print(f"==== Focus: {focus}")
                        lastFocus = focus

        window.close()
        return exitAction, updatedMidiObsData



    async def showMidiInputGUI(self, midiObsData):

        self.midiObsData = midiObsData
        midiDevice = midiObsData["midiDevice"]

        controls = obsControls.ObsControls(self.config, self.midiObsJSON)
        obsSocket = controls.websocketConnect()     # send the connection string
        # wsLoop = asyncio.get_event_loop()

        try:
            await obsSocket.connect()               # Make the connection to obs-websocket
            await obsSocket.wait_until_identified() # Wait for the identification handshake to complete
        except:
            return "error", "Cannot connect to OBS: {}".format(sys.exc_info()[1])

        try:
            with mido.open_input(midiDevice) as inMidi:
                ## clear anything already in the midi input buffer
                while inMidi.receive(block=False) is not None:
                    pass
        except:
            return "error", "No MIDI device attached"

        exitAction = "close"
        midiSetup = obsMidiSetup.MidiSettings(self.config)
        obsCmd = obsWScmd.ObsWScmd(self.config, obsSocket)

        sg.theme(_guiTheme)
        layout = [[sg.Text(f'USING MIDI INPUT: {midiDevice}')]]

        layout.append([sg.Text("Midi input:", size=(15)), sg.In(key="midiIn", readonly=True, enable_events=False, size=(3))])        
        layout.append([sg.Text("Midi value:", size=(15)), sg.In(key="midiVal", readonly=True, enable_events=False, size=(3))])
        layout.append([sg.Text("Midi type:", size=(15)), sg.In(key="midiType", readonly=True, enable_events=False, size=(20))])
        layout.append([sg.Text(" ")])
        layout.append([sg.Text("OBS action:", size=(15)), sg.In(key="obsAction", readonly=True, enable_events=False, size=(20))])
        layout.append([sg.Text("OBS value:", size=(15)), sg.In(key="obsValue", readonly=True,  enable_events=False, size=(20))])

        layout.append([sg.vtop([sg.Text("OBS response:", size=(15)), 
                       sg.Multiline(key="obsResponse", disabled=True, enable_events=False, font=("Courier New", 10), size=(60,10))])])

        layout.append([sg.Button('Setup'), sg.Button('Exit Program')]) #, sg.Button('Close')

        window = sg.Window('MIDI-OBS', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(_guiMinSize)

        midiConfig = midiObsData["midiConfiguration"]
        midiConfig = await obsCmd.getCurrentValues(midiConfig)
        exitFromMidi = False
        lastIndex = -1
        response = None

        with mido.open_input(midiDevice) as inMidi:
            ## clear anything already in the midi input buffer
            while inMidi.receive(block=False) is not None:
                pass

            while True:
                time.sleep(0.05)

                ## read the midi device
                for msg in inMidi.iter_pending():
                    midiVal = midiSetup.midiToObj(msg)

                    print("showMidiInputGUI  ID: {: >2}, status: {}, value: {: >3}"
                        .format(midiVal.control, midiVal.status, midiVal.value))

                    window.Element("midiIn").update(value=self.stringNumbersOnly(str(midiVal.control)))
                    window.Element("midiVal").update(str(midiVal.value))
                    window.Element("midiType").update(midiVal.status)

                    midiConfig, index = self.setObsDataValue(midiVal, midiConfig)
                    if lastIndex != index:                        
                        window.Element("obsAction").update(" ")
                        window.Element("obsResponse").update(" ")

                    if index >= 0:
                        midiData = midiConfig[index]
                        # print(f"obsDataValue {index}")
                        # print(json.dumps(midiData, indent=4, sort_keys=False))
    
                        if midiVal.status == "button":
                            if midiData["buttonLastVal"] != midiData["buttonValue"]:
                                response = await obsCmd.doButtonAction(midiData, midiVal)
                                midiData["buttonLastValue"] = midiData["buttonValue"]
                                midiConfig[index] = midiData

                        if midiVal.status == "change":
                            if midiData["changeLastVal"] != midiData["changeValue"]:
                                response = await obsCmd.doChangeAction(midiData, midiVal)
                                midiData["changeLastVal"] = midiData["changeValue"]
                                midiConfig[index] = midiData

                        window.Element("obsAction").update(midiData["action"])
                        window.Element("obsResponse").update(response)
                        
                    lastIndex = index
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
        return exitAction, False

    def showHostSetupGUI(self, midiObJSONConfigFile):
        fileSettings = obsJSONsetup.JsonFileSettings(self.scriptLogging)

        filename = os.path.join(self.config["midiObsPath"],midiObJSONConfigFile)
        error, obsConfig = fileSettings.loadJsonFile(filename)
        if error:
            exitAction = "error"
            return exitAction, obsConfig

        config = obsConfig["config"]
        updated = False

        # print("--- midiObsJson ---")
        # print(json.dumps(midiObsJSON, indent=4, sort_keys=False))
        # print("---config 1 ---")
        # print(json.dumps(config, indent=4, sort_keys=False))

        sg.theme(_guiTheme)
        layout = [[sg.Text(f'OBS WEBSOCKET HOST SETTINGS')]]
        layout.append([sg.Text("Server IP:", size=(20)), sg.In(key="wsAddress", enable_events=True, size=(30))])        
        layout.append([sg.Text("Server Port:", size=(20)), sg.In(key="wsPort", enable_events=True, size=(30))])        
        layout.append([sg.Text("Server Password:", size=(20)), sg.In(key="wsPassword", enable_events=True, size=(30))])        

        layout.append([sg.Button('Save and Close'), sg.Button('Close')]) #, sg.Button('Exit Program')])

        window = sg.Window('MIDI-OBS - Server Settings ', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(_guiMinSize)

        window.Element("wsAddress").update(value=config["wsAddress"])
        window.Element("wsPort").update(value=config["wsPort"])
        window.Element("wsPassword").update(value=config["wsPassword"])

        while True:
            event, values = window.read(timeout = 100)
            
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
                break
    
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
            obsConfig["config"]["midiObsFile"] = self.config["midiObsFile"]

            error, message = fileSettings.saveJSONfile(self.config["midiObsPath"], midiObJSONConfigFile, obsConfig)
            if error:
                exitAction = "error"
                config = message

        config["midiObsPath"] = self.config["midiObsPath"]
        config["midiObsFile"] = self.config["midiObsFile"]
        return exitAction, config

    def showErrorGUI(self, error):

        sg.theme(_guiTheme)

        print(f"AN ERROR: {error}")

        errorMsg = []
        errorMsg.append("Ensure that OBS is runnning and that your Midi Device is plugged in before you start this program.")
        errorMsg.append("The installled version of OBS needs to be version 28 or greater and OBS-Websocket should be version 5 or higher.")
        
        layout = [[sg.Text('AN ERROR HAS OCCURED', font=("Helvetica", 12, "italic"))]]
        for e in errorMsg:
            layout.append([sg.Text(e)])
            
        layout.append([sg.Text(" ")])
        if error:
            layout.append([sg.Text("Reported Error:", font=("Helvetica", 12, "italic"))])
            layout.append([sg.Text(error)])

        layout.append([sg.Button('Close')])

        window = sg.Window('MIDI-OBS ', layout, return_keyboard_events=True, resizable=True, finalize=True)
        window.set_min_size(_guiMinSize)

        while True:
            event, values = window.read(timeout = 100)
            
            if event == sg.WIN_CLOSED or event == 'Close':
                break

        window.close()
        return
