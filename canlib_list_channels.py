from canlib import canlib


num_channels = canlib.getNumberOfChannels()
print("Found %d channels" % num_channels)

for channel in range(0, num_channels):

    chdata = canlib.ChannelData(channel)

    print("%d. %s (%s / %s)" % (
        channel,
        chdata.channel_name,
        chdata.card_upc_no,
        chdata.card_serial_no)
    )