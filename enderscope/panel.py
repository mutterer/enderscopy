"""ipywidgets control panel for jogging a Stage and recording/replaying positions."""

import json
import os
from typing import List, Optional, Tuple

from ipywidgets import Button, GridspecLayout, Layout, Output, widgets
from IPython.display import display


class Panel():
    """
    A control panel for the stage
    This is a basic user interface to control the stage
    built using ipywidgets
    """

    def create_button(self, description, bcolor):
        b = Button(description=description, style=dict(button_color=bcolor), layout=Layout(height='auto', width='auto'))
        b.on_click(self.on_button_clicked)
        return b

    def set_steps(self, xys,zs):
        self.xys = xys
        self.zs = zs

    def checkbox_changed(self,element):
        if element['new']:
            self.recording = True
            element['owner'].description = 'Recording...'
        else:
            self.recording = False
            element['owner'].description = 'Record'

    def on_button_clicked(self, b):
        positions_path = os.path.join(os.getcwd(), "positions.json")

        if b.description == 'Home':
            with self.output:
                self.output.clear_output()
                print("homing...")
            self.s.home()
            with self.output:
                self.output.clear_output()
                print("moving...")
                self.s.finish_moves()
                self.output.clear_output()
                print(self.s.get_position(dict=True))
            return

        elif b.description.startswith('P'):
            m = int(b.description[-1]) - 1
            if self.recording:
                self.recorded_positions[m] = self.s.get_position()
                b.style.button_color = "#ffd6b9"
            elif self.recorded_positions[m] is not None:
                self.s.move_position(self.recorded_positions[m])
            with self.output:
                self.output.clear_output()
                print("moving...")
                self.s.finish_moves()
                self.output.clear_output()
                print(self.s.get_position(dict=True))
            return

        elif b.description.startswith('Save'):
            payload = {
                "recorded_positions": [
                    (list(p) if p is not None else None) for p in self.recorded_positions
                ]
            }
            try:
                with open(positions_path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                with self.output:
                    self.output.clear_output()
                    print(f"saved {positions_path}")
            except Exception as e:
                with self.output:
                    self.output.clear_output()
                    print(f"error saving {positions_path}: {e}")
            return

        elif b.description.startswith('Open'):
            try:
                with open(positions_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                raw = payload.get("recorded_positions", [])
                loaded: List[Optional[Tuple[float, float, float]]] = []
                for item in raw:
                    if item is None:
                        loaded.append(None)
                        continue
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        x = float(item[0])
                        y = float(item[1])
                        z = float(item[2]) if len(item) >= 3 else 0.0
                        loaded.append((x, y, z))
                    else:
                        loaded.append(None)

                # Keep exactly 6 slots (P1..P6)
                loaded = (loaded + [None] * 6)[:6]
                self.recorded_positions = loaded

                # Update P1..P6 button colors to reflect loaded slots.
                for idx in range(6):
                    btn = getattr(self, "_pos_buttons", {}).get(idx)
                    if btn is None:
                        continue
                    btn.style.button_color = "#ffd6b9" if self.recorded_positions[idx] is not None else "lightgrey"

                with self.output:
                    self.output.clear_output()
                    print(f"opened {positions_path}")
            except FileNotFoundError:
                with self.output:
                    self.output.clear_output()
                    print(f"no file found: {positions_path}")
            except Exception as e:
                with self.output:
                    self.output.clear_output()
                    print(f"error opening {positions_path}: {e}")
            return

        # Default: move by direction name (Up/Down/North/South/East/West)
        self.s.move_towards(b.description, 5)
        with self.output:
            self.output.clear_output()
            print("moving...")
            self.s.finish_moves()
            self.output.clear_output()
            print(self.s.get_position(dict=True))

    def __init__(self, s):
        self.recording = False
        self.recorded_positions = [None for i in range(6)]
        self._pos_buttons = {}
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
        self._pos_buttons[0] = self.create_button('P1', 'lightgrey')
        self._pos_buttons[1] = self.create_button('P2', 'lightgrey')
        self._pos_buttons[2] = self.create_button('P3', 'lightgrey')
        self._pos_buttons[3] = self.create_button('P4', 'lightgrey')
        self._pos_buttons[4] = self.create_button('P5', 'lightgrey')
        self._pos_buttons[5] = self.create_button('P6', 'lightgrey')
        grid[1,3] = self._pos_buttons[0]
        grid[1,4] = self._pos_buttons[1]
        grid[2,3] = self._pos_buttons[2]
        grid[2,4] = self._pos_buttons[3]
        grid[3,3] = self._pos_buttons[4]
        grid[3,4] = self._pos_buttons[5]
        grid[4,3] = self.create_button('Save', 'pink')
        grid[4,4] = self.create_button('Open', 'pink')
        self.xys = 5
        self.zs = 1
        self.grid = grid
        self.output = Output()
        display (grid, self.output)
