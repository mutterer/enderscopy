import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO

import time
import serial
from serial_utils import SerialDevice
from ipywidgets import widgets, Button, Layout, ButtonStyle, GridspecLayout, Output
from IPython.display import display, Image

G_CODES = {
    'absolute': 'G90',
    'relative': 'G91',
    'homing': 'G28',
    'finish': 'M400',
    'current_position': 'M114'
}
DIRECTION_PREFIXES = {
    "north": "Y",
    "south": "Y-",
    "east": "X",
    "west": "X-",
    "up": "Z",
    "down": "Z-"
}

class Stage(SerialDevice):
    """
    This is the 3 axis stage that moves the sample
    """

    def __init__(self, port, baud_rate, homing=False, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)
        if homing==True:
            self.home()
        
    def write_code(self, code, check_ok=True, debug=False):
        super().write_code(code)
        response = self.serial.readline().decode('utf-8')
        if check_ok:
            while not response.startswith("ok"):
                if debug:
                    print (response.strip('\n'))
                response = self.serial.readline().decode('utf-8')
        if debug:
            print(code)        
        return response

    def move_absolute(self, x, y, z=None, debug=False):
        """
        Moves the stage to the given coordinates
        :param x:
        :param y:
        :param z:
        :return:
        """
        self.set_absolute()
        if z is None:
            code = f"G0 X {x} Y {y}"
        else:
            code = f"G0 X {x} Y {y} Z {z}"
        self.write_code(code, debug=debug)

    def move_position(self, p, debug=False):
        """
        Moves the stage to the given position
        :param p: position
        :return:
        """
        if p is not None:
            self.set_absolute()
            if len(p)<3 :
                x,y = p
                code = f"G0 X {x} Y {y}"
            else:
                x,y,z = p
                code = f"G0 X {x} Y {y} Z {z}"
            self.write_code(code, debug=debug)
            
    def move_relative(self, x, y, z=None, debug=False):
        """
        Moves the stage by given mm distance
        :param x:
        :param y:
        :param z:
        :return:
        """
        self.set_relative(debug=debug)
        if z is None:
            code = f"G0 X {x} Y {y}"
        else:
            code = f"G0 X {x} Y {y} Z {z}"
        if debug:
            print(code)
        self.write_code(code, debug=debug)

    def move_towards(self, direction, distance, debug=False):
        """
        Moves the stage in the given direction
        :param direction:
        :return:
        """
        self.set_relative()
        if direction.lower() in ('up', 'down'):
            code = f"G0 {DIRECTION_PREFIXES[direction.lower()]}{distance}"
        else:
            code = f"G0 {DIRECTION_PREFIXES[direction.lower()]}{distance}"
        self.write_code(code, debug=debug)

    def move_axis(self, axis, distance, debug=False):
        """
        Moves the stage along the given axis
        :param distance:
        :return:
        """
        self.set_relative()
        code = f"G0 {axis.upper()}{distance}"
        self.write_code(code, debug=debug)

    def get_position(self, dict=False, debug=False):
        self.flush_serial_buffer()
        response = self.write_code(G_CODES['current_position'],
                                   check_ok=False)
        if debug:
            print(response)
        ok = self.serial.readline()
        if not ok.decode('utf-8').startswith("ok"):
            print("Error reading stage position")
            return
        position = response.split(" Count")[0]
        parts = position.split()
        positions = {part.split(":")[0]: float(part.split(":")[1]) for part in parts}
        if dict==False:
            order = ['X','Y', 'Z']
            positions = tuple([positions[field] for field in order])
        return positions

    def home(self, debug=False):
        self.write_code(G_CODES['homing'], debug=debug)

    def finish_moves(self, debug=False):
        self.write_code(G_CODES['finish'], debug=debug)

    def set_relative(self, debug=False):
        self.write_code(G_CODES['relative'], debug=debug)

    def set_absolute(self, debug=False):
        self.write_code(G_CODES['absolute'], debug=debug)

class Panel():
    def create_button(self, description, bcolor):
        b = Button(description=description, style=dict(button_color=bcolor), layout=Layout(height='auto', width='auto'))
        b.on_click(self.on_button_clicked)
        return b

    def checkbox_changed(self,element):
        if element['new'] == True:
            self.recording = True
            element['owner'].description = 'Recording...'
        else:
            self.recording = False
            element['owner'].description = 'Record'
        
    def on_button_clicked(self, b):
        if b.description == 'Home':
            with self.output:
                self.output.clear_output()
                print ("homing...")
            self.s.home()
        elif b.description.startswith('P'):
            m = int(b.description[-1])-1
            if self.recording == True:
                self.recorded_positions[m] = self.s.get_position()
                b.style.button_color="#ffd6b9"
            elif self.recorded_positions[m] is not None:
                self.s.move_position(self.recorded_positions[m])
        else:
            self.s.move_towards(b.description,5)
        with self.output:
            self.output.clear_output()
            print ("moving...")
            self.s.finish_moves()
            self.output.clear_output()
            print (self.s.get_position(dict=True))
            
    def __init__(self, s):
        self.recording = False
        self.recorded_positions = [None for i in range(6)] 
        self.s = s
        grid = GridspecLayout(5, 12, height='auto', width='auto')
        grid[0:2, 0] = self.create_button('Up', 'paleturquoise')
        grid[2:, 0] = self.create_button('Down', 'paleturquoise')
        grid[0, 1:3] = self.create_button('North', 'palegreen')
        grid[2, 1:3] = self.create_button('South', 'palegreen')
        grid[1, 1] = self.create_button('West', 'palegreen')
        grid[1, 2] = self.create_button('East', 'palegreen')
        grid[3:, 1:3] = self.create_button('Home', 'lightyellow')
        record_cb = widgets.Checkbox(value=False, description='Record', indent=False, layout=Layout(width='100px'))
        record_cb.observe(self.checkbox_changed, names='value')
        grid[0, 3:5] = record_cb
        grid[1,3] = self.create_button('P1', 'lightgrey')
        grid[1,4] = self.create_button('P2', 'lightgrey')
        grid[2,3] = self.create_button('P3', 'lightgrey')
        grid[2,4] = self.create_button('P4', 'lightgrey')
        grid[3,3] = self.create_button('P5', 'lightgrey')
        grid[3,4] = self.create_button('P6', 'lightgrey')
        grid[4,3] = self.create_button('Save', 'pink')
        grid[4,4] = self.create_button('Open', 'pink')
        self.grid = grid
        self.output = Output()
        display (grid, self.output)

# def read_g_code(fname):
#     fpath = os.path.join(PROJECT_PATH, fname)
#     with open(fpath, "r") as text_file:
#         data = text_file.read()
#     return data

class Enderlights(SerialDevice):
    """
    An illumination device built from an Arduino board and a neopixels RGB leds ring
    """

    def __init__(self, port, baud_rate=9600, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)
        
    def write_code(self, code, check_ok=True, debug=False):
        super().write_code(code)
        response = self.serial.readline().decode('utf-8')
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
