import PySimpleGUI as sg
import sys
import mido
import time
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsWScmd import ObsWScmd
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsGUIcommon import ObsGUIcommon

class ObsGUIshowMidiObs(object):
    
    def __init__(self, guiTheme, guiMinSize, config, midiObsConfig):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        self.config = config
        self.midiObsConfig = midiObsConfig
        # self.scriptDir = config["scriptDir"]
        return

    async def showMidiObsGUI(self, midiObsData):
        guiCommon = ObsGUIcommon(self.config, self.midiObsConfig, midiObsData)

        midiDevice = midiObsData["midiDevice"]
        buttonStatus = []
        midiDeviceInfo = guiCommon.getMidiDeviceInfo(midiObsData)

        controls = ObsControls(self.config, midiObsData, self.midiObsConfig)
        obsSocket = controls.websocketConnect()     # send the connection string

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
        midiSetup = ObsMidiSettings(self.config)
        scenesSectionData = guiCommon.getSectionData(midiObsData,"scenes")
        obsCmd = ObsWScmd(self.config, obsSocket, midiDeviceInfo, scenesSectionData)

        # midiDeviceInfo = guiCommon.getMidiDeviceInfo(self.midiObsData)
        obsData = midiObsData["midiConfiguration"]
        buttonStatus, obsData = await obsCmd.getCurrentValues(obsData, midiDeviceInfo)
        exitFromMidi = False
        lastIndex = -1
        response = None

        sg.theme(self.guiTheme)
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
        window.set_min_size(self.guiMinSize)

        with mido.open_input(midiDevice) as inMidi:
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

                    obsData, index = guiCommon.setObsDataValue(midiVal, obsData)
                    if lastIndex != index:                        
                        window.Element("obsAction").update(" ")
                        window.Element("obsResponse").update(" ")

                    if index >= 0:
                        midiData = obsData[index]
                        # print(f"obsDataValue {index}")
                        # print(json.dumps(midiData, indent=4, sort_keys=False))
    
                        if midiVal.status == "button":
                            if midiData["section"] == "scenes":                                    
                                response, buttonStatus = await obsCmd.doSceneChange(obsData, midiData, buttonStatus)
                            else:
                                response, buttonStatus = await obsCmd.doButtonAction(midiData, midiVal, buttonStatus)
                                    
                            obsData[index] = midiData
                                                    
                        if midiVal.status == "change":
                            if midiData["changeLastVal"] != midiData["changeValue"]:
                                response, buttonStatus = await obsCmd.doChangeAction(midiData, midiVal, buttonStatus)
                                midiData["changeLastVal"] = midiData["changeValue"]
                                obsData[index] = midiData

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