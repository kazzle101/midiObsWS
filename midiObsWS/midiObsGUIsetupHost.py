import FreeSimpleGUI as sg
import sys
import mido
import time

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
from midiObsWS.midiObsWScmd import ObsWScmd
from midiObsWS.midiObsMidiSettings import ObsMidiSettings

class ObsGUIsetupHost(object):
    
    def __init__(self, guiTheme, guiMinSize):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        return

    async def showHostSetupGUI(self, config):
        obsMidi = ObsMidiSettings(config)
        obsCmd = ObsWScmd(config, None, None)
        
        newConfig = config    
        err, midiInputs = obsMidi.listMidiDevices()
        err, midiOutputs = obsMidi.listMidiOutputDevices()

        midiOutputs.insert(0, "not set")

        hostSetInfo = []
        hostSetInfo.append("INFO: The OBS Websocket Host needs validating, enter details and click test")
        hostSetInfo.append("")

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
        midiLayout.append([sg.Text('This Midi Channel is used with Midi Out, for general devices this is normally 10')]) 

        layout.append([
          [sg.Frame('Midi Device Settings', midiLayout, font='Any 12', title_color='blue', size=frameSize)],
        ])

        layout.append([sg.Button('Save and Close'), sg.Button('Close')]) #, sg.Button('Exit Program')])
        
        layout.append([sg.Text(hostSetInfo[newConfig["wsHostSet"]], size=(80), key="wsHostSetInfo")])

        window = sg.Window('MIDI-OBS - Settings ', layout, return_keyboard_events=True, 
                           resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)
        window.force_focus()

        window.Element("wsAddress").update(value=config["wsAddress"])
        window.Element("wsPort").update(value=config["wsPort"])
        window.Element("wsPassword").update(value=config["wsPassword"])

        if config["midiIn"] == "":
            window.find_element("midiIn").update(value=midiInputs[0])
        else:      
            window.find_element("midiIn").update(value=config["midiIn"])

        if config["midiOut"] == "":
            window.find_element("midiOut").update(value=midiOutputs[0])
        else:
            window.find_element("midiOut").update(value=config["midiOut"])

        window.Element("midiChannel").update(disabled=False)
        window.Element("midiChannel").update(value=config["midiChannel"])
        window.Element("midiChannel").update(disabled=True)

        while True:
            event, values = window.read(timeout = 100)

            if event == "Test OBS Connection":
                window.Element("obsTestInfo").update("")
                wsAddress = values["wsAddress"].strip()
                wsPort = values["wsPort"].strip()
                wsPassword = values["wsPassword"].strip()
                error, response = await obsCmd.obsTest(wsAddress, wsPort, wsPassword)
                if error:
                    newConfig["wsHostSet"] = 0
                else:
                    newConfig["wsHostSet"] = 1
                    
                window.Element("wsHostSetInfo").update(value=str(hostSetInfo[newConfig["wsHostSet"]]))                                    
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
                exitAction = "close"
                break

            if event == "Save and Close":
                exitAction = "setup"
                newConfig["wsAddress"] = values["wsAddress"].strip()
                newConfig["wsPort"] = values["wsPort"].strip()
                newConfig["wsPassword"] = values["wsPassword"].strip()

                newConfig["midiSet"] = 1
                newConfig["midiIn"] = values["midiIn"]
                if values["midiOut"] == "not set":
                    newConfig["midiOut"] = ""
                else:
                    newConfig["midiOut"] = values["midiOut"]

                newConfig["midiChannel"] = int(values["midiChannel"])
                break
    
        window.close()
        
        return exitAction, newConfig 
