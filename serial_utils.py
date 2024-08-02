import glob
import sys
from time import sleep

import serial


def serial_ports():
    """ Lists serial port names
    		from: https://stackoverflow.com/a/14224477
        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = [f'COM{i + 1}' for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def open_port(com, port, speed):
    com.port = port
    com.baudrate = speed
    com.parity = serial.PARITY_NONE
    com.stopbits = serial.STOPBITS_ONE
    com.bytesize = serial.EIGHTBITS
    com.open()
    while not com.isOpen():
        sleep(0.1)


class SerialDevice:
    def __init__(self, port, baud_rate, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        self.serial = serial.Serial()
        self.serial.port = port

        self.serial.baudrate = baud_rate
        self.serial.parity = parity
        self.serial.stopbits = stop_bits
        self.serial.bytesize = byte_size

        self.serial.open()
        while not self.serial.isOpen():
            sleep(0.1)

    def flush_serial_buffer(self):
        while self.serial.in_waiting > 0:
            self.serial.read()

    def write_code(self, code):
        if not code.endswith("\n"):
            code += "\n"
        self.serial.write(bytes(code, "utf-8"))
