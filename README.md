# midiObsWS
An interface to allow OBS to be controlled by a MIDI device via obs-Websockets.

This system has been written to provide basic functionality; scene switching, volume control and allow operation of the main controls such as recording, streaming and the virtual camera.

**Version 0.4 beta - December 2022**

Written in Python 3.9, use OBS v28 or higher as this comes with obs-websockets 5 included.

I've tested this in a Windows 11 PC. It should work with a Mac but I had problems getting tkinter installed, it should also work with Liunx distributions that have OBS 28 installed. The MIDI device I've used is a Behringer X-Touch Mini.

## Installation
### Windows (with python 3.9 already installed)
```
python -m pip install mido python-rtmidi websocket-client argparse simpleobsws pysimplegui
```
### Apple Mac (macOS Ventura)
Getting it working proved to be more difficult than it should have been, I suspect milage may vary for others.
```
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
## Use
Start OBS and configure your video, audio and scenes to how you like. Connect your MIDI device to a USB port.

In OBS setup the Websocket - Tools > obs-websocket Settings. Enable authentication and generate a password. Click the Show Connect Info button for the login infomration, if you are running midiObsWS on the same computer as OBS _localhost_ can be used as the Server IP.

Start midiObsWS with **python midiObsWS.py** When first run, the system will ask you for the obs-websocket server settings and the midi device you will be using as a controller, OBS shoud be running and the misdi device connected:

<img width="546" alt="midiObsWS_host" src="https://user-images.githubusercontent.com/1898711/205518626-77c082fc-8efd-46a9-9bd2-68c4f782189b.png">

You can test the OBS connection by clicking the test button, on success it'll say OK and give you the version numbers of OBS and obs-websockets.

Enter the details and click Save and Close, the password is stored in plain text in the _midiObsConfig.json_ file, the system then connects to OBS to obtain the configuration and you will then be presented with the setup page, otherwise if there is an error describing the problem, if it is a password error, start again with **python midiObsWS.py --sethost**.

<img width="725" alt="midiObsWS_setup" src="https://user-images.githubusercontent.com/1898711/205466660-bcf82571-3b88-43f0-ae47-b2d114d2bf90.png">

To attach a MIDI control to an OBS action, just click in the text box and press a button or twiddle a knob on your MIDI device. For the controls in section one, you probably want the Toggle options, rather than assigning different on/off keys, the scenes are expecting a button press, ans the audio inputs have two options one for a push button to mute the sound and another to ajdust the volume.

Click Save and Close, you will be taken to the main controller screen, this is where the program operates OBS via the websocket:

<img width="545" alt="midiObsWS_main" src="https://user-images.githubusercontent.com/1898711/205467030-e01141aa-e4a7-45a5-83ec-ea2cdcf3f62d.png">

Once fully configured, starting the program again will be take you directly to the contoller page, and on startup the midi device will be set to the values currently in OBS, button LED's will be set on where things are active, and indicators for the volume knobs set appropriatley.

You can now press buttons and twiddle knobs. Enjoy.

## Known Issues
- The password being stored in plain text.
- If you reconfigure OBS this won't pick up the change. You will need to delete the midiObsData.json file and configure again from start.
- No checks are mode for duplicate numbers - the same MIDI control can be attached to multiple controls.
- The GUI is a bit old fashioned, this is an attempt to have an interface that will work on multiple platforms and be reasonably simple.

## Links
- https://obsproject.com/
- https://github.com/obsproject/obs-websocket - this is now included in OBS, v28.0.0 onwards
- https://github.com/IRLToolkit/simpleobsws/tree/master
