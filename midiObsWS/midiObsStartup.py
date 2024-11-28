
import os
import sys
import tempfile

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)

from midiObsWS.midiObsDisplay import ObsDisplay
from midiObsWS.midiObsDatabase import ObsDatabase
from midiObsWS.midiObsMidiSettings import ObsMidiSettings
from midiObsWS.midiObsControls import ObsControls

class ObsStartup():

    def __init__(self, scriptDir, scriptLogging):
        self.scriptDir = scriptDir 
        self.scriptLogging = scriptLogging
        return
    
    def filePermissionsCheck(self, pathfile):

        path = os.path.dirname(pathfile)
        try:
            testfile = tempfile.TemporaryFile(dir = path)
            testfile.close()
        except (OSError, IOError) as e:
            if e.errno == 13  or e.errno == 17:  # errno.EACCES, errno.EEXIST
                return False
            e.filename = path
            raise

        return True

    def checkCanWriteToScriptDir(self):

        # fn = os.path.join(self.scriptDir, jsonConfigFilename)
        fCheck = self.filePermissionsCheck(self.scriptDir)
        if not fCheck:
            print(f"cannot write to {self.scriptDir}, exiting")
            display = ObsDisplay()
            display.showErrorGUI(f"cannot write to directory: {self.scriptDir}")
            sys.exit(0)     

        return

    def checkForDatabase(self):
        db = ObsDatabase(self.scriptDir)
        error, message = db.createDefaultDatabase()
        if error:
            print(message)
            display = ObsDisplay()
            display.showErrorGUI(message)
            sys.exit(0)
        
        return True
        
    def checkForMidiInputDevice(self):        
        midiSetup = ObsMidiSettings(None)
        error, midiDevices = midiSetup.listMidiDevices()
        if error:
            print("No MIDI input device attached (checkForMidiInputDevice)")
            display = ObsDisplay()
            display.showErrorGUI("No MIDI input device attached")
            sys.exit(0)

        return midiDevices
    
    def hasMidiInDeviceChanged(self, config, midiDevices):
        
        if config["midiSet"] == 0:
            return 0
        
        if config["midiIn"] not in midiDevices:
            return 0

        return config["midiSet"]
    
    def getInputsAndScenes(self, config):
        
        db = ObsDatabase(self.scriptDir)
        controls = ObsControls(config)
        
        ws={}
        ws["Address"] = config["wsAddress"]
        ws["Port"] = config["wsPort"]
        ws["Password"] = config["wsPassword"]
        
        error, inputsAndScenes = controls.getCurrentInputsAndScenes(ws)
        if error:
            print(f"error: {inputsAndScenes}")
            return {}

        # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))
        
        inputs = inputsAndScenes["GetInputList"]["inputs"]
        scenes = inputsAndScenes["GetSceneList"]["scenes"]
        
        inputData = db.setInputsList(inputs)
        scenesData = db.setScenesList(scenes)
        
        # print(json.dumps(inputData, indent=4, sort_keys=False))
        # print(json.dumps(scenes, indent=4, sort_keys=False))
        
        return {"inputs": inputs, "scenes": scenes}

    def getListofInputKinds(self, config):
        obsControls = ObsControls(config)        
        e, data = obsControls.getCurrentInputsAndScenes()
        if "GetInputList" not in data:
            return ["Input list not found", e, data]
               
        return data["GetInputList"]

