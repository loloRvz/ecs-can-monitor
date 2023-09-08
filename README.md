# CAN bus monitor for Embbedded Control Systems course (151-0593-00)

This repo contains:
- A script which reads and displays live data from a CAN bus
- A script which acts as a universal B user, for the remote virtual wall assignment of Lab 8

These scripts should help the students test and debug their code.

This is a fork from https://github.com/alexandreblin/python-can-monitor. The scripts use 

## Usage
- Install the linux drivers, follow the instructions on this [link](https://www.kvaser.com/canlib-webhelp/section_install_linux.html).

- Install pip dependencies

    pip install -r requirements.txt

- Connect two 'Kvaser Leaf Light v2' dongles, one for receiving and one for sending messages.

- Check your drivers are installed and recognising your dongles correctly by running:
    python list_channels.py

You should see the two dongles on channel 0 and 1

- Set the virtual wall parter A's id (VWPARTNERID) in 'can_monitor.py'. Your id is 120.

- Launch the script
    python monitor.py

Press 'q' at any time to exit the script.



