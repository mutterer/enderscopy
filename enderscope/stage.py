"""The 3-axis motorized stage that moves the sample."""

from typing import List, Tuple

import serial

from ._virtual.history import VirtualStagePathPlotter
from .constants import DIRECTION_PREFIXES, ENDER3V3SE, G_CODES
from .serial_device import SerialDevice


class Stage(SerialDevice):
    """
    This is the 3 axis stage that moves the sample
    """

    def __init__(self, port, baud_rate, homing=False, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS,
                 plot_virtual_path: bool = True):
        super().__init__(port, baud_rate, parity, stop_bits, byte_size)

        # If we're using the virtual stage, pop up a live XYZ path plot.
        self._virtual_path_plotter = None
        if plot_virtual_path and getattr(self, "_virtual_device", None) is not None:
            try:
                self._virtual_path_plotter = VirtualStagePathPlotter(
                    self._virtual_device.history,
                    title="Virtual Stage XYZ Path",
                )
            except Exception:
                self._virtual_path_plotter = None

        if homing:
            self.home()

    def get_position_history(self, xyze: bool = False):
        """Return the recorded position history for a virtual stage.

        :param bool xyze: if True, returns (x, y, z, e) tuples; else (x, y, z)
        """
        vd = getattr(self, "_virtual_device", None)
        if vd is None or not hasattr(vd, "history"):
            return []
        return vd.history.snapshot_xyze() if xyze else vd.history.snapshot_xyz()

    def get_history(self, xyze: bool = False):
        """Return the recorded history for a virtual stage.

        Behavior:
        - If ``xyze=False`` (default): returns a list of ``(x, y, z)`` tuples.
            If the underlying history elements include an ``E`` value, it is
            stripped.
        - If ``xyze=True``: returns the underlying history elements unchanged
            (typically ``(x, y, z, e)`` tuples).

        For non-virtual stages, returns an empty list.
        """
        hist = self.get_position_history(xyze=xyze)
        if not xyze:
            try:
                return [(x, y, z) for (x, y, z, _e) in hist]
            except Exception:
                return [(p[0], p[1], p[2]) for p in hist]
        return list(hist)

    def clear_history(self, keep_current: bool = True, debug: bool = False):
        """Clear the recorded position history for a virtual stage.

        :param bool keep_current: if True, the history will be reset to the current (x, y, z)
        :param bool debug: passed through to position query if needed
        """
        vd = getattr(self, "_virtual_device", None)
        if vd is None or not hasattr(vd, "history"):
            return

        if keep_current:
            try:
                x, y, z = self.get_position(debug=debug)
                vd.history.reset_to(x, y, z, 0.0)
            except Exception:
                try:
                    vd.history.clear()
                except Exception:
                    pass
        else:
            try:
                vd.history.clear()
            except Exception:
                pass

    def set_history(self, points: List[Tuple[float, float, float]]):
        """Replace the virtual stage history with a list of (x, y, z) points.

        Updates the live plot (if enabled).
        """
        vd = getattr(self, "_virtual_device", None)
        if vd is None or not hasattr(vd, "history"):
            return

        try:
            vd.history.set_xyz(points)
        except Exception:
            # Fallback: clear and re-add
            try:
                vd.history.clear()
                for (x, y, z) in points:
                    vd.history.add(x, y, z, 0.0)
            except Exception:
                pass

        if getattr(self, "_virtual_path_plotter", None) is not None:
            try:
                self._virtual_path_plotter._last_len = -1
            except Exception:
                pass
            try:
                self._virtual_path_plotter.force_refresh()
            except Exception:
                pass

        # Ensure the plot updates even if the length matches a prior state.
        if getattr(self, "_virtual_path_plotter", None) is not None:
            try:
                self._virtual_path_plotter._last_len = -1
            except Exception:
                pass
            try:
                self._virtual_path_plotter.force_refresh()
            except Exception:
                pass

    def write_code(self, code, check_ok=True, debug=False):
        """
        Writes a gcode command to the stage

        :param str code: gcode command
        :param bool check_ok: check (wait) for 'ok' response
        :param bool debug: print the command to be sent
        """
        super().write_code(code)
        response = self.serial.readline().decode('ascii', errors='replace')
        if check_ok:
            while not response.startswith("ok"):
                if debug:
                    print(response.strip('\n'))
                response = self.serial.readline().decode('ascii', errors='replace')
        if debug:
            print(code)        

        # In notebooks (inline backend), timers may not run; refresh after each
        # command that could update the position.
        if getattr(self, "_virtual_path_plotter", None) is not None:
            try:
                head = (code.strip().split()[:1] or [""])[0].upper()
                if head in ("G0", "G00", "G1", "G01", "G28", "M114"):
                    self._virtual_path_plotter.force_refresh()
            except Exception:
                pass
        return response

    def set_speed(self, speed, debug=False):
        """
        Sets the speed of the stage
        :param speed: speed in mm/min
        :return:
        """
        code = f"G0 F{speed}"
        self.write_code(code, debug=debug)

    def set_speed_limit(self, speed, axis='x', debug=False):
        """
        Sets the speed of the stage

        :param float speed: speed in mm/min
        :param str axis: axis to set speed for, one of 'x', 'y', 'z'
        :param bool debug: print the command to be sent
        """
        self.write_code(f'{G_CODES["set_speed_limit"]} {axis.upper()}{speed}',
                        debug=debug)

    def move_absolute(self, x, y, z=None, debug=False):
        """
        Moves the stage to the given coordinates

        :param float x: x coordinate
        :param float y: y coordinate
        :param float z: (optional) z coordinate
        :param bool debug: print the command to be sent
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

        :param iterable p: position coordinates (x, y, optional z)
        :param bool debug: print the command to be sent
        """
        if p is not None:
            self.move_absolute(*p, debug=debug)

    def move_relative(self, x, y, z=None, debug=False):
        """
        Moves the stage by given mm distance in each axis,
        relative to the current position

        :param float x: x distance
        :param float y: y distance
        :param float z: (optional) z distance
        :param bool debug: print the command to be sent
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

        :param str direction: direction to move, one of 'north', 'south', 'east', 'west', 'up', 'down'
        :param float distance: The distance to move in the given direction
        :param bool debug: print the command to be sent
        """
        self.set_relative()
        code = f"G0 {DIRECTION_PREFIXES[direction.lower()]}{distance}"
        self.write_code(code, debug=debug)

    def move_axis(self, axis, distance, debug=False):
        """
        Moves the stage along the given axis

        :param str axis: axis to move along, one of 'x', 'y', 'z'
        :param float distance: The distance to move in the given direction
        :param bool debug: print the command to be sent
        """
        self.set_relative()
        code = f"G0 {axis.upper()}{distance}"
        self.write_code(code, debug=debug)

    def get_position(self, dict=False, debug=False):
        """
        Gets the current position of the stage

        :param bool dict: return the position as a dictionary
        :param bool debug: print the command to be sent
        :return: current position as a tuple or dictionary
        """
        self.flush_serial_buffer()
        response = self.write_code(G_CODES['current_position'],
                                   check_ok=False)
        if debug:
            print(response)
        ok = self.serial.readline()
        if not ok.decode('ascii', errors='replace').startswith("ok"):
            print("Error reading stage position")
            return
        position = response.split(" Count")[0]
        parts = position.split()
        positions = {part.split(":")[0]: float(part.split(":")[1]) for part in parts}
        if not dict:
            order = ['X','Y', 'Z']
            positions = tuple([positions[field] for field in order])
        return positions

    def home(self, debug=False):
        """Moves the stage to the home position"""
        self.write_code(G_CODES['homing'], debug=debug)

    def safe_home(self, model=ENDER3V3SE, debug=False):
        self.write_code(f"G28 X Y", debug=debug) # homing XY
        self.write_code(f"M206 X{model['x_safe_offset']}", debug=debug) # safe homing offset (from center or FW defined home pos)
        self.write_code(f"M206 Y{model['y_safe_offset']}", debug=debug) # safe homing offset (from center or FW defined home pos)
        self.write_code(f"G28 Z", debug=debug) # Z homing
        self.write_code(f"M206 X{model['x_home_offset']}", debug=debug) # abs x position of new home position as defined above
        self.write_code(f"M206 Y{model['y_home_offset']}", debug=debug) # abs y position of new home position as defined above

    def finish_moves(self, debug=False):
        """
        Finishes the current moves
        Ensures that the stage has finished moving before continuing
        """
        self.write_code(G_CODES['finish'], debug=debug)

    def set_relative(self, debug=False):
        """Sets the stage to relative movement mode"""
        self.write_code(G_CODES['relative'], debug=debug)

    def set_absolute(self, debug=False):
        """Sets the stage to absolute movement mode"""
        self.write_code(G_CODES['absolute'], debug=debug)

    def read_params(self, debug=False):
        """Reads the current device parameters"""
        return self.write_code(G_CODES['device_params'], debug=debug)
