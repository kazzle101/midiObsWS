
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

    def midiReset(self, midiOutputDevice):

        if not midiOutputDevice or midiOutputDevice == "":
            return

        with mido.open_output(midiOutputDevice, autoreset=True) as outMidi:
            outMidi.reset()
        
        return

    # used when an entry is manually changed on the GUIsetupMidi page
    # midiConfig == midiObsData["midiConfiguration"]
    def setMidiKeyValue(self, event, values, midiConfig):

        if event == None:
            return midiConfig
        
        # an entry that has been set to blank (unused) gets changed to -1
        section, action, type = event.split("_",2)
        value = values[event]
        if not value:
            value = -1
        else:
            value = int(value)

        for d in midiConfig:
            if d["section"] == section and d["action"] == action:
                if type == "c":
                    d["changeID"] = value
                elif type == "b":
                    d["buttonID"] = value
                break

        return midiConfig

    # used when an entry is updated using a midi controller on the GUIsetupMidi page
    # midiConfig == midiObsData["midiConfiguration"]
    def setMidiObsValue(self, focus, midiVal, midiConfig):

        if focus == None:
            print("error: input not identified")
            return midiConfig

        section, action, type = focus.split("_",2)
        for d in midiConfig:

            if d["section"] == section and d["action"] == action:
                if type == "c":
                    d["changeID"] = midiVal.control
                elif type == "b":
                    d["buttonID"] = midiVal.control

                break

        return midiConfig

    async def setMidiDeviceKey(self, midiOutputDevice, midiVal, buttonStatus):

        if midiVal.control < 0:
            return buttonStatus

        if midiVal.status == "button" and midiVal.value == 0:
            if midiVal.control in buttonStatus:
                msg = mido.Message('note_on', channel=midiVal.channel, note=midiVal.control) 
                buttonStatus.remove(midiVal.control)
            else:
                msg = mido.Message('note_off', channel=midiVal.channel, note=midiVal.control) 
                buttonStatus.append(midiVal.control)
        
            with mido.open_output(midiOutputDevice) as outMidi:
                outMidi.send(msg)

        if midiVal.status == "change":
            msg = mido.Message('control_change', channel=midiVal.channel, control=midiVal.control, value=midiVal.value) 

            with mido.open_output(midiOutputDevice) as outMidi:
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

    def getFirstMidiInput(self):

        inputNames = mido.get_input_names()
        if not inputNames:
            print("no MIDI input devices attached?")
            return None

        return 0

    def listMidiOutputDevices(self):

        devices = []
        outputNames = mido.get_output_names()
        if not outputNames:
            return True, []    

        for n in outputNames:
            devices.append(n)

        return False, devices

    def listMidiDevices(self):
        
        devices = []
        inputNames = mido.get_input_names()
        if not inputNames:
            return True, []

        for n in inputNames:
            devices.append(n)

        return False, devices