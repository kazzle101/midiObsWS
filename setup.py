from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name="midiObsWS",
    version="1.0.10",
    description="An interface to allow OBS to be controlled by a MIDI device via obs-Websockets.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kazzle101/midiObsWS",
    author="Karl",
    author_email="",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    packages=["midiObsWS"],
    include_package_data=True,
    install_requires=[
        "mido", "python-rtmidi", "websocket-client", "argparse", 
        "simpleobsws", "FreeSimpleGUI"
    ],
    entry_points={"console_scripts": ["midiObsWS=midiObsWS.__main__:main"]},
)