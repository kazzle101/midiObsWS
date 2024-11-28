
import sys
import asyncio

_guiTheme = "SandyBeach"
_guiMinSize = (720,480)

from midiObsWS.midiObsGUIerror import ObsGUIerror
from midiObsWS.midiObsGUIsetupHost import ObsGUIsetupHost
from midiObsWS.midiObsGUIsetupMidi import ObsGUIsetupMidi
from midiObsWS.midiObsGUIshowMidiObs import ObsGUIshowMidiObs

class ObsDisplay(object):
    
    def __init__(self):
        return
    
    def showErrorGUI(self, error):
        guiError = ObsGUIerror(_guiTheme, _guiMinSize)
        guiError.showErrorGUI(error)
        return
    
    def showHostSetupGUI(self, config, midiDevices):
        loop = asyncio.get_event_loop()
        
        obsGUIsetupHost = ObsGUIsetupHost(_guiTheme, _guiMinSize)
        # exitAction, newConfig = obsGUIsetupHost.showHostSetupGUI(config, midiDevices)
        exitAction, newConfig = loop.run_until_complete(obsGUIsetupHost.showHostSetupGUI(config))

        return exitAction, newConfig
    
    def showMidiSetupGUI(self, config, scriptDir):

        setupMidi = ObsGUIsetupMidi(_guiTheme, _guiMinSize, scriptDir)
        exitAction, message = setupMidi.showMidiSetupGUI(config)

        return exitAction, message

    def showMidiObsGUI(self, config, scriptDir):
        loop = asyncio.get_event_loop()
        
        showMidi = ObsGUIshowMidiObs(_guiTheme, _guiMinSize, scriptDir)
        exitAction, message = loop.run_until_complete(showMidi.showMidiObsGUI(config))
        
        return exitAction, message
        