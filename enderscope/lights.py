"""Illumination device built from an Arduino board and a NeoPixel RGB LED ring."""

import serial

from .serial_device import SerialDevice


class Enderlights(SerialDevice):
    """
    An illumination device built from an Arduino board and a neopixels RGB leds ring
    """

    def __init__(self, port, baud_rate=9600, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)

    def write_code(self, code, check_ok=True, debug=False):
        super().write_code(code)
        response = self.serial.readline().decode('ascii', errors='replace')
        if not response.startswith("ok"):
            print (response.strip('\n'))
        return response

    def shutter(self, s):
        """
        Opens or closes a virtual shutter
        """
        code = f"S0"
        if s==True:
            code = f"S1"
        self.write_code(code)

    def mode(self, value):
        """
        switches modes
        """
        code = f"M{value}"
        self.write_code(code)

    def parameter(self, value):
        """
        switches modes
        """
        code = f"P{value}"
        self.write_code(code)

    def red(self, value):
        """
        sets red level
        """
        code = f"R{value}"
        self.write_code(code)

    def green(self, value):
        """
        sets green level
        """
        code = f"G{value}"
        self.write_code(code)

    def blue(self, value):
        """
        sets green level
        """
        code = f"B{value}"
        self.write_code(code)

    def color(self, r,g,b):
        """
        sets rgb levels
        """
        self.red(r)
        self.green(g)
        self.blue(b)

    def reset(self):
        """
        resets illuminator
        """
        self.shutter(False)
        self.mode(0)
        self.write_code(f"MA65535\n")
        self.color(20,20,20)
