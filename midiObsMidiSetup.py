
import sys
import mido
import argparse
import time
import json
import os

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    

class MidiSettings:
    def __init__(self, config):
        self.config = config

        return

    class MIDIvalue(object):
        status = ""
        control = 0
        value = 0

    def setMidiObsValue(self, focus, midiVal, midiConfigData):

        print(focus)
        if focus == None:
            print("error: input not identified")
            return midiConfigData

        section, action, type = focus.split("_",2)
        # print(section, action, type)
        # print(midiObsData)
        for d in midiConfigData:
            if d["section"] == section and d["action"] == action:
                if type == "c":
                    d["changeID"] = midiVal.control
                elif type == "b":
                    d["buttonID"] = midiVal.control
                # d["control"] = controlType
                # print(f"id: {midiControl}, control: {controlType}")
                # print(json.dumps(d, indent=4, sort_keys=False))
                break

        print("-----------------------------")

        return midiConfigData


    def midiToObj(self, midi):
        """
        converts the object provided by mido to something more suitable
        for what I am needing to do - for less programming later on.

        Input, eg:
            control_change channel=10 control=6 value=44 time=0
            note_on channel=10 note=14 velocity=127 time=0
            note_off channel=10 note=14 velocity=0 time=0

        Output:
            status:  button - a button
                     change - slider or knob
            control: The identity number of the individual button, slider, knob, etc
            value:   button - 127 on press, 0 on release
                     change - a value between 0 and 127.
        """
        midiVal = self.MIDIvalue()

        if midi.type.startswith("note_"):
            midiVal.status = "button"   
            midiVal.value = midi.velocity
            midiVal.control = midi.note
        elif midi.type == "control_change":
            midiVal.status = "change"
            midiVal.value = midi.value
            midiVal.control = midi.control
        else:   ## unknown type
            midiVal.status = midi.type
            midiVal.value = -1
            midiVal.control = -1

        return midiVal

    def getFirstMidiInput(self):

        inputNames = mido.get_input_names()
        if not inputNames:
            print("no MIDI input devices attached?")
            return None

        return 0

    def listMidiDevices(self):
        
        devices = []
        inputNames = mido.get_input_names()
        if not inputNames:
            return True, []

        c=0
        for n in inputNames:
            devices.append(n)
            c+=1

        return False, devices