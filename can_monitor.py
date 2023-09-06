#!/usr/bin/python

import argparse
import curses
import sys
import threading
import traceback

import can

should_redraw = threading.Event()
stop_bus = threading.Event()

can_messages = {}
can_messages_lock = threading.Lock()

thread_exception = None
g_stdscr = None

CLEAR_DICT_ARB_ID = 0x777
CLEAR_DICT_DATA_LEN = 8
CLEAR_DICT_DATA = [7, 7, 7, 7, 7, 7, 7, 7]
BLACKLIST = []
WHITELIST = []

def data_is_special_clear_frame(arb_id, data_len, data):
    if arb_id != CLEAR_DICT_ARB_ID:
        return False

    if data_len != CLEAR_DICT_DATA_LEN:
        return False

    for i in range(CLEAR_DICT_DATA_LEN):
        if CLEAR_DICT_DATA[i] != data[i]:
            return False

    return True

def read_bus(bus_device):
    """Read data from `bus_device` until the next newline character."""
    message = bus.recv(0.2)
    while True:
        if message:
            break
        message = bus.recv(0.2)

    try:
        string = "{}:ID={}:LEN={}".format("RX", message.arbitration_id, message.dlc)
        for x in range(message.dlc):
            string += ":{:02x}".format(message.data[x])

    except Exception as e:
        print(e)
    return string


def bus_run_loop(bus_device):
    """Background thread for serial reading."""
    try:
        while not stop_bus.is_set():
            line = read_bus(bus_device)

            # Sample frame from Arduino: FRAME:ID=246:LEN=8:8E:62:1C:F6:1E:63:63:20
            # Split it into an array (e.g. ['FRAME', 'ID=246', 'LEN=8', '8E', '62', '1C', 'F6', '1E', '63', '63', '20'])
            frame = line.split(':')

            try:
                frame_id = int(frame[1][3:])  # get the ID from the 'ID=246' string

                if WHITELIST != [] and frame_id != CLEAR_DICT_ARB_ID and frame_id not in WHITELIST:
                    continue
                elif BLACKLIST != [] and frame_id != CLEAR_DICT_ARB_ID and frame_id in BLACKLIST:
                    continue

                frame_length = int(frame[2][4:])  # get the length from the 'LEN=8' string

                data = [int(byte, 16) for byte in frame[3:]]  # convert the hex strings array to an integer array
                data = [byte for byte in data if byte >= 0 and byte <= 255]  # sanity check


                if len(data) != frame_length:
                    # Wrong frame length or invalid data
                    continue

                # Clear the dictionnary if a special message is received
                if data_is_special_clear_frame(frame_id, frame_length, data):
                    with can_messages_lock:
                        global can_messages
                        can_messages = {}
                        should_redraw.set()
                        win = init_window(g_stdscr)
                        continue

                # Add the frame to the can_messages dict and tell the main thread to refresh its content
                with can_messages_lock:
                    can_messages[frame_id] = data
                    should_redraw.set()
            except Exception as e:
                print(e)
                # Invalid frame
                continue
    except:
        if not stop_bus.is_set():
            # Only log exception if we were not going to stop the thread
            # When quitting, the main thread calls close() on the serial device
            # and read() may throw an exception. We don't want to display it as
            # we're stopping the script anyway
            global thread_exception
            thread_exception = sys.exc_info()


def init_window(stdscr):
    """Init a window filling the entire screen with a border around it."""
    stdscr.clear()
    stdscr.refresh()

    max_y, max_x = stdscr.getmaxyx()
    root_window = stdscr.derwin(max_y, max_x, 0, 0)

    root_window.box()

    return root_window


def main(stdscr, bus_thread):
    """Main function displaying the UI."""
    # Don't print typed character
    curses.noecho()
    curses.cbreak()

    global g_stdscr
    g_stdscr = stdscr
    # Set getch() to non-blocking
    stdscr.nodelay(True)

    win = init_window(stdscr)

    while True:
        # should_redraw is set by the serial thread when new data is available
        if should_redraw.is_set():
            max_y, max_x = win.getmaxyx()

            column_width = 70
            id_column_start = 2
            id_padding = 14
            bytes_column_start = 15 + id_padding
            text_column_start = 45 + id_padding

            # Compute row/column counts according to the window size and borders
            row_start = 3
            lines_per_column = max_y - (1 + row_start)
            num_columns = int((max_x - 2) / column_width)

            # Setting up column headers
            for i in range(0, num_columns):
                win.addstr(1, id_column_start + i * column_width, 'ID')
                win.addstr(1, bytes_column_start + i * column_width, 'Bytes')
                win.addstr(1, text_column_start + i * column_width, 'Text')

            win.addstr(3, id_column_start, "Press 'q' to quit")

            row = row_start + 2  # The first column starts a bit lower to make space for the 'press q to quit message'
            current_column = 0

            # Make sure we don't read the can_messages dict while it's being written to in the serial thread
            with can_messages_lock:
                for frame_id in sorted(can_messages.keys()):
                    msg = can_messages[frame_id]

                    # convert the bytes array to an hex string (separated by spaces)
                    msg_bytes = ' '.join('%02X' % byte for byte in msg)

                    # try to make an ASCII representation of the bytes
                    # nonprintable characters are replaced by '?'
                    # and spaces are replaced by '.'
                    msg_str = ''
                    for byte in msg:
                        char = chr(byte)
                        if char == '\0':
                            msg_str = msg_str + '.'
                        elif ord(char) < 32 or ord(char) > 126:
                            msg_str = msg_str + '?'
                        else:
                            msg_str = msg_str + char

                    # print frame ID in decimal and hex
                    #win.addstr(row, id_column_start + current_column * column_width, '%s' % str(frame_id).ljust(8))
                    win.addstr(row, id_column_start + id_padding + current_column * column_width, '{:08x}'.format(frame_id))

                    # print frame bytes
                    win.addstr(row, bytes_column_start + current_column * column_width, msg_bytes.ljust(23))

                    # print frame text
                    win.addstr(row, text_column_start + current_column * column_width, msg_str.ljust(8))

                    row = row + 1

                    if row >= lines_per_column + row_start:
                        # column full, switch to the next one
                        row = row_start
                        current_column = current_column + 1

                        if current_column >= num_columns:
                            break

            win.refresh()

            should_redraw.clear()

        c = stdscr.getch()
        if c == ord('q') or not bus_thread.is_alive():
            break
        elif c == curses.KEY_RESIZE:
            win = init_window(stdscr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process CAN data from a socket-can device.')

    bus_device = None
    bus_thread = None

    try:
        bus = can.interface.Bus(channel='0', bitrate=500000, bustype='kvaser')

        # Start the bus reading background thread
        bus_thread = threading.Thread(target=bus_run_loop, args=(bus,))
        bus_thread.start()

        # Make sure to draw the UI the first time even if there is no data
        should_redraw.set()

        # Start the main loop
        curses.wrapper(main, bus_thread)

    finally:
        # Cleanly stop bus thread before exiting
        if bus_thread:
            stop_bus.set()

            bus_thread.join()

            # If the thread returned an exception, print it
            if thread_exception:
                traceback.print_exception(*thread_exception)
                sys.stderr.flush()
