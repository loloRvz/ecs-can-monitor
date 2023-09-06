from canlib import canlib
import sys

# print(f"Found {num_channels} channels")

# for ch in range(num_channels):
#     chd = canlib.ChannelData(ch)
#     print(f"{ch}. {chd.channel_name} ({chd.card_upc_no.product()}:{chd.card_serial_no}/{chd.chan_no_on_card})")

# Open receiving channel
ch_rx = canlib.openChannel(channel=0)
ch_rx.setBusParams(canlib.canBITRATE_500K)


ch_rx.busOn()

while True:
    # Read messages
    frame = ch_rx.read(timeout=1000)

    # Keep messages ID ending in '0' (10,20,..,110). They are to VirtualWall_A_tx message IDs
    if frame.id%10 == 0:
        print(frame)
        print("ID: ",frame.id)
        print("DLC: ",frame.dlc)
        print("Angle: ",frame.data.decode('ascii',errors='replace'))

# except KeyboardInterrupt:
#     ch.busOff()


# ch_a = canlib.openChannel(channel=0)
# ch_b = canlib.openChannel(channel=1)

# ch_a.setBusParams(canlib.canBITRATE_250K)
# ch_b.setBusParams(canlib.canBITRATE_250K)

# ch_a.busOn()
# ch_b.busOn()

# frame = Frame(id_=200, data=[72, 69, 76, 76, 79, 33], flags=canlib.MessageFlag.STD )
# ch_a.write(frame)

# msg = ch_b.read(timeout=500)
# print(msg)

# ch_a.busOff()
# ch_b.busOff()

# ch_a.close()
# ch_b.close()


