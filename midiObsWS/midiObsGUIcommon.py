
import sys
import re
import time
import json

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
class ObsGUIcommon(object):

    def __init__(self, config):
        self.config = config


    def validateDigitInput(self, newText, maxLen=6):
        
        if newText == "":
            return True
        
        if len(str(newText)) > int(maxLen):
            return False
        
        if newText.isdigit():
            return True
        else:
            return False    
    
    def validateStringInput(self, newText, maxLen=40):
        
        if newText == "":
            return True
        
        if len(str(newText)) > int(maxLen):
            return False
        
        return False


    def setAllnames(self, allNames, names):

        for n in names:
            allNames.append(n)

        return allNames

    def makeSectionControls(self, sg, buttons):
        
        i=1
        data = []
        names = []
        for b in buttons:
            title = f"{i}. {b['display']}"
            name = f"controls_{b['id']}_b"
            names.append({
                "section": "controls", 
                "name": name, 
                "midiID": b["buttonID"], 
                "value": b["buttonValue"], 
                "id": b["id"], 
                "uuid": b["name"],
                "type": b["ioKind"],
                "title": b["display"] + " (control)",
                "changed": False})
            
            if sg is not None:
                data.append([sg.Text(title, size=(30)), sg.In(key=name, enable_events=True, size=(3))])
            i+=1
        
        return data, names
        
    def makeSectionScenes(self, sg, userScenes):
        
        i=1
        data = []
        names = []
        for b in userScenes:
            title = f"{i}. {b['name']}"
            name = f"scenes_{b['id']}_b"
            names.append({
                "section": "scenes", 
                "name": name, 
                "midiID": b["buttonID"], 
                "value": b["buttonValue"], 
                "id": b["id"], 
                "type": "display",
                "uuid": b["uuid"],
                "title": b["name"] + " (scene)",
                "changed": False})
            
            if sg is not None:
                data.append([sg.Text(title, size=(30)), sg.In(key=name, enable_events=True, size=(3))])
            i+=1
        
        return data, names
        
    def makeSectionSourcesBtn(self, sg, userInputs):
        
        i=1
        data = []
        names = []
        for b in userInputs:
            vid = ""
            if b["inputType"] == "video":
                vid = " (video)"
            
            title = f"{i}. {b['name']}{vid}"
            name = f"sources_{b['id']}_b"
            names.append({
                "section": "sourcesBtn", 
                "name": name, 
                "midiID": b["buttonID"], 
                "value": b["buttonValue"], 
                "id": b["id"], 
                "type": b["inputType"],
                "uuid": b["uuid"],
                "title": b["name"] + " (button)",
                "changed": False})
            
            if sg is not None:
                data.append([sg.Text(title, size=(30)), sg.In(key=name, enable_events=True, size=(3))])
            i+=1
        
        return data, names
    
    def makeSectionSourcesRot(self, sg, userInputs):
     
        i=1
        data = []
        names = []
        for b in userInputs:
            if b["inputType"] == "video":
                continue
            
            title = f"{i}. {b['name']}"
            name = f"sources_{b['id']}_r"
            names.append({
                "section": "sourcesRot", 
                "name": name, 
                "midiID": b["changeID"], 
                "value": b["changeValue"], 
                "id": b["id"], 
                "type": b["inputType"],
                "uuid": b["uuid"],
                "title": b["name"] + " (rotary)",
                "changed": False})
            
            if sg is not None:
                data.append([sg.Text(title, size=(30)), sg.In(key=name, enable_events=True, size=(3))])
            i+=1
        
        return data, names
        
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

    def setDefaultValue(self, value):        
        if value < 0:
            return ""        
        return str(value)

    def updateAllInputByName(self, allInputs, update, name):

        for a in allInputs:
            if a["name"] == name:
                a = update
                break
            
        return allInputs

    async def setObsDataValue(self, midiVal, allInputs):

        action = False
        types = dict()
        types["r"] = "change"  # rotary knob
        types["b"] = "button"
        
        # print ("------")
        # print (f"control: {midiVal.control}, status {midiVal.status}, value: {midiVal.value}")
        # print ("=-=-=-=-=-")
        # print(json.dumps(allInputs, indent=4, sort_keys=False))

        midi = {}
        idxName = None # -1
        for a in allInputs:
            section, id, type = a["name"].split("_", 2)            
            if a["midiID"] == midiVal.control and midiVal.status == types[type]:
                midi = a
                idxName = midi["name"]
                break
            # idx+=1

        # print ("------------")
        # print (midi)

        if not midi:
            return False, allInputs, None # -1

        if not "lastValue" in midi:
            midi["lastValue"] = None

        # print(f"midiVal.value {midiVal.value}, midiVal.status {midiVal.status}, idx {idx} ")

        if midiVal.status == "button":  
            if midiVal.value == 0:     ## button released  
                midi["lastValue"] = midi["value"]
                midi["value"] = midi["value"] ^ 1                    
                action = True
                # print(midi)
                allInputs = self.updateAllInputByName(allInputs, midi, idxName)
            # if midiVal.value == 127:   ## button pressed
            #     midi["value"] = 0
        elif midiVal.status == "change":
            midi["lastValue"] = midi["value"]
            midi["value"] = midiVal.value
            action = True
            allInputs = self.updateAllInputByName(allInputs, midi, idxName)
            # allInputs[idx] = midi
 
        # time.sleep(0.05)
        # allInputs[idx] = midi
        return action, allInputs, midi
