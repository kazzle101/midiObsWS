
import FreeSimpleGUI as sg
import sys
import time

if __name__ == "__main__":
    print("this python script only works from: midiObsWS.py")
    sys.exit(0)
    
class ObsGUIerror(object):
    
    def __init__(self, guiTheme, guiMinSize):        
        self.guiTheme = guiTheme
        self.guiMinSize = guiMinSize
        return
    
    def showErrorGUI(self, error1, error2=False):

        sg.theme(self.guiTheme)

        print(f"AN ERROR: {error1}")

        errorMsg = []
        errorMsg.append("Ensure that OBS is runnning and that your Midi Device is plugged in before you start this program.")
        errorMsg.append("The installled version of OBS needs to be version 28 or greater and OBS-Websocket should be version 5 or higher.")
        
        layout = [[sg.Text('AN ERROR HAS OCCURED', font=("Helvetica", 12, "italic"))]]
        for e in errorMsg:
            layout.append([sg.Text(e)])
            
        layout.append([sg.Text(" ")])
        if error1:
            layout.append([sg.Text("Reported Error:", font=("Helvetica", 12, "italic"))])
            layout.append([sg.Text(error1)])

        if error2:
            layout.append([sg.Text(" ")])
            layout.append([sg.Text("Error:", font=("Helvetica", 12, "italic"))])
            layout.append([sg.Text(error2)])

        layout.append([sg.Button('Close')])

        window = sg.Window('MIDI-OBS ', layout, return_keyboard_events=True, 
                           resizable=True, finalize=True)
        window.set_min_size(self.guiMinSize)
        window.force_focus()

        while True:
            time.sleep(0.05)
            event, values = window.read(timeout = 100)
            
            if event == sg.WIN_CLOSED or event == 'Close':
                break

        window.close()
        return

    
