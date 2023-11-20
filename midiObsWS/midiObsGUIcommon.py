
from faulthandler import disable
import sys
import mido
import time
import json
import os
import time
import re
# import PySimpleGUI as sg
# import asyncios

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
class ObsGUIcommon(object):

    def __init__(self, config, midiObsConfig, midiObsData):
        self.config = config
        self.midiObsConfig = midiObsConfig
        self.midiObsData = midiObsData

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

    def limitMidiChannels(self, value):

        value = self.stringNumbersOnly(value)
        if not value or value == "":
            return "0"

        if int(value) < 1:
            return "1"

        if int(value) > 16:
            return "16"

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

    def setObsDataValue(self, midiVal, obsData):

        # print(midiVal)

        # print("showMidiInputGUI  ID: {: >2}, status: {}, value: {: >3}"
        #         .format(midiVal.control, midiVal.status, midiVal.value))        

        midi = {}
        idx = 0
        for m in obsData:
            if m["buttonID"] == midiVal.control and midiVal.status == "button":
                midi = m
                break
        
            if m["changeID"] == midiVal.control and midiVal.status == "change":
                midi = m
                break
            idx+=1

        if not midi:
            return obsData, -1

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
        obsData[idx] = midi
        return obsData, idx

    def setKeyName(self, section, name):
        return section+"_"+name
    
    def getMidiDeviceInfo(self, midiObsData):

        midi = {}
        midi["midiDevice"] = midiObsData["midiDevice"]
        midi["midiOutputDevice"] = midiObsData["midiOutputDevice"]
        midi["midiConfigured"] = midiObsData["midiConfigured"]
        midi["midiChannel"] = int(midiObsData["midiChannel"])
        return midi


    def getAllItemsNamesList(self, inputsAndScenes):

        # print(json.dumps(inputsAndScenes, indent=4, sort_keys=False))

        nameList=[]
        for b in self.midiObsConfig["buttons"]:
            nameList.append(self.setKeyName("controls",b["name"]+"_b"))

        if "inputs" in inputsAndScenes["GetInputList"]:
            for i in inputsAndScenes["GetInputList"]["inputs"]:
                nameList.append(self.setKeyName("sources", i["inputName"]+"_b"))
                nameList.append(self.setKeyName("sources", i["inputName"]+"_c"))

        if "scenes" in inputsAndScenes["GetSceneList"]:
            for s in inputsAndScenes["GetSceneList"]["scenes"]:
                nameList.append(self.setKeyName("scenes",s["sceneName"]+"_b"))

        return nameList

    def getSectionData(self, midiData, thisSection):

        section = []

        if not "midiConfiguration" in midiData:
            return section

        for s in midiData["midiConfiguration"]:
            if s["section"] == thisSection:
                section.append(s)
            
        return section

    # not used
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
