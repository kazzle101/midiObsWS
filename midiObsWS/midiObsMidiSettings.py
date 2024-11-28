
import sys
import mido
import mido.backends.rtmidi  # included as a workaround for PYinstaller
import json

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    

class ObsMidiSettings:
    def __init__(self, config):
        self.config = config
        return

    class MIDIvalue(object):
        status = ""
        control = 0
        value = 0
        channel = 0

    def midiReset(self, midiOut):

        if not midiOut:
            return 

        with mido.open_output(midiOut, autoreset=True) as outMidi:
            outMidi.reset()
        
        return
    
    async def setMidiDeviceKeyOnOrOff(self, midiOut, midiChannel, midiID, buttonStatus, onOff):

        if not midiOut or midiID < 0:
            return buttonStatus
            
        if onOff == "on" or onOff == True:
            msg = mido.Message('note_on', channel=midiChannel, note=midiID) 
            if midiID not in buttonStatus:
                buttonStatus.append(midiID)

        else:
            msg = mido.Message('note_off', channel=midiChannel, note=midiID)
            if midiID in buttonStatus:
                buttonStatus.remove(midiID)

        with mido.open_output(midiOut) as outMidi:
            outMidi.send(msg)

        return buttonStatus
    
    async def setMidiDeviceChangeValue(self, midiOut, midiChannel, midiID, buttonStatus, value):
    
        if not midiOut or midiID < 0:
            return buttonStatus
        
        msg = mido.Message('control_change', channel=midiChannel, control=midiID, value=value)    
        with mido.open_output(midiOut) as outMidi:
            outMidi.send(msg)
        
        return buttonStatus

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
            channel: used for sending messages to the midi device
        """
        midiVal = self.MIDIvalue()

        if midi.type.startswith("note_"):
            midiVal.status = "button"   
            midiVal.value = midi.velocity
            midiVal.control = midi.note
            midiVal.channel = midi.channel
        elif midi.type == "control_change":
            midiVal.status = "change"
            midiVal.value = midi.value
            midiVal.control = midi.control
            midiVal.channel = midi.channel
        else:   ## unknown type
            midiVal.status = midi.type
            midiVal.value = -1
            midiVal.control = -1
            midiVal.channel = -1

        return midiVal

    def listMidiOutputDevices(self):

        devices = []
        outputNames = mido.get_output_names()
        if not outputNames:
            return True, []    

        for n in outputNames:
            if n not in devices:
                devices.append(n)

        return False, devices

    def listMidiDevices(self):
        
        devices = []
        inputNames = mido.get_input_names()
        if not inputNames:
            return True, []

        for n in inputNames:
            if n not in devices:
                devices.append(n)

        return False, devices