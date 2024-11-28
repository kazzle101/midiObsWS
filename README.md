# midiObsWS
An interface to allow OBS to be controlled by a MIDI device via obs-Websockets.

This system has been written to provide basic functionality; scene switching, volume control and allow operation of the main controls such as recording, streaming and the virtual camera. The MIDI device I've used is a Behringer X-Touch Mini.

## Update November 2024
**Version 0.10 beta**
- Updated to use a SQLite database rather than using JSON files - this simplifies a lot of things, current users will need to reconfigure.
- Fixed a bug that prevented removal of a previously set input on the setup screen.
- Added ability to play Media Sources (subscribe button type video animations, tested with .mp4 and animated .gif files).
- Replaced pysimplegui with [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI) to keep everything open source.

## Update November 2023
**Version 0.8 beta**
Update so the LEDs on the controller show the selected scene correctly, now only the LED for the selected scene is lit. Also have the LEDs show according to the current settings in OBS on startup.

## Installation
Connect your MIDI input device and start and configure OBS before you launch midiObsWS otherwise it will just say you need to connect a MIDI device and Start OBS then exit.

To configure OBS go to - Tools > obs-websocket Settings, enable Websocket server and generate a password, and click the Show Connect Info button for the login information.

### Windows Executable
A Windows Standalone executable is now incuded in the dist folder, copy onto your PC somewhere suitable and double-click it. [DOWNLOAD HERE](https://github.com/kazzle101/midiObsWS/raw/main/dist/midiObsWS.exe)

The executable was created with PyInstaller using:
```
python -m PyInstaller '.\midiObs.py' --name midiObsWS -F 
```

## Manual Installation
### Windows (with python 3.9+ already installed)

Install prython from: https://www.python.org/downloads/ 
You probably want the Windows Installer (64-bit)

During install tick add Python to the path, once installed you may need to reboot, check that you have the right version at the command prompt with: 
```
PS c:\> python --version
```
The computer I tested on had a couple of older versions of python and I had to remove these to have the correct/expected version show.

You will probably need to update pip: python.exe -m pip install --upgrade pip
Install the dependancies, download midiObsWS to your desired location and run program:
```
pip install FreeSimpleGUI mido simpleobsws python-rtmidi 
pip install websocket-client==1.6.1 websockets==11.0.3

git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
python midiObs.py
```
Note the version numbers on the websockets, using the latest versions gives an error when connecting to OBS: "BaseEventLoop.create_connection() got an unexpected keyword argument 'extra_headers'" 

### Linux Install (Debian / Ubuntu)
```
sudo apt install python3-pip
sudo apt install python3-rtmidi libportmidi-dev
sudo apt install python3-mido python3-websocket sqlite3 python3-tk 
sudo python -m pip install argparse simpleobsws FreeSimpleGUI --break-system-packages

git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
python midisObs.py
```

### Apple Mac (macOS Ventura)
Getting it working proved to be more difficult than it should have been, I suspect milage may vary for others. This is because GTK is no longer suppied with macOS.
```
git clone https://github.com/kazzle101/midiObsWS
cd midiObsWS
$ sudo python -m pip install mido python-rtmidi websocket-client argparse simpleobsws sqlite3 FreeSimpleGUI
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

## Use
Start OBS and configure your video, audio and scenes to how you like. Connect your MIDI device to a USB port.

In OBS setup the Websocket - Tools > obs-websocket Settings, enable Websocket server and generate a password, and click the Show Connect Info button for the login information. Now with OBS running, and the midi device connected, start midiObsWS with **python midiObs.py** When first run, the system will ask you for the obs-websocket server settings, if you are running midiObsWS on the same computer as OBS then _localhost_ can be used as the Server IP. Set the options for the midi device you will be using as a controller, Midi Out can be left unset if your device does not have illuminated feedback:

<img width="546" alt="midiObsWS_host" src="https://user-images.githubusercontent.com/1898711/205518626-77c082fc-8efd-46a9-9bd2-68c4f782189b.png">

The database is created: _midiOBSws.db_ this contains your OBS login details, a list of standard actions (toggle recording, etc) and a list of input kinds, these are used to distinguish between video and audio devices, there is also a table containing your mapping between the midi device and your actions, volume controls and scenes.

You can test and validate the OBS connection by clicking the _Test OBS Connection_ button, on success it'll say OK and give you the version numbers for OBS and obs-websockets.

Enter the details and click _Save and Close_, the password is stored in plain text in the database, the system then connects to OBS to obtain the configuration and you will then be presented with the setup page, otherwise an error describing the problem will be shown.

<img width="725" alt="midiObsWS_setup" src="https://user-images.githubusercontent.com/1898711/205466660-bcf82571-3b88-43f0-ae47-b2d114d2bf90.png">

To attach a MIDI control to an OBS action, just click in the text box for the control you wish to set and press a button or twiddle a knob on your MIDI device. For the controls in section one, you probably want the Toggle options, rather than assigning different on/off keys. In section two the scenes are expecting a button press to switch between them, and in section three the audio inputs have two options one for a push button to toggle mute the sound and another to adjust the volume. Click _Save and Close_, you will be taken to the main controller screen, this is where the program operates OBS via the websocket:

<img width="545" alt="midiObsWS_main" src="https://user-images.githubusercontent.com/1898711/205467030-e01141aa-e4a7-45a5-83ec-ea2cdcf3f62d.png">

Once fully configured, starting the program again will be take you directly to the contoller page, and on startup the midi device will be set to the values currently in OBS, button LED's will be set on where things are active, and indicators for the volume knobs set appropriatley. 

You can now press buttons and twiddle knobs. Enjoy.

## Identifying Video and Audio
To tell the difference between Video and Audio sources I have a list of default input types, these can be found in the _wsActions_ table in the database, or towards the end of _midiObsDatabase.py_ in the _createDefaultDatabase_ function. While OBS will supply a list of inputKinds it won't say if these are Video or audio, so these need to be manually set.

While I have included all that I could find from Windows, Mac and Linux, I expect some will be missing, and so your input will not appear on the setup screen. You can find your list of inputKinds from the command line:
```
python midiObs.py --inputkinds
```
Usng your favourate SQLite browser (https://sqlitebrowser.org/) you can add the missing input kind, for example:
```
INSERT INTO wsActions (io, showOnSetup, ioKind, name, display) VALUES ('input',1,'inputType' 'inputKind','inputName')
```
where:
- inputType: audio or video, this is for you to decide.
- inputKind: the name of the missing input, from your list.
- inputName: the same as the inputKind, but without the underscores.
The showOnSetup is used to display the input on the setup screen. This is normally 1 for audio and 0 for video, apart from ffmpeg_source as this is used for the Media Sources.

Leave a note in the issues, and I'll do an update.

## Known Issues
- The password being stored in plain text.
- If you reconfigure OBS this won't pick up the change, you will need to go back into the setup screen.
- No checks are mode for duplicate numbers - the same MIDI control can be attached to multiple controls.
- The GUI is a bit old fashioned, this is an attempt to have an interface that will work on multiple platforms and be reasonably simple.

## Links
- https://obsproject.com/
- https://github.com/obsproject/obs-websocket - this is now included in OBS, v28.0.0 onwards
- https://github.com/IRLToolkit/simpleobsws/tree/master

## Update Log
**Version 0.6 beta - August 2023**
Tested with Python 3.11

Many updates and bugfixes, mostly around creating default configuration files without having to know how the system works, also moving around functions to help make the code a bit more readable. Files have been moved around so pyinstaller installer can do its thing.

**Version 0.4 beta - December 2022**
Written for Python 3.9, use OBS v28 or higher as this comes with obs-websockets 5 included.

I've tested this in a Windows 11 PC. It should work with a Mac but I had problems getting tkinter installed, it should also work with Liunx distributions that have OBS 28 installed. 
