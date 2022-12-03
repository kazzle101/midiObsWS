#!/usr/bin/env python

import sys
import signal
import mido
import argparse
import time
import json
import os
import re
import ntpath
import asyncio

# https://github.com/obsproject/obs-websocket - this is now included in OBS, v28.0.0 onwards
# https://github.com/IRLToolkit/simpleobsws/tree/master
#
# using python 3.9
#
# python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui

"""
apple mac:
    if you see an error:
        ModuleNotFoundError: No Module named '_tkinter'
    then try:
        $ sudo port install py-tkinter
            or
        $ sudo brew install python-tk 
"""

"""
linux (debian bullseye) 
    the included version of OBS is too old (version 26.1.2) to support ObsWebsocket

    you can update using the unstable release, which may break your installation of Debian
    in /etc/apt/sources.list add:
        deb http://deb.debian.org/debian unstable  main contrib non-free
        deb-src http://deb.debian.org/debian unstable main contrib non-free

    then:
        sudo apt update
        sudo apt remove obs-studio
        sudo apt install obs-studio
        sudo shutdown -r now

    log back in and install:
        sudo apt install ./obs-websocket-5.0.0-beta1-Ubuntu64.deb
        sudo apt install libjack-jackd2-dev libasound2-dev python3-tk

    this will update to version 27.2.4

"""

_scriptDir = os.path.dirname(os.path.realpath(__file__))
_scriptLogging = os.path.join(_scriptDir, "midiObsDebug.log")
_midiObsJSONfilename = "midiObsConfig.json"
_midiObsData = {}

import midiObsMidiSetup as obsMidiSetup
import midiObsJSONsetup as obsJSONsetup
import midiObsControls as obsControls
import midiObsDisplay as obsDisplay

# I couldn't find anything useful to do with the video devices directly
# switching between video feeds is done with scenes
def filterOutVideoDevices(data):

    cfg = []

    if "deviceType" in data[0]:
        for d in data:
            if d["deviceType"] != "video":
                cfg.append(d)
        return cfg

    if "inputType" in data[0]:
        for d in data:
            if d["inputType"] != "video":
                cfg.append(d)
        return cfg

    return data

def main():
    global _midiObsData

    config = {}
    config["scriptDir"] = _scriptDir
    config["scriptLogging"] = _scriptLogging

    fileSettings = obsJSONsetup.JsonFileSettings(_scriptLogging)

    signal.signal(signal.SIGINT, fileSettings.exitNicely)

    desc = """MIDI - OBS Controller"""
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-j", "--jsonfile", type=str, help="load a midi settings json file")
    parser.add_argument("-c", "--jsoncfgfile", type=str, help="load a json configuration file")        
    parser.add_argument("-t", "--testobs", action='store_true', help="run the test OBS script")      
    parser.add_argument("-v", "--wsver", action='store_true', help="get version number of OBS Websockets")
    parser.add_argument("-k", "--inputkinds", action='store_true', help="list inputs attached to OBS")
    parser.add_argument("--getsetlist", action='store_true', help="list get set and other options")

    args = parser.parse_args()

    if args.jsoncfgfile:
        error, midiObsJSON = fileSettings.loadJsonFile(args.jsonCfgfile)
    else:
        error, midiObsJSON = fileSettings.loadJsonFile(_midiObsJSONfilename)

    if error:
        display = obsDisplay.ObsDisplay(config, None, None, None)
        display.showErrorGUI(midiObsJSON)           
        print(f"json config data not loaded: {midiObsJSON}")
        sys.exit(0)       

    config = midiObsJSON.pop("config")
    config["scriptDir"] = _scriptDir
    config["scriptLogging"] = _scriptLogging

    if args.jsonfile:
        midiObsFile = args.jsonFile
        config["midiObsPath"] = ntpath.dirname(midiObsFile)
        config["midiObsFile"] = ntpath.basename(midiObsFile)
    else:
        midiObsFile = os.path.join(config["midiObsPath"], config["midiObsFile"])

    fCheck = fileSettings.filePermissionsCheck(midiObsFile)
    if not fCheck:
        midiObsPath = ntpath.dirname(midiObsFile)
        display = obsDisplay.ObsDisplay(config, None, None, None)
        display.showErrorGUI(f"cannot write to directory: {midiObsPath}")
        sys.exit(0)     

    midiLoadError, _midiObsData = fileSettings.loadJsonFile(midiObsFile)
    
    controls = obsControls.ObsControls(config, midiObsJSON)

    if args.getsetlist:
        controls.makeGetSetList()
        return

    if args.wsver:
        controls.getWSversion()
        print("complete")
        return

    if args.testobs:
        controls.testOBSstuff()
        print("OBS test complete")
        return

    if args.inputkinds:
        controls.getInputKinds()
        return

    error, inputsAndScenes = controls.getCurrentInputsAndScenes()
    if error:
        display = obsDisplay.ObsDisplay(config, None, None, None)
        if inputsAndScenes == "cannot connect":
            print("Cannot connect, proably need to set the password in the midiObsConfig.json file")
            display.showErrorGUI("Cannot connect, proably need to set the password in the midiObsConfig.json file")
            sys.exit(0)
        else:
            display.showErrorGUI(f"OBS not Running or OBS-Websocket not installed,\n{inputsAndScenes}")
            sys.exit(0)        

    midiSetup = obsMidiSetup.MidiSettings(config)
    error, midiDevices = midiSetup.listMidiDevices()
    if error:
        display = obsDisplay.ObsDisplay(config, None, None, None)
        display.showErrorGUI("No MIDI input device attached")
        sys.exit(0)

    midiCheck = fileSettings.checkMidiObsData(_midiObsData)
    if midiLoadError or midiCheck:          
        if midiLoadError:
            err = _midiObsData
        else:
            err = midiCheck

        print(f"json midi data file not loaded: {err}, creating default")
        _midiObsData = fileSettings.makeDefaultMidiObsData(midiObsJSON, inputsAndScenes, midiDevices)
        error, message = fileSettings.saveJSONfile(config["midiObsPath"],config["midiObsFile"],_midiObsData)
        if error:
            display = obsDisplay.ObsDisplay(config, None, None, None)
            display.showErrorGUI(message)
            sys.exit(0)

    obsSocket = controls.websocketConnect()
    loop = asyncio.get_event_loop()

    ## remove references to video 
    _midiObsData["midiConfiguration"] = filterOutVideoDevices(_midiObsData["midiConfiguration"])
    midiObsJSON["inputKinds"]["video"] = []
    inputsAndScenes["GetInputList"]["inputs"] = filterOutVideoDevices(inputsAndScenes["GetInputList"]["inputs"])

    # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))
    # sys.exit()

    display = obsDisplay.ObsDisplay(config, midiObsJSON, _midiObsData, obsSocket)

    # print(json.dumps(midiObsJSON, indent=4, sort_keys=False))
    # sys.exit()

    exitAction = ""
    if _midiObsData["midiConfigured"] == 0:
        exitAction = "setup"

    while True:
        if exitAction == "close" or exitAction == "exit":
            break

        elif exitAction == "setup":
            exitAction, _midiObsData = display.showMidiSetupGUI(inputsAndScenes, midiDevices, _midiObsData)
            if not _midiObsData:
                display.showErrorGUI(f"unhelpful error message (midiObsData empty?)")
                sys.exit(0) 
            if exitAction == "error":
                display.showErrorGUI(f"{_midiObsData}")
                sys.exit(0)

        elif exitAction == "host":
            exitAction, config = display.showHostSetupGUI(config, midiObsJSON)
            if exitAction == "error":
                display.showErrorGUI(f"{config}")
                sys.exit(0)

        else:            
            exitAction, error = loop.run_until_complete(display.showMidiInputGUI(_midiObsData))
            if error:
                display.showErrorGUI(f"{error}")
                sys.exit(0)

    return


if __name__ == "__main__":
    main()