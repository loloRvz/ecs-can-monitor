# CAN bus monitor for Embbedded Control Systems course (151-0593-00)

This repo contains:
- A script which reads and displays live data from a CAN bus
- A script which acts as a universal B user, for the remote virtual wall assignment of Lab 8

These scripts should help the students test and debug their code.

## Usage
Install the linux drivers, follow the instructions on this [link](https://www.kvaser.com/canlib-webhelp/section_install_linux.html)

Install pip dependencies

    pip install -r requirements.txt

Launch the script

    python

Press Q at any time to exit the script.

Sending a special frame (right now, `777#0707070707070707`) will reset the screen
Adding arbitration ids to BLACKLIST or WHITELIST can allow you to select what
you want and don't want to see when there are too many messages.

## Example

    ./canmonitor.py vcan0

![Screenshot](http://i.imgur.com/1nqCQKz.png)


