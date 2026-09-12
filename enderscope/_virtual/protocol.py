"""Minimal Marlin G-code interpreter used to emulate a stage over a virtual serial link."""

from typing import Dict, List

from .history import VirtualPositionHistory


def strip_comments(line: str) -> str:
    # Very small Marlin-like comment handling: ';' starts a comment.
    if ';' in line:
        line = line.split(';', 1)[0]
    return line.strip()


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_args(tokens: List[str]) -> Dict[str, float]:
    """Parse Marlin-ish args.

    Supports both compact form (X10) and split form (X 10) used in enderscope.py.
    """
    args: Dict[str, float] = {}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if not t:
            i += 1
            continue
        t = t.strip()
        if len(t) == 1 and t.upper() in ("X", "Y", "Z", "E", "F", "S"):
            # Split form: X 10
            if i + 1 < len(tokens) and is_float(tokens[i + 1]):
                args[t.upper()] = float(tokens[i + 1])
                i += 2
                continue
        # Compact form: X10, Y-5
        k = t[0].upper()
        if k in ("X", "Y", "Z", "E", "F", "S") and len(t) > 1 and is_float(t[1:]):
            args[k] = float(t[1:])
        i += 1
    return args


class VirtualMarlinState:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0
        self.absolute_xyz = True
        self.absolute_e = True
        self.feedrate = 1500.0
        self.history = VirtualPositionHistory()
        self.history.add(self.x, self.y, self.z, self.e)


class VirtualMarlinProtocol:
    def __init__(self, on_position_update=None):
        self.state = VirtualMarlinState()
        self._on_position_update = on_position_update

    def startup_lines(self) -> List[str]:
        # Keep it minimal; Stage.write_code will skip until it sees "ok".
        return ["start", "echo:Marlin (virtual)"]

    def handle(self, raw_line: str) -> List[str]:
        line = raw_line.strip("\r\n")
        if not line:
            return []

        # Accept and ignore checksums/line numbers like: N123 G0 X10*45
        line_wo_checksum = line.split("*", 1)[0].strip()
        if line_wo_checksum.upper().startswith("N"):
            parts = line_wo_checksum.split()
            if len(parts) >= 2:
                line_wo_checksum = " ".join(parts[1:])

        line_wo_checksum = strip_comments(line_wo_checksum)
        if not line_wo_checksum:
            return []

        parts = line_wo_checksum.split()
        cmd = parts[0].upper()
        args = parse_args(parts[1:])

        if cmd in ("G0", "G00", "G1", "G01"):
            return self._handle_move(args)
        if cmd == "G28":
            return self._handle_home(args)
        if cmd == "G90":
            self.state.absolute_xyz = True
            return ["ok"]
        if cmd == "G91":
            self.state.absolute_xyz = False
            return ["ok"]
        if cmd == "M82":
            self.state.absolute_e = True
            return ["ok"]
        if cmd == "M83":
            self.state.absolute_e = False
            return ["ok"]
        if cmd == "M203":
            # Speed limits (ignored, but acknowledged)
            return ["ok"]
        if cmd == "M400":
            # Finish moves
            return ["ok"]
        if cmd == "M114":
            # Current position: Stage.get_position expects one line, then an ok line.
            s = self.state
            pos = (
                f"X:{s.x:.2f} Y:{s.y:.2f} Z:{s.z:.2f} E:{s.e:.2f} "
                f"Count X:0 Y:0 Z:0"
            )
            return [pos, "ok"]

        return [f'echo:Unknown command: "{line_wo_checksum}"', "ok"]

    def _handle_home(self, args: Dict[str, float]) -> List[str]:
        # Home selected axes if specified, else all.
        has_axis = any(k in args for k in ("X", "Y", "Z"))
        if not has_axis:
            self.state.x = 0.0
            self.state.y = 0.0
            self.state.z = 0.0
        else:
            if "X" in args:
                self.state.x = 0.0
            if "Y" in args:
                self.state.y = 0.0
            if "Z" in args:
                self.state.z = 0.0

        self.state.history.add(self.state.x, self.state.y, self.state.z, self.state.e)
        if self._on_position_update is not None:
            try:
                self._on_position_update(self.state.x, self.state.y, self.state.z, self.state.e)
            except Exception:
                pass
        return ["ok"]

    def _handle_move(self, args: Dict[str, float]) -> List[str]:
        s = self.state
        if "F" in args:
            s.feedrate = float(args["F"])

        def apply_axis(cur: float, key: str) -> float:
            if key not in args:
                return cur
            v = float(args[key])
            return v if s.absolute_xyz else (cur + v)

        s.x = apply_axis(s.x, "X")
        s.y = apply_axis(s.y, "Y")
        s.z = apply_axis(s.z, "Z")

        # E is rarely used by your Stage, but keep it consistent.
        if "E" in args:
            ev = float(args["E"])
            s.e = ev if s.absolute_e else (s.e + ev)

        s.history.add(s.x, s.y, s.z, s.e)
        if self._on_position_update is not None:
            try:
                self._on_position_update(s.x, s.y, s.z, s.e)
            except Exception:
                pass

        return ["ok"]
