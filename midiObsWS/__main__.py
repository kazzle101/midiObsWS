#!/usr/bin/env python

import sys
import signal
import argparse
import os
import asyncio
import json

# https://github.com/obsproject/obs-websocket - this is now included in OBS, v28.0.0 onwards
# https://github.com/IRLToolkit/simpleobsws/tree/master
#
# using python >= 3.9
#
# python -m pip install mido python-rtmidi websocket-client argparse simpleobsws sqlite3

if getattr(sys, 'frozen', False):
    _scriptDir = os.path.dirname(sys.executable)
else:
    _scriptDir = os.path.dirname(os.path.realpath(__file__))

_scriptLogging = os.path.join(_scriptDir, "midiObsDebug.log")

from midiObsWS.midiObsStartup import ObsStartup
from midiObsWS.midiObsDatabase import ObsDatabase
from midiObsWS.midiObsDisplay import ObsDisplay
from midiObsWS.midiObsMidiSettings import ObsMidiSettings

def exitNicely(signum, frame):
    print("")
    print("exiting....")    
    sys.exit(0)       

def main():
    signal.signal(signal.SIGINT, exitNicely)

    obsStartup = ObsStartup(_scriptDir, _scriptLogging)
    obsStartup.checkCanWriteToScriptDir()
    obsStartup.checkForDatabase()
    midiDevices = obsStartup.checkForMidiInputDevice()
    
    db = ObsDatabase(_scriptDir)
    config = db.getConfig()
                
    parser = argparse.ArgumentParser(description="""MIDI - OBS Controller""")     
    parser.add_argument("-k", "--inputkinds", action='store_true', 
                        help="list inputs attached to OBS, the host must be configured and OBS running")
    parser.add_argument("-m", "--mididevices", action='store_true',
                        help="list of attached midi in and out devices") 
    
    args = parser.parse_args()
    if args.inputkinds:
        
        if config["wsHostSet"] == 0:
            print("OBS Host not configured")
            sys.exit(0)
        
        data = obsStartup.getListofInputKinds(config)
        print(json.dumps(data, indent=4, sort_keys=False))
        sys.exit(0)
        
    if args.mididevices:
        midiSettings = ObsMidiSettings(None)
        err, midiIn = midiSettings.listMidiDevices()
        if err:
            print("No Midi IN device found")
        else:
            print("Midi IN:")
            print(json.dumps(midiIn, indent=4, sort_keys=False))
        
        err, midiOut = midiSettings.listMidiOutputDevices()
        if err:
            print("No Midi OUT device found")
        else:
            print("Midi OUT:")
            print(json.dumps(midiOut, indent=4, sort_keys=False))

        sys.exit(0)

    config["midiSet"] = obsStartup.hasMidiInDeviceChanged(config, midiDevices)
            
    exitAction = ""
    if config["configured"] == 0:
        exitAction = "setup"
    if config["wsHostSet"] == 0 or config["midiSet"] == 0:
        exitAction = "host"

    display = ObsDisplay()

    while True:
        
        if exitAction == "close" or exitAction == "exit":
            break
        
        elif exitAction == "host":
            while True:
                midiSettings = ObsMidiSettings(None)
                err, midiIn = midiSettings.listMidiDevices()
                err, midiOut = midiSettings.listMidiOutputDevices()
                midiInOut = {"midiIn": midiIn, "midiOut": midiOut}
                exitAction, config = display.showHostSetupGUI(config, midiInOut)
                if exitAction == "error":
                    display.showErrorGUI(f"{message}")
                    sys.exit(0)
                elif exitAction == "exit":
                    break
                elif config["wsHostSet"] == 1 and config["midiSet"] == 1:
                    db.setConfig(config)
                    exitAction = "setup"
                    break
                else:
                    if config["wsHostSet"] == 0:
                        print("The OBS Websocket connection has not been set")
                    if config["midiSet"] == 0:
                        print("The MIDI In Device needs setting") 
        
        elif exitAction == "setup":
            obsStartup.getInputsAndScenes(config)
            exitAction, message = display.showMidiSetupGUI(config, _scriptDir)
            if exitAction == "error":
                display.showErrorGUI(f"{message}")
                sys.exit(0)
            elif exitAction == "exit":
                break
            else:
                config = db.getConfig()
            
        else:
            exitAction, message = display.showMidiObsGUI(config, _scriptDir)
            if exitAction == "error":
                display.showErrorGUI(f"{message}")
                sys.exit(0)
                
    return


if __name__ == "__main__":
    main()