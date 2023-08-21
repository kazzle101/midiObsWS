import sys
import os
import tempfile
import json
import logging

if __name__ == "__main__":
    print("this python script only works from: midi-obs-ws.py")
    sys.exit(0)

class ObsFiles:

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.scriptDir = os.path.dirname(sys.executable)
        else:
            self.scriptDir = os.path.dirname(os.path.realpath(__file__))

        self.scriptLogging = os.path.join(self.scriptDir, "midiObsDebug.log")

    # def exitNicely(self, signum, frame):
    #     print("")
    #     print("exiting....")    
    #     sys.exit(0)        

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

        path = os.path.dirname(pathfile)
        # print("filePermissionsCheck")
        # print(path)
        # print(self.scriptDir)
        # print(os.path.dirname(sys.executable))

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