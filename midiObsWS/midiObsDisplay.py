
import sys
import asyncio
import mido

_guiTheme = "SandyBeach"
_guiMinSize = (720,480)

from midiObsWS.midiObsGUIerror import ObsGUIerror
from midiObsWS.midiObsGUIsetupHost import ObsGUIsetupHost
from midiObsWS.midiObsGUIsetupMidi import ObsGUIsetupMidi
from midiObsWS.midiObsGUIshowMidiObs import ObsGUIshowMidiObs

class ObsDisplay(object):
    
    def __init__(self):
        return
    
    def checkMidi(self, config):
         
        ## detect possible "MidiInWinMM::openPort: error creating Windows MM MIDI input port." error.
        ## This means mido thinks the port is already in use, the quick fix is to restart the computer
        try:
            with mido.open_input(config["midiIn"], backend='mido.backends.rtmidi') as inMidi:
                while inMidi.receive(block=False) is not None:
                    pass

        except Exception as e:
            print("MIDI ERROR (mido):")
            print(e)
            return "error", f"MIDI Error: {str(e)}"        
        
        return False, ""
    
    
    def showErrorGUI(self, error):
        guiError = ObsGUIerror(_guiTheme, _guiMinSize)
        guiError.showErrorGUI(error)
        return
        
    def showHostSetupGUI(self, config, midiDevices):
        loop = asyncio.get_event_loop()
        
        obsGUIsetupHost = ObsGUIsetupHost(_guiTheme, _guiMinSize)
        exitAction, newConfig = loop.run_until_complete(obsGUIsetupHost.showHostSetupGUI(config))
        return exitAction, newConfig
    
    def showMidiSetupGUI(self, config, scriptDir):

        exitAction, message = self.checkMidi(config)
        if exitAction:
            return  exitAction, message
        
        setupMidi = ObsGUIsetupMidi(_guiTheme, _guiMinSize, scriptDir)
        exitAction, message = setupMidi.showMidiSetupGUI(config)
        return exitAction, message

    def showMidiObsGUI(self, config, scriptDir):
        loop = asyncio.get_event_loop()
        
        exitAction, message = self.checkMidi(config)
        if exitAction:
            return  exitAction, message
        
        showMidi = ObsGUIshowMidiObs(_guiTheme, _guiMinSize, scriptDir)
        exitAction, message = loop.run_until_complete(showMidi.showMidiObsGUI(config))
        return exitAction, message
        