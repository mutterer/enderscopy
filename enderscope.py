import glob
import sys
from time import sleep

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from ipywidgets import widgets, Button, Layout, GridspecLayout, Output
from IPython.display import display

import serial


G_CODES = {
    'absolute': 'G90',
    'relative': 'G91',
    'homing': 'G28',
    'finish': 'M400',
    'current_position': 'M114'
}
DIRECTION_PREFIXES = {
    'north': 'Y',
    'south': 'Y-',
    'east': 'X',
    'west': 'X-',
    'up': 'Z',
    'down': 'Z-'
}



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
        if not code.endswith('\n'):
            code += '\n'
        self.serial.write(bytes(code, 'utf-8'))

    @staticmethod
    def serial_ports():  # TODO: check if this should be a function or a static method
        """
        Lists serial port names (from: https://stackoverflow.com/a/14224477)
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


class Stage(SerialDevice):
    """This is the 3 axis stage that moves the sample"""

    def __init__(self, port, baud_rate, homing=False, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)
        if homing:
            self.home()
        
    def write_code(self, code, check_ok=True, debug=False):
        super().write_code(code)
        response = self.serial.readline().decode('utf-8')
        if check_ok:
            while not response.startswith('ok'):
                if debug:
                    print(response.strip('\n'))
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
        :param bool debug:
        :return:
        """
        self.set_absolute()
        if z is None:
            code = f'G0 X {x} Y {y}'
        else:
            code = f'G0 X {x} Y {y} Z {z}'
        self.write_code(code, debug=debug)

    def move_position(self, p, debug=False):
        """
        Moves the stage to the given position

        :param p: position
        :param bool debug:
        :return:
        """
        if p is not None:
            self.move_absolute(*p, debug=debug)
            
    def move_relative(self, x, y, z=None, debug=False):
        """
        Moves the stage by given mm distance

        :param x:
        :param y:
        :param z:
        :param bool debug:
        :return:
        """
        self.set_relative(debug=debug)
        if z is None:
            code = f'G0 X {x} Y {y}'
        else:
            code = f'G0 X {x} Y {y} Z {z}'
        if debug:
            print(code)
        self.write_code(code, debug=debug)

    def move_towards(self, direction, distance, debug=False):
        """
        Moves the stage in the given direction

        :param direction:
        :param distance:
        :param bool debug:
        :return:
        """
        self.set_relative()
        code = f'G0 {DIRECTION_PREFIXES[direction.lower()]}{distance}'
        self.write_code(code, debug=debug)

    def move_axis(self, axis, distance, debug=False):
        """
        Moves the stage along the given axis

        :param axis:
        :param distance:
        :param bool debug:
        :return:
        """
        self.set_relative()
        code = f'G0 {axis.upper()}{distance}'
        self.write_code(code, debug=debug)

    def get_position(self, as_dict=False, debug=False):
        """
        Gets the current position of the stage

        :param bool as_dict:
        :param bool debug:
        :return:
        """
        self.flush_serial_buffer()
        response = self.write_code(G_CODES['current_position'],
                                   check_ok=False)
        if debug:
            print(response)
        ok = self.serial.readline()
        if not ok.decode('utf-8').startswith('ok'):
            print('Error reading stage position')
            return
        position = response.split(' Count')[0]
        parts = position.split()
        positions = {part.split(':')[0]: float(part.split(':')[1]) for part in parts}
        if not as_dict:
            order = 'XYZ'
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

class Panel:
    def __init__(self, stage):
        self.recording = False
        self.recorded_positions = [None] * 6
        self.stage = stage
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
        grid[1, 3] = self.create_button('P1', 'lightgrey')
        grid[1, 4] = self.create_button('P2', 'lightgrey')
        grid[2, 3] = self.create_button('P3', 'lightgrey')
        grid[2, 4] = self.create_button('P4', 'lightgrey')
        grid[3, 3] = self.create_button('P5', 'lightgrey')
        grid[3, 4] = self.create_button('P6', 'lightgrey')
        grid[4, 3] = self.create_button('Save', 'pink')
        grid[4, 4] = self.create_button('Open', 'pink')
        self.xys = 5
        self.zs = 1
        self.grid = grid
        self.output = Output()
        display (grid, self.output)

    def create_button(self, description, btn_color):
        b = Button(description=description, style=dict(button_color=btn_color), layout=Layout(height='auto', width='auto'))
        b.on_click(self.on_button_clicked)
        return b

    def set_steps(self, xys, zs):
        self.xys = xys
        self.zs = zs
        
    def checkbox_changed(self, element):
        if element['new']:
            self.recording = True
            element['owner'].description = 'Recording...'
        else:
            self.recording = False
            element['owner'].description = 'Record'
        
    def on_button_clicked(self, btn):
        if btn.description == 'Home':
            with self.output:
                self.output.clear_output()
                print('homing...')
            self.stage.home()
        elif btn.description.startswith('P'):
            m = int(btn.description[-1]) - 1
            if self.recording:
                self.recorded_positions[m] = self.stage.get_position()
                btn.style.button_color= '#ffd6b9'
            elif self.recorded_positions[m] is not None:
                self.stage.move_position(self.recorded_positions[m])
        else:
            self.stage.move_towards(btn.description, 5)
        with self.output:
            self.output.clear_output()
            print('moving...')
            self.stage.finish_moves()
            self.output.clear_output()
            print(self.stage.get_position(as_dict=True))
            

class EnderLights(SerialDevice):
    """
    An illumination device built from an Arduino board and a neopixels RGB leds ring
    """

    def __init__(self, port, baud_rate=9600, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)
        
    def write_code(self, code, check_ok=True, debug=False):
        super().write_code(code)
        response = self.serial.readline().decode('utf-8')
        if not response.startswith('ok'):
            print(response.strip('\n'))
        return response

    def shutter(self, s):  # TODO: replace name
        """Opens or closes a virtual shutter"""
        code = 'S1' if s else 'S0'
        self.write_code(code)

    def mode(self, value):
        """Switches modes"""
        code = f'M{value}'
        self.write_code(code)

    def parameter(self, value):
        """Switches modes"""
        code = f'P{value}'
        self.write_code(code)

    def red(self, value):
        """Sets red level"""
        code = f'R{value}'
        self.write_code(code)

    def green(self, value):
        """Sets green level"""
        code = f'G{value}'
        self.write_code(code)

    def blue(self, value):
        """Sets green level"""
        code = f'B{value}'
        self.write_code(code)

    def color(self, r, g, b):
        """Sets RGB levels"""
        self.red(r)
        self.green(g)
        self.blue(b)

    def reset(self):
        """Resets illuminator"""
        self.shutter(False)
        self.mode(0)
        self.write_code(f'MA65535\n')
        self.color(20,20,20)


class ScanPatterns:
    def plot_path(self, path=np.array([[0,0]]), labels=True, field=(10, 10), title='Path preview'):
        x = path[:, 0]
        y = path[:, 1]
        field = Rectangle((0, 0), field[0], field[1])
        rectangle = Rectangle((0, 0), 200, 190,
                          edgecolor='green', facecolor='#00ff0010', linewidth=1)
        plt.gca().add_patch(rectangle)
        plt.plot(x,y, marker='x')
        plt.axis('equal')
        ticks = np.arange(-50, 221, 25)
        plt.xticks(ticks)
        plt.yticks(ticks)
        plt.grid(linestyle='--', linewidth=0.7, alpha=0.7)
        plt.xlim(-10, 200)
        plt.ylim(-10, 200)
        plt.xlabel('x axis')
        plt.ylabel('y axis')
        plt.title(title)
        if labels:
            for idx, (x_pos, y_pos) in enumerate(zip(x, y)):
                plt.text(x_pos, y_pos, str(idx+1), fontsize=10, color='gray', ha='right', va='bottom')
                f = Rectangle((x_pos-field.get_width()/2,y_pos-field.get_height()/2),
                              field.get_width(), field.get_height(),
                              edgecolor='red', facecolor='none', linewidth=0.25
                             )
                plt.gca().add_patch(f)

    def raster(self, cols=4, rows=3):
        return np.array(list((x,y) for y in range(rows) for x in range(cols)))

    def snake(self, cols=4, rows=3):
        return np.array(
            list((x,y)
                 for y in range(rows)
                 for x in range((cols-1)*(y%2),cols-(cols+1)*(y%2),((y+1)%2)-1*((y%2)))
                ))

    def random(self, num_points=10, seed=1):
        x_min, x_max = 0, 180  # Range for x values
        y_min, y_max = 0, 180  # Range for y values
        np.random.seed(seed)
        return np.column_stack((
            np.random.uniform(x_min, x_max, num_points),
            np.random.uniform(y_min, y_max, num_points)))

    def spiral(self, num_points=50):
        directions = np.array([[1, 0], [0, 1], [-1, 0], [0, -1]])
        d = 0
        i = 1 
        p = np.array([0, 0])
        sp = np.array([p])
        while len(sp) < num_points:
            for j in range(i):
                p += directions[d]
                sp = np.append(sp,[p], axis=0)
            d = (d+1) % 4
            i += d%2 == 0
        return np.array(sp[:num_points])
