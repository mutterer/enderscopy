import time
import serial
from serial_utils import SerialDevice
from ipywidgets import widgets, Button, Layout, ButtonStyle, GridspecLayout, Output
from IPython.display import display, Image

import numpy as np
import matplotlib.pyplot as plt
import numpy as np
import serial
from picamera2 import Picamera2
import sys
import time






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
    @staticmethod
    def snake(x_win, y_win, step_x, step_y):
        # Your existing code here
        a = []  # List of all x positions - empty list
        b = []  # List of all y positions
        x = 1
        y = 1  # Starting point of bed

        for j in range(y_win - 1):
            if j == 0:
                for i in range(x_win):  # Increment x step
                    if i % x_win != 0:
                        dx = step_x
                        dy = 0
                    elif i % x_win == 0:
                        dx = 0
                        dy = 0

                    x += dx
                    y += dy
                    a.append(x)
                    b.append(y)

            if j % 2 != 0:
                for i in range(x_win):
                    if i % x_win != 0:
                        dx = step_x
                        dy = 0
                    elif i % x_win == 0:
                        dx = 0
                        dy = step_y

                    x += dx
                    y += dy
                    a.append(x)
                    b.append(y)

            elif j % 2 == 0:
                for i in range(x_win):
                    if i % x_win != 0:
                        dx = -step_x
                        dy = 0
                    elif i % x_win == 0:
                        dx = 0
                        dy = step_y

                    x += dx
                    y += dy
                    a.append(x)
                    b.append(y)

        x_vals = np.array(a)
        y_vals = np.array(b)

        if (x_vals.max() > 235) | (y_vals.max() > 235):
            print('Too high values. x_max=235 and y_max=235.')
        else:
            return x_vals, y_vals

    @staticmethod
    def plot_snake_path(x, y):
        plt.plot(x, y, marker='x')
        plt.xlabel('X')
        plt.ylabel('y')
        plt.title('snake scan')
        plt.grid(True)
        plt.show()
        
    def wait_user_input(self):
        endTerm = '\n'
        tune = "M300 S440 P200" + endTerm
        self.write_code(tune)
        pause = "M25" + endTerm
        self.write_code(pause)
        print('Place sample')
        input("Press the Enter key to proceed")

        resume = "M108" + endTerm
        self.write_code(resume)

    def move_camera(self, picam2, folder, x, y):

        (x_origin, y_origin, z_origin) = self.get_position()

        for i in range(len(x)):
            #camera.resolution = (640, 480)
            xPos = x_origin + x[i]
            yPos = y_origin + y[i]
            self.move_absolute(xPos, yPos)
            time.sleep(0.5)
            picam2.capture_file(f"{folder}_{i}.tif")#We capture the camera photo and put it into the folder
            time.sleep(0.5)
            
        print("Finish!")
        
    def Snap(self):
       #save the current photo into the directory folder
        picam2.capture_file(f"{folder}_{i}.tif")
        print("snap")
        
    
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
            code = f"G0 X {x} Y {y} F {18000}"
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

    def checkbox_changed(self, element):
        if element['new'] == True:
            self.recording = True
            element['owner'].description = 'Recording...'
        else:
            self.recording = False
            element['owner'].description = 'Record'
            
    def on_button_clicked(self, b):
        """
        Gère les actions en fonction du bouton cliqué.
        """
        with self.output:
            self.output.clear_output()  # Nettoie la sortie avant chaque action
            try:
                if b.description == 'Home':
                    print("Homing...")
                    self.s.home()
                elif b.description.startswith('P') and b.description[1:].isdigit():
                    # Vérifie si le bouton est un bouton de type P (ex : P1, P2)
                    m = int(b.description[1:]) - 1  # Récupère le numéro du bouton P
                    if self.recording:
                        # Enregistre la position actuelle
                        self.recorded_positions[m] = self.s.get_position()
                        b.style.button_color = "#ffd6b9"
                        print(f"Position enregistrée pour P{m + 1}: {self.recorded_positions[m]}")
                    elif self.recorded_positions[m] is not None:
                        # Déplace le stage vers la position enregistrée
                        print(f"Déplacement vers la position enregistrée P{m + 1}")
                        self.s.move_position(self.recorded_positions[m])
                    else:
                        print(f"Aucune position enregistrée pour P{m + 1}")
                elif b.description == 'Snap':
                    print("Capture d'image...")
                    self.snap()
                elif b.description == 'Preview':
                    print("Activation du preview...")
                    self.start_preview()
                elif b.description == 'Stop Preview':
                    print("Arrêt du preview...")
                    self.stop_preview()
                else:
                    # Déplacement dans une direction (Up, Down, North, etc.)
                    print(f"Déplacement vers {b.description}...")
                    self.s.move_towards(b.description, 5)
                
                # Attend la fin des mouvements si nécessaire
                self.s.finish_moves()
                print("Position actuelle:", self.s.get_position(dict=True))
            except Exception as e:
                # Capture les erreurs et les affiche
                print(f"Erreur lors de l'exécution de l'action pour {b.description}: {e}")
         

    



    def snap(self):
        """
        Capture et enregistre l'image actuelle avec un horodatage.
        """
        import os  # Pour vérifier l'existence du dossier

        # Définir le dossier et vérifier s'il existe
        folder = "/home/rasp/Desktop/Manualmode/"
        if not os.path.exists(folder):
            os.makedirs(folder)  # Crée le dossier s'il n'existe pas

        # Générer un nom de fichier avec horodatage
        color = "Image_"
        filename = f"{folder}{color}{time.strftime('%H%M%S')}.jpg"

        try:
            # Capture de l'image avec la caméra
            self.picam2.capture_file(filename)
            print(f"Snap: Image saved as {filename}")
            with self.output:
                self.output.clear_output()
                print(f"Snap: Image saved as {filename}")
        except Exception as e:
            # Gestion des erreurs
            print(f"Erreur lors de la capture de l'image: {e}")
            with self.output:
                self.output.clear_output()
                print(f"Erreur lors de la capture de l'image: {e}")

    def start_preview(self):
        """
        Affiche un aperçu de la caméra pour régler la mise au point.
        """
        try:
            # Activer l'aperçu avec Picamera2
            self.picam2.start(show_preview=True)
            print("Preview started. Adjust focus if needed.")
            with self.output:
                self.output.clear_output()
                print("Preview started. Adjust focus if needed.")
        except Exception as e:
            print(f"Erreur lors du démarrage du preview : {e}")
            with self.output:
                self.output.clear_output()
                print(f"Erreur lors du démarrage du preview : {e}")


    def stop_preview(self):
        """
        Arrête l'aperçu de la caméra.
        """
        try:
            # Arrêter l'aperçu avec Picamera2
            self.picam2.stop_preview()
            print("Preview stopped.")
            with self.output:
                self.output.clear_output()
                print("Preview stopped.")
        except Exception as e:
            print(f"Erreur lors de l'arrêt du preview : {e}")
            with self.output:
                self.output.clear_output()
                print(f"Erreur lors de l'arrêt du preview : {e}")




    def __init__(self, s, picam2):
        self.recording = False
        self.recorded_positions = [None for _ in range(6)]
        self.s = s
        self.picam2 = picam2  # Caméra intégrée
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
        grid[4, 5] = self.create_button('Snap', 'cyan')  # Bouton Snap
        grid[4, 6] = self.create_button('Preview', 'orange')  # Bouton Preview
        grid[4, 7] = self.create_button('Stop Preview', 'red')  # Bouton Stop Preview

        self.grid = grid
        self.output = Output()
        display(grid, self.output)



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
        
    def light_all_different_colors(self):
        """Activates the multi-color illumination."""
        self.write_code("A\n")
        
    def light_one_by_one(self):
        """Activate sequential illumination mode."""
        self.write_code("B\n")
        
    def light_all_one_color(self):
        """Activate uniform white illumination."""
        self.write_code("C/n")
        
    def turn_off(self):
        """Turn off all lights"""
        self.write_code("S0\n")
        
    def query_state(self):
        """Quarry the current state of rgb values."""
        self.write_code("?\n")
        return self.seriel.readline().decode('utf-8').strip()
        
        
