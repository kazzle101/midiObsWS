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
# python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui

if getattr(sys, 'frozen', False):
    _scriptDir = os.path.dirname(sys.executable)
else:
    _scriptDir = os.path.dirname(os.path.realpath(__file__))

_scriptLogging = os.path.join(_scriptDir, "midiObsDebug.log")
_midiObsConfigFile = "midiObsConfig.json"
# _midiObsData = {}

from midiObsWS.midiObsStartup import ObsStartup
from midiObsWS.midiObsJSONsetup import ObsJSONsetup
from midiObsWS.midiObsControls import ObsControls
from midiObsWS.midiObsDisplay import ObsDisplay

def exitNicely(signum, frame):
    print("")
    print("exiting....")    
    sys.exit(0)       

def main():
    # global _midiObsData

    loop = asyncio.get_event_loop()
    config = {}
    config["scriptDir"] = _scriptDir
    config["scriptLogging"] = _scriptLogging    
    exitAction = ""

    # fileSettings = obsJSONsetup.JsonFileSettings(_scriptLogging)

    signal.signal(signal.SIGINT, exitNicely)

    desc = """MIDI - OBS Controller"""

    parser = argparse.ArgumentParser(description=desc)     
    parser.add_argument("-s", "--sethost", action='store_true', help="set the obs-websocket hostname and password")  
    parser.add_argument("-k", "--inputkinds", action='store_true', help="list inputs attached to OBS")
    parser.add_argument("--getsetlist", action='store_true', help="list get set and other options")

    args = parser.parse_args()
    obsStartup = ObsStartup(_scriptLogging)
    obsJSONsetup = ObsJSONsetup(_scriptLogging)

    obsStartup.checkCanWriteToScriptDir(_midiObsConfigFile, config)

    midiObsConfig = obsStartup.loadObsConfigJsonFile(_midiObsConfigFile, config)
     
    config = midiObsConfig.pop("config")
    config["scriptDir"] = _scriptDir
    config["scriptLogging"] = _scriptLogging
    config["midiObsConfigFile"] = _midiObsConfigFile

    midiObsData = obsStartup.loadObsDataJsonFile(config["midiObsDataFile"], config)
   
    if args.sethost:
        exitAction, midiObsData, config = obsStartup.setupHost(config, midiObsData)

    if not "hostSet" in config or config["hostSet"] == 0:
        exitAction, midiObsData, config = obsStartup.setupHost(config, midiObsData)

    controls = ObsControls(config, midiObsData, midiObsConfig)

    if args.getsetlist:
        controls.makeGetSetList()
        return

    if args.inputkinds:
        controls.getInputKinds()
        return
    
    midiObsData, midiDevices = obsStartup.checkForMidiInputDevice(config, midiObsData)

    # print(json.dumps(config, indent=4, sort_keys=False))
    # print("cc _main_")
  
    inputsAndScenes, midiObsData, config = obsStartup.setInputsAndScenes(config, midiObsData, midiObsConfig)
    obsStartup.checkMidiObsData(config, midiObsData)

    # obsSocket = controls.websocketConnect()
    # print(json.dumps(midiObsData["midiConfiguration"], indent=4, sort_keys=False))
    # print(json.dumps(midiObsData, indent=4, sort_keys=False))

    midiObsData["midiConfiguration"] = obsJSONsetup.filterOutVideoDevices(midiObsData["midiConfiguration"])
    midiObsConfig["inputKinds"]["video"] = []
    inputsAndScenes["GetInputList"]["inputs"] = obsJSONsetup.filterOutVideoDevices(inputsAndScenes["GetInputList"]["inputs"])

    # print(json.dumps(_midiObsData, indent=4, sort_keys=False))
    # sys.exit()

    display = ObsDisplay(config, midiObsConfig)

    # print(json.dumps(config, indent=4, sort_keys=False))
    # sys.exit()

    # exitAction = ""
    if midiObsData["midiConfigured"] == 0:
        exitAction = "setup"

    while True:
        if exitAction == "close" or exitAction == "exit":
            break

        elif exitAction == "setup":
            exitAction, midiObsData = display.showMidiSetupGUI(inputsAndScenes, midiDevices, midiObsData)
            if not midiObsData:
                display.showErrorGUI(f"unhelpful error message (midiObsData empty?)")
                sys.exit(0) 
            if exitAction == "error":
                display.showErrorGUI(f"{midiObsData}")
                sys.exit(0)

        elif exitAction == "host":
            exitAction, config, midiObsData = display.showHostSetupGUI(_midiObsConfigFile, config["midiObsDataFile"], config)
            if exitAction == "error":
                display.showErrorGUI(f"{config}")
                sys.exit(0)

        else:            
            #exitAction, error = loop.run_until_complete(display.showMidiInputGUI(_midiObsData))
            exitAction, error = display.showMidiObsGUI(midiObsData)
            if error:
                display.showErrorGUI(f"{error}")
                sys.exit(0)

    return


if __name__ == "__main__":
    main()