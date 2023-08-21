
# from faulthandler import disable
import sys
import asyncio

# https://github.com/obsproject/obs-websocket/blob/master/docs/generated/protocol.md

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
_guiTheme = "SandyBeach"
_guiMinSize = (720,480)


from midiObsWS.midiObsGUIerror import ObsGUIerror
from midiObsWS.midiObsGUIsetupHost import ObsGUIsetupHost
from midiObsWS.midiObsGUIsetupMidi import ObsGUIsetupMidi
from midiObsWS.midiObsGUIshowMidiObs import ObsGUIshowMidiObs

class ObsDisplay(object):
    
    def __init__(self, config, midiObsConfig):
        self.config = config
        # self.midiObsData = midiObsData
        self.midiObsConfig = midiObsConfig
        # self.scriptLogging = config["scriptLogging"]
        # self.obsSocket = obsSocket
        # self.buttonStatus = []
        # self.scriptDir = config["scriptDir"]

    def showHostSetupGUI(self, midiObsConfigFile, midiObsDataFile, config):
        loop = asyncio.get_event_loop()

        obsGUIsetupHost = ObsGUIsetupHost(_guiTheme, _guiMinSize, config)
        exitAction, config, midiObsData = loop.run_until_complete(obsGUIsetupHost.showHostSetupGUI(midiObsConfigFile, midiObsDataFile, config))

        return exitAction, config, midiObsData


    def showMidiSetupGUI(self, inputsAndScenes, midiDevices, midiObsData):

        setupMidi = ObsGUIsetupMidi(_guiTheme, _guiMinSize, self.config, self.midiObsConfig)
        exitAction, updatedMidiObsData = setupMidi.showMidiSetupGUI(inputsAndScenes, midiDevices, midiObsData)

        return exitAction, updatedMidiObsData

    
    # the main screen showing midi inputs and OBS actions
    def showMidiObsGUI(self, midiObsData):
        loop = asyncio.get_event_loop()

        showMidiObs = ObsGUIshowMidiObs(_guiTheme, _guiMinSize, self.config, self.midiObsConfig)
        exitAction, error = loop.run_until_complete(showMidiObs.showMidiObsGUI(midiObsData))

        return exitAction, error
  
    def showErrorGUI(self, error):
        guiError = ObsGUIerror(_guiTheme, _guiMinSize)
        guiError.showErrorGUI(error)
        return

