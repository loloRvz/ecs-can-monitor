#!/usr/bin/python

import curses
import sys
import threading
import traceback
import struct
import time

import can

should_redraw = threading.Event()
stop_reading = threading.Event()

can_messages = {}
can_messages_lock = threading.Lock()

thread_exception = None
g_stdscr = None

BLACKLIST = []

STATIONBASEID = 200
VWPARTNERID = 30

_torque = 0

class ClearInterrupt():
    def __init__(self, period):
        self.next_t = time.time()
        self.done=False
        self.period = period
        self._run()

    def _run(self):
        # Clear can messages array
        with can_messages_lock:
            can_messages.clear()
        should_redraw.set()

        self.next_t+=self.period
        if not self.done:
            threading.Timer( self.next_t - time.time(), self._run).start()
    
    def stop(self):
        self.done=True

class TxTorqueInterrupt():
    def __init__(self, period, tx_bus):
        self.next_t = time.time()
        self.done=False
        self.period = period
        self.tx_bus = tx_bus
        self._run()

    def _run(self):
        send_msg_bytearray = bytearray(struct.pack("f", _torque))  
        send_msg_bytearray.reverse()
        send_msg = can.Message(arbitration_id=STATIONBASEID+1, data=send_msg_bytearray, is_extended_id=False)
        self.tx_bus.send(send_msg)
        
        self.next_t+=self.period
        if not self.done:
            threading.Timer( self.next_t - time.time(), self._run).start()
    
    def stop(self):
        self.done=True

def bus_run_loop(rx_bus,tx_bus):
    """Background thread for serial reading."""
    try:
        while not stop_reading.is_set():
            msg = rx_bus.recv(0.2)
            if msg:
                id, dlc, data = msg.arbitration_id, msg.dlc, msg.data

                if id in BLACKLIST:
                    continue

                with can_messages_lock:
                    can_messages[id] = data
                    should_redraw.set()   

                if id == VWPARTNERID:
                    msg_bytearray = [byte for byte in data]
                    msg_bytearray.reverse()
                    angle = 0
                    if len(msg_bytearray) == 4:
                        angle = struct.unpack('f', bytearray(msg_bytearray))[0]
                    
                    global _torque
                    if angle < 0:
                        _torque = -500*angle
                    else:
                        _torque = 0
                
        stop_reading.wait()

    except:
        if not stop_reading.is_set():
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

            padding = 5
            id_width = 5
            bytes_width = 25
            float_width = 10
            active_width = 10

            id_column_start = padding
            bytes_column_start = id_column_start + id_width + padding 
            float_column_start = bytes_column_start + bytes_width + padding
            active_column_start = float_column_start + float_width + padding

            # Compute row/column counts according to the window size and borders
            row_start = 3
            lines_per_column = max_y - (1 + row_start)

            # Setting up column headers
            win.addstr(1, id_column_start, 'ID'.rjust(id_width))
            win.addstr(1, bytes_column_start, 'Bytes'.ljust(bytes_width))
            win.addstr(1, float_column_start, 'Float'.rjust(float_width))

            row = row_start 

            # Don't read can_messages while being written to in serial thread
            with can_messages_lock:
                for frame_id in sorted(list(can_messages)):
                    msg = can_messages[frame_id]

                    # convert the bytes array to an hex string (separated by spaces)
                    msg_bytes = ' '.join('%02X' % byte for byte in msg)

                    # convert the bytes array to float
                    msg_bytearray = [byte for byte in msg]
                    msg_bytearray.reverse()
                    if len(msg_bytearray) == 4:
                        msg_float = struct.unpack('f', bytearray(msg_bytearray))[0]
                    else:
                        msg_float = 0

                    # Print frame ID
                    win.addstr(row, id_column_start, str(frame_id).rjust(id_width))
                    # Print frame bytes
                    win.addstr(row, bytes_column_start, msg_bytes.ljust(bytes_width))
                    # Print frame in float
                    win.addstr(row, float_column_start, f'{msg_float:5.2f}'.rjust(float_width))

                    row = row + 1
                    if row >= lines_per_column + row_start:
                        row = row_start

            # Fill rest of window with nothing
            while row < max_y-2:
                win.addstr(row, id_column_start, "".rjust(70))
                row+=1

            # Add quit message
            win.addstr(max_y-2, 2, "Press 'q' to quit")

            win.refresh()
            should_redraw.clear()

        c = stdscr.getch()
        if c == ord('q') or not bus_thread.is_alive():
            break
        elif c == curses.KEY_RESIZE:
            win = init_window(stdscr)

if __name__ == '__main__':

    rx_bus_device = None
    rx_bus_thread = None

    try:
        # Start Bus interfaces
        rx_bus = can.interface.Bus(channel='0', bitrate=500000, bustype='kvaser')
        tx_bus = can.interface.Bus(channel='1', bitrate=500000, bustype='kvaser')

        # Start the bus reading background thread
        rx_bus_thread = threading.Thread(target=bus_run_loop, args=(rx_bus,tx_bus))
        rx_bus_thread.start()

        # Clear old messages every 300ms
        clear_isr=ClearInterrupt(period = 0.3)

        tx_isr = TxTorqueInterrupt(period = 0.001, tx_bus = tx_bus)

        # Make sure to draw the UI the first time even if there is no data
        should_redraw.set()

        # Start the main loop
        curses.wrapper(main, rx_bus_thread)

    finally:
        # Cleanly stop bus thread before exiting
        if rx_bus_thread:
            stop_reading.set()

            rx_bus_thread.join()

            clear_isr.stop()
            tx_isr.stop()

            # If the thread returned an exception, print it
            if thread_exception:
                traceback.print_exception(*thread_exception)
                sys.stderr.flush()
