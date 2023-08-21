# midiObsWS
An interface to allow OBS to be controlled by a MIDI device via obs-Websockets.

This system has been written to provide basic functionality; scene switching, volume control and allow operation of the main controls such as recording, streaming and the virtual camera. The MIDI device I've used is a Behringer X-Touch Mini.

## Update August 2023
**Version 0.6 beta**
Tested with Python 3.11

Many updates and bugfixes, mostly around creating the default configuration files without having to know how the system works, also moving around functions to help make the code a bit more readable. A Windows Standalone executable is now incuded in the dist folder, copy onto your PC somewhere suitable and double-click it. This was created with PyInstaller using:
```
python -m PyInstaller '.\midiObs.py' --name midiObsWS -F 
```
Connect your MIDI input device and start OBS before you launch midiObsWS otherwise it will just say you need to connect a MIDI device and Start OBS then exit.

Files have been moved around so the installer can do its thing.

The setup.py should work if you have python and setuptools already installed:
```
git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
python setup.py install
python midiObs.py
```

## Manual Installation
### Windows (with python 3.9+ already installed)
```
git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui
python midiObs.py
```
### Apple Mac (macOS Ventura)
Getting it working proved to be more difficult than it should have been, I suspect milage may vary for others. This is because GTK is no longer suppied with macOS.
```
git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
$ sudo python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui
$ sudo port install rtmidi
```
if python-rtmidi says cannot find jack.h, try:
```
$ sudo python -m pip install python-rtmidi --install-option="--no-jack"
```
If you see an error, No Module named '__tkinter'
```
$ sudo port install py-tkinter tk +quartz
```
### Linux
I've not tested this on Linux, as I don't run a machine with a GUI desktop, however, installation should be:
```
git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
sudo python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui
python midiObs.py
```

## Use
Start OBS and configure your video, audio and scenes to how you like. Connect your MIDI device to a USB port.

In OBS setup the Websocket - Tools > obs-websocket Settings, enable Websocket server and generate a password, and click the Show Connect Info button for the login information. Now with OBS running, and the midi device connected, start midiObsWS with **python midiObs.py** When first run, the system will ask you for the obs-websocket server settings, if you are running midiObsWS on the same computer as OBS then _localhost_ can be used as the Server IP, as well as the midi device you will be using as a controller:

<img width="546" alt="midiObsWS_host" src="https://user-images.githubusercontent.com/1898711/205518626-77c082fc-8efd-46a9-9bd2-68c4f782189b.png">

Two files are created; _midiObsConfig.json_ this contains your OBS login details, a list of standard actions (toggle recording, etc) and a list of input kinds, these are used to distinguish between video and audio devices. The other file is _midiObsData.json_ this contains your mapping between the midi device and your standard actions, volume controls and scenes.

You can test the OBS connection by clicking the _Test OBS Connection_ button, on success it'll say OK and give you the version numbers for OBS and obs-websockets.

Enter the details and click _Save and Close_, the password is stored in plain text in the _midiObsConfig.json_ file, the system then connects to OBS to obtain the configuration and you will then be presented with the setup page, otherwise an error describing the problem will be shown.

<img width="725" alt="midiObsWS_setup" src="https://user-images.githubusercontent.com/1898711/205466660-bcf82571-3b88-43f0-ae47-b2d114d2bf90.png">

To attach a MIDI control to an OBS action, just click in the text box for the control you wish to set and press a button or twiddle a knob on your MIDI device. For the controls in section one, you probably want the Toggle options, rather than assigning different on/off keys. In section two the scenes are expecting a button press to switch between them, and in section three the audio inputs have two options one for a push button to toggle mute the sound and another to adjust the volume. Click _Save and Close_, you will be taken to the main controller screen, this is where the program operates OBS via the websocket:

<img width="545" alt="midiObsWS_main" src="https://user-images.githubusercontent.com/1898711/205467030-e01141aa-e4a7-45a5-83ec-ea2cdcf3f62d.png">

Once fully configured, starting the program again will be take you directly to the contoller page, and on startup the midi device will be set to the values currently in OBS, button LED's will be set on where things are active, and indicators for the volume knobs set appropriatley. 

You can now press buttons and twiddle knobs. Enjoy.

## Setting an Input Kind
The _midiObsConfig.json_ contains a list of input devices, inputKinds. This is so the software can distinguish between audio and video hardware, for example:
```
"audio": [
    {
        "name": "wasapi_input_capture",
        "display": "wasapi input capture"
    },
```
I created this list by running **python midiObs.py --inputkinds** on various platforms; Windows 11, Debian Linux, macOS Ventura and updating the config file.

If your setup is not already on the list, then you will need to add it to the _midiObsConfig.json_ file in the appropriate section.

## Known Issues
- The password being stored in plain text.
- If you reconfigure OBS this won't pick up the change. You will need to delete the midiObsData.json file and configure again from start.
- No checks are mode for duplicate numbers - the same MIDI control can be attached to multiple controls.
- The GUI is a bit old fashioned, this is an attempt to have an interface that will work on multiple platforms and be reasonably simple.

## Links
- https://obsproject.com/
- https://github.com/obsproject/obs-websocket - this is now included in OBS, v28.0.0 onwards
- https://github.com/IRLToolkit/simpleobsws/tree/master


## Update Log
**Version 0.4 beta - December 2022**

Written for Python 3.9, use OBS v28 or higher as this comes with obs-websockets 5 included.

I've tested this in a Windows 11 PC. It should work with a Mac but I had problems getting tkinter installed, it should also work with Liunx distributions that have OBS 28 installed. 
