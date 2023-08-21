
import os
import sys
import asyncio

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

from midiObsWS.midiObsFiles import ObsFiles
from midiObsWS.midiObsDisplay import ObsDisplay
from midiObsWS.midiObsJSONsetup import ObsJSONsetup
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsControls import ObsControls

class ObsStartup():

    def __init__(self, scriptLogging):
        if getattr(sys, 'frozen', False):
            self.scriptDir = os.path.dirname(sys.executable)
        else:
            self.scriptDir = os.path.dirname(os.path.realpath(__file__))

        self.scriptLogging = scriptLogging

        self.ws = {}
        self.ws["Address"] = None
        self.ws["Port"] = None
        self.ws["Password"] = None

        return

    def checkCanWriteToScriptDir(self, jsonConfigFilename, config):
        obsFiles = ObsFiles()

        fn = os.path.join(self.scriptDir, jsonConfigFilename)
        fCheck = obsFiles.filePermissionsCheck(fn)
        if not fCheck:
            print(f"cannot write to {self.scriptDir}, exiting")
            display = ObsDisplay(config, None)
            display.showErrorGUI(f"cannot write to directory: {self.scriptDir}")
            sys.exit(0)     

        return

    def loadObsConfigJsonFile(self, midiObsConfigFile, config):
        obsFiles = ObsFiles()
        obsJSONsetup = ObsJSONsetup(self.scriptLogging)

        fn = os.path.join(self.scriptDir, midiObsConfigFile)
        error, midiObsConfig = obsFiles.loadJsonFile(fn)
        if error:
            midiObsConfig = obsJSONsetup.createDefaultConfigData(self.scriptDir)
            print(f"creating default {midiObsConfigFile} config file")
            error, msg = obsFiles.saveJSONfile(self.scriptDir, midiObsConfigFile, midiObsConfig)
            if error:            
                display = ObsDisplay(config, None)
                display.showErrorGUI(msg)           
                print(f"json config data not loaded: {midiObsConfigFile}")
                sys.exit(0)       

        # convert old data to new version of config file
        if "midiObsFile" in midiObsConfig["config"]:
            midiObsConfig["config"]["midiObsDataFile"] = midiObsConfig["config"]["midiObsFile"]
            midiObsConfig["config"].pop("midiObsFile", None)

        return midiObsConfig
    
    def loadObsDataJsonFile(self, midiObsDataFile, config):
        obsFiles = ObsFiles()
        obsJSONsetup = ObsJSONsetup(self.scriptLogging)        

        fn = os.path.join(self.scriptDir, midiObsDataFile)
        error, midiObsData = obsFiles.loadJsonFile(fn)
        if error:
            midiObsData = obsJSONsetup.createDefaultData()
            print(f"creating default {midiObsDataFile} data file")
            error, msg = obsFiles.saveJSONfile(self.scriptDir, midiObsDataFile, midiObsData)
            if error:            
                display = ObsDisplay(config, None)
                display.showErrorGUI(msg)           
                print(f"json data data not loaded: {midiObsDataFile}")
                sys.exit(0)      

        return midiObsData
    
    def checkForMidiInputDevice(self, config, midiObsData):
        midiSetup = ObsMidiSettings(config)
        error, midiDevices = midiSetup.listMidiDevices()
        if error:
            print("No MIDI input device attached")
            display = ObsDisplay(config, None)
            display.showErrorGUI("No MIDI input device attached")
            sys.exit(0)

        if not midiObsData["midiDevice"]:
            midiObsData["midiDevice"] = midiDevices[0]

        return midiObsData, midiDevices
    
    def setupHost(self, config, midiObsData):

        loop = asyncio.get_event_loop()
        midiObsConfigFile = config["midiObsConfigFile"]
        midiObsDataFile = config["midiObsDataFile"]

        display = ObsDisplay(config, None)
        exitAction, config, midiObsData = display.showHostSetupGUI(midiObsConfigFile, midiObsDataFile, config)
        if exitAction == "error":
            display.showErrorGUI(f"{config}")
            sys.exit(0)
        if exitAction == "exit":
            sys.exit(0)

        # config["scriptDir"] = self.scriptDir
        # config["scriptLogging"] = self.scriptLogging

        self.ws["Address"] = config["wsAddress"]
        self.ws["Port"] = config["wsPort"]
        self.ws["Password"] = config["wsPassword"]

        return exitAction, midiObsData, config


    def setInputsAndScenes(self, config, midiObsData, midiObsConfig):
        obsJSONsetup = ObsJSONsetup(self.scriptLogging)
        obsFiles = ObsFiles()

        if "wsPassword" in config and config["wsPassword"]: 
            self.ws["Address"] = config["wsAddress"]
            self.ws["Port"] = config["wsPort"]
            self.ws["Password"] = config["wsPassword"]

        previousMidiObsData = midiObsData
        controls = ObsControls(config, midiObsData, midiObsConfig)
        display = ObsDisplay(config, None)

        while True:
            if self.ws["Password"] is not None:
                ws = self.ws
            else:
                ws = None

            error, inputsAndScenes = controls.getCurrentInputsAndScenes(ws)

            if error == False:
                break
                
            # print(error, inputsAndScenes)
            # print(json.dumps(self.ws, indent=4, sort_keys=False))

            if inputsAndScenes == "cannot connect":
                exitAction, midiObsData, cnf  = self.setupHost(config, midiObsData)
                if exitAction == "error":
                    display.showErrorGUI(f"{config}")
                    sys.exit(0)
                elif exitAction == "exit":
                    sys.exit(0)    
            else:
                print(f"OBS not Running or OBS-Websocket not installed,\n{inputsAndScenes}")
                display.showErrorGUI(f"OBS not Running or OBS-Websocket not installed,\n{inputsAndScenes}")
                sys.exit(0)   

        # config["scriptDir"] = self.scriptDir
        # config["scriptLogging"] = self.scriptLogging
        config["wsAddress"] = self.ws["Address"]
        config["wsPort"] = self.ws["Port"]
        config["wsPassword"] = self.ws["Password"]


        # print("setInputsAndScenes---------")
        # print(json.dumps(config, indent=4, sort_keys=False))

        if midiObsData["midiConfigured"] == 0 or not midiObsData["midiConfiguration"]:
            midiObsData = obsJSONsetup.makeDefaultMidiObsData(midiObsData, midiObsConfig, inputsAndScenes)

        if previousMidiObsData != midiObsData:
            error, message = obsFiles.saveJSONfile(self.scriptDir,config["midiObsDataFile"], midiObsData)
            if error:
                print(f"{message}")
                display.showErrorGUI(message)
                sys.exit(0)

        return inputsAndScenes, midiObsData, config

    def checkMidiObsData(self, config, midiObsData):
        display = ObsDisplay(config, None)
        jsonDataFilename = config["midiObsDataFile"]

        if type(midiObsData) is not dict:
            print(f"wrong JSON data type for {jsonDataFilename}")
            display.showErrorGUI(f"wrong JSON data type for {jsonDataFilename}")
            sys.exit(0)

        info = ""
        if not "midiDevice" in midiObsData:
            info += "midiDevice, "

        if not "midiConfigured" in midiObsData:
            info += "midiConfigured, "

        if not "midiConfiguration" in midiObsData:
            info += "midiConfiguration, "

        if info:
            info = info[0:-2]
            print(f"\n## Fields [{info}] missing from {jsonDataFilename}")
            display.showErrorGUI(f"fields [{info}] missing from {jsonDataFilename}")
            sys.exit(0)

        return False


