import sys
import mido
import time
import json
import os
import logging
import tempfile
import ntpath
import errno

if __name__ == "__main__":
    print("this python script only works from: midi-obs-ws.py")
    sys.exit(0)


class JsonFileSettings:
    def __init__(self, scriptLogging):
        self.scriptLogging = scriptLogging
        return

    def exitNicely(self, signum, frame):
        print("")
        print("exiting....")    
        sys.exit(0)        

    def getLogger(self, name, level=logging.INFO):
        logFormat = logging.Formatter('[%(asctime)s] (%(levelname)s) T%(thread)d : %(message)s')

        stdOutput = logging.StreamHandler(sys.stdout)
        stdOutput.setFormatter(logFormat)
        stdOutput.setLevel(level)

        fileOutput = logging.FileHandler(os.path.join(self.scriptLogging))
        fileOutput.setFormatter(logFormat)
        fileOutput.setLevel(level)

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(fileOutput)
        logger.addHandler(stdOutput)
        return logger

    def filePermissionsCheck(self, pathfile):

        path = ntpath.dirname(pathfile)

        try:
            testfile = tempfile.TemporaryFile(dir = path)
            testfile.close()
        except (OSError, IOError) as e:
            if e.errno == 13  or e.errno == 17:  # errno.EACCES, errno.EEXIST
                return False
            e.filename = path
            raise

        return True

    def saveJSONfile(self, outputPath, outputFilename, outputData):
        
        filename = os.path.join(outputPath, outputFilename)

        print(f"Saving json data to: {filename}")

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(outputData, f, ensure_ascii=False, indent=4)
        except IOError as e:                    
            return True, f"cannot write to directory: {outputPath}, Error: {e.errno}"

        return False, "ok"

    def loadJsonFile(self, filename):
        jsonData = {}

        if not os.path.isfile(filename):
            print(f"JSON file not found: {filename}")
            return True, f"JSON file not found: {filename}"

        # filename = os.path.join(_outputPath,_outputFile)
        with open(filename, 'r', encoding='utf-8') as f:
            try:    
                jsonData = json.load(f)
                print(f"loaded JSON File: {filename}")
            except Exception as e:
                print( "-------------------------------------------")
                print(f"Error Loading JSON File: {filename}")
                print(f"{e}")
                print("-------------------------------------------")
                return True, f"Error Loading JSON File: {filename}"
        
        # if midiObsData:
        #     midiObsData = self.checkJsonData(midiObsData)

        return False, jsonData

    def makeDefaultMidiObsData(self, midiObsJSON, inputsAndScenes, midiDevices):

        midiObsData = {}
        midiObsData["midiDevice"] = midiDevices[0]
        midiObsData["midiOutputDevice"] = ""
        midiObsData["midiChannel"] = 10
        midiObsData["midiConfigured"] = 0

        # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))

        midiConfig = []
        for b in midiObsJSON["buttons"]:
            data = {"section": "controls",
                    "action": b["name"],
                    "name": b["display"],
                    # "control": "button",
                    "buttonID": -1,                    
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": "" }
            midiConfig.append(data)

        for s in inputsAndScenes["GetInputList"]["inputs"]:
            data =  {"section": "sources",
                    "action": s["inputName"],
                    "name": s["inputName"],
                    # "control": "",
                    "buttonID": -1,
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": s["inputType"] }
            midiConfig.append(data)

        for s in inputsAndScenes["GetSceneList"]["scenes"]:
            data =  {"section": "scenes",
                    "action": s["sceneName"],
                    "name": s["sceneName"],
                    # "control": "",
                    "buttonID": -1,
                    "changeID": -1,
                    "buttonValue": 0,
                    "changeValue": 0,
                    "deviceType": "" }
            midiConfig.append(data)      
            
        midiObsData["midiConfiguration"] = midiConfig

        return midiObsData


    def checkMidiObsData(self, midiObsData):

        if type(midiObsData) is not dict:
            return "wrong JSON data type"
        
        info = ""
        if not "midiDevice" in midiObsData:
            info += "midiDevice, "

        if not "midiConfigured" in midiObsData:
            info += "midiConfigured, "
    
        if not "midiConfiguration" in midiObsData:
            info += "midiConfiguration, "

        if info:
            info = info[0:-2]
            print(f"\n## Fields [{info}] missing from jsonFile")
            return f"fields [{info}] missing from jsonFile"

        return ""
