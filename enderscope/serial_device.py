"""Base class for physical/virtual serial-connected devices."""

from time import sleep

import serial

from ._virtual.device import VirtualMarlinDevice


class SerialDevice:
    """
    A generic class for serial devices
    It can be used to list available (functional) serial ports and to connect to a serial device
    It only implements the basic functionality of opening a serial port,
    writing to it and flushing the buffer
    """

    def __init__(self, port, baud_rate, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        self._virtual_device = None
        if isinstance(port, str) and port.lower() == 'virtual':
            # Create a virtual Marlin device and attach pyserial to it.
            self._virtual_device = VirtualMarlinDevice(baudrate=baud_rate)
            self.serial = self._virtual_device.serial
        else:
            self.serial = serial.Serial()
            self.serial.port = port
            self.serial.baudrate = baud_rate
            self.serial.parity = parity
            self.serial.stopbits = stop_bits
            self.serial.bytesize = byte_size
            self.serial.timeout = 1
            self.serial.write_timeout = 1
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
