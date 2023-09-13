# CAN bus monitor for Embbedded Control Systems course (151-0593-00)

This python script reads and displays live data from a CAN bus. It can also act as partner 'B', for the remote virtual wall assignment of Lab 8. This script should help the students test and debug their code.

This script is to be used with two [Kvaser Leaf Light v2](https://www.kvaser.com/product/kvaser-leaf-light-hs-v2/) usb dongles for the can interface.

Parts of this script is forked from https://github.com/alexandreblin/python-can-monitor.

## Install
- Install Kvaser's canlib linux drivers. Follow the instructions on this [link](https://www.kvaser.com/canlib-webhelp/section_install_linux.html).

- Install pip dependencies

        pip install -r requirements.txt

- Connect two *Kvaser Leaf Light v2* dongles, one for receiving and one for sending can messages.

- Check your drivers are installed correctly and recognise your dongles by running:

        python list_channels.py

    You should see the two dongles on channel 0 and 1

- Set the virtual wall parter A's id (VWPARTNERID) in 'can_monitor.py'. Your id is 120.

# Run
Launch the script:

    python monitor.py

Press 'q' at any time to exit.