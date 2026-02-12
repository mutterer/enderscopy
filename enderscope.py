import time
import glob
import sys
import os
import atexit
import threading
import socket
import io
import warnings
import json
from typing import Optional, Dict, Tuple, List
from time import sleep
import serial
from ipywidgets import widgets, Button, Layout, ButtonStyle, GridspecLayout, Output
from IPython.display import display, Image
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


class _VirtualPositionHistory:
    def __init__(self):
        self._lock = threading.Lock()
        # Store tuples of (t, x, y, z, e)
        self._points: List[Tuple[float, float, float, float, float]] = []

    def add(self, x: float, y: float, z: float, e: float) -> None:
        with self._lock:
            self._points.append((time.time(), float(x), float(y), float(z), float(e)))

    def snapshot_xyz(self) -> List[Tuple[float, float, float]]:
        with self._lock:
            return [(p[1], p[2], p[3]) for p in self._points]

    def snapshot_xyze(self) -> List[Tuple[float, float, float, float]]:
        with self._lock:
            return [(p[1], p[2], p[3], p[4]) for p in self._points]

    def clear(self) -> None:
        with self._lock:
            self._points.clear()

    def reset_to(self, x: float, y: float, z: float, e: float = 0.0) -> None:
        with self._lock:
            self._points.clear()
            self._points.append((time.time(), float(x), float(y), float(z), float(e)))

    def set_xyz(self, points: List[Tuple[float, float, float]], e: float = 0.0) -> None:
        """Replace history with a list of (x, y, z) points."""
        with self._lock:
            self._points = [(time.time(), float(x), float(y), float(z), float(e)) for (x, y, z) in points]


class _VirtualStagePathPlotter:
    """Live plot of the virtual stage XYZ path.

    Uses a Matplotlib timer to refresh from the history buffer.
    """

    def __init__(self, history: _VirtualPositionHistory, title: str = "Virtual Stage Path"):
        self._history = history
        self._title = title
        self._last_len = 0
        self._timer = None
        self._closed = False
        self._display_handle = None
        self._warned_interactive = False
        self._inline_backend = False
        self._scatter = None

        # Create a 3D plot.
        self._fig = plt.figure()
        self._ax = self._fig.add_subplot(111, projection='3d')
        self._ax.set_title(self._title)
        self._ax.set_xlabel('X')
        self._ax.set_ylabel('Y')
        self._ax.set_zlabel('Z')
        try:
            self._ax.set_xlim(-10, 300)
            self._ax.set_ylim(-10, 300)
            self._ax.set_zlim(-10, 300)
        except Exception:
            pass
        (self._line,) = self._ax.plot([], [], [], '-', linewidth=1)
        (self._pt,) = self._ax.plot([], [], [], 'o', color='lightgreen', markersize=12)

        try:
            self._fig.canvas.mpl_connect('close_event', self._on_close)
        except Exception:
            pass

        # In Jupyter, the default inline backend won't execute GUI timers.
        # - For interactive GUI backends, we use a canvas timer.
        # - For inline backends, we use an IPython display handle and refresh on-demand.
        try:
            import matplotlib
            backend = (matplotlib.get_backend() or "").lower()
        except Exception:
            backend = ""

        if "inline" in backend:
            self._inline_backend = True
            if not self._warned_interactive:
                self._warned_interactive = True
                warnings.warn(
                    "Matplotlib is using the inline backend, so the virtual-stage plot is not interactive. "
                    "For zoom/rotate/pan in JupyterLab: install `ipympl` and run `%matplotlib widget` before creating the Stage.",
                    RuntimeWarning,
                )
            try:
                from IPython.display import display
                self._display_handle = display(self._fig, display_id=True)
                # Prevent the inline backend from auto-displaying the same figure
                # again at the end of the cell execution.
                try:
                    plt.close(self._fig)
                except Exception:
                    pass
            except Exception:
                self._display_handle = None
        else:
            # Start a periodic refresh timer (runs in GUI event loop).
            try:
                self._timer = self._fig.canvas.new_timer(interval=200)
                self._timer.add_callback(self._refresh)
                self._timer.start()
            except Exception:
                self._timer = None

            # Attempt to pop up a window without blocking.
            try:
                plt.show(block=False)
            except Exception:
                pass

    def _on_close(self, *_args):
        self._closed = True
        try:
            if self._timer is not None:
                self._timer.stop()
        except Exception:
            pass

    def _refresh(self):
        if self._closed:
            return
        pts = self._history.snapshot_xyz()
        if len(pts) == self._last_len:
            return
        self._last_len = len(pts)
        if not pts:
            # History cleared: clear artists so the plot reflects it.
            try:
                self._line.set_data([], [])
                self._line.set_3d_properties([])
            except Exception:
                pass
            try:
                if self._scatter is not None:
                    self._scatter.remove()
                    self._scatter = None
            except Exception:
                pass
            try:
                self._pt.set_data([], [])
                self._pt.set_3d_properties([])
            except Exception:
                pass

            # Force a draw/update.
            if self._display_handle is not None and self._inline_backend:
                try:
                    self._fig.canvas.draw()
                    buf = io.BytesIO()
                    self._fig.savefig(buf, format="png")
                    self._display_handle.update(Image(data=buf.getvalue()))
                except Exception:
                    pass
            else:
                try:
                    self._fig.canvas.draw_idle()
                except Exception:
                    pass
                if self._display_handle is not None:
                    try:
                        self._display_handle.update(self._fig)
                    except Exception:
                        pass
            return

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]

        # Line connecting positions.
        try:
            self._line.set_data(xs, ys)
            self._line.set_3d_properties(zs)
        except Exception:
            pass

        # Markers for the full history.
        try:
            if self._scatter is not None:
                self._scatter.remove()
        except Exception:
            pass

        try:
            self._scatter = self._ax.scatter(xs, ys, zs, c='red', s=12, depthshade=False)
        except Exception:
            self._scatter = None
        self._pt.set_data([xs[-1]], [ys[-1]])
        self._pt.set_3d_properties([zs[-1]])

        # Use fixed limits for a stable view.
        try:
            self._ax.set_xlim(-10, 300)
            self._ax.set_ylim(-10, 300)
            self._ax.set_zlim(-10, 300)
        except Exception:
            pass

        # Draw/update depending on backend.
        if self._display_handle is not None and self._inline_backend:
            # Inline backend: explicitly render to PNG and update the output.
            # Updating the raw Figure object can be deferred until cell end.
            try:
                self._fig.canvas.draw()
                buf = io.BytesIO()
                self._fig.savefig(buf, format="png")
                self._display_handle.update(Image(data=buf.getvalue()))
            except Exception:
                pass
        else:
            try:
                self._fig.canvas.draw_idle()
            except Exception:
                pass

            if self._display_handle is not None:
                try:
                    self._display_handle.update(self._fig)
                except Exception:
                    pass

    def force_refresh(self) -> None:
        """Force a refresh (useful for Jupyter inline backends)."""
        try:
            self._refresh()
        finally:
            # Some interactive backends need an event flush.
            try:
                self._fig.canvas.flush_events()
            except Exception:
                pass

G_CODES = {
    'absolute': 'G90',
    'relative': 'G91',
    'homing': 'G28',
    'finish': 'M400',
    'set_speed_limit': 'M203',    
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


# ------------------------------------------------------------
# Virtual Marlin serial device (pure Python)
#
# Usage: Stage('virtual', 115200)
# - macOS/Linux: creates a PTY slave path and connects via pyserial.
# - Windows: uses a TCP server and connects via pyserial's socket:// URL.
# ------------------------------------------------------------

def _vs_strip_comments(line: str) -> str:
    # Very small Marlin-like comment handling: ';' starts a comment.
    if ';' in line:
        line = line.split(';', 1)[0]
    return line.strip()


def _vs_is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _vs_parse_args(tokens: List[str]) -> Dict[str, float]:
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
            if i + 1 < len(tokens) and _vs_is_float(tokens[i + 1]):
                args[t.upper()] = float(tokens[i + 1])
                i += 2
                continue
        # Compact form: X10, Y-5
        k = t[0].upper()
        if k in ("X", "Y", "Z", "E", "F", "S") and len(t) > 1 and _vs_is_float(t[1:]):
            args[k] = float(t[1:])
        i += 1
    return args


class _VirtualMarlinState:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0
        self.absolute_xyz = True
        self.absolute_e = True
        self.feedrate = 1500.0
        self.history = _VirtualPositionHistory()
        self.history.add(self.x, self.y, self.z, self.e)


class _VirtualMarlinProtocol:
    def __init__(self, on_position_update=None):
        self.state = _VirtualMarlinState()
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

        line_wo_checksum = _vs_strip_comments(line_wo_checksum)
        if not line_wo_checksum:
            return []

        parts = line_wo_checksum.split()
        cmd = parts[0].upper()
        args = _vs_parse_args(parts[1:])

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


class _VirtualSerialBackend:
    def endpoint(self) -> str:
        raise NotImplementedError

    def start(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def read_line(self, timeout: float) -> Optional[bytes]:
        raise NotImplementedError

    def write(self, data: bytes) -> None:
        raise NotImplementedError


class _PtyBackend(_VirtualSerialBackend):
    def __init__(self):
        self._master_fd: Optional[int] = None
        self._slave_name: Optional[str] = None
        self._buf = bytearray()

    def start(self) -> None:
        import pty

        mfd, sfd = pty.openpty()
        self._master_fd = mfd
        self._slave_name = os.ttyname(sfd)
        try:
            os.set_blocking(self._master_fd, False)
        except Exception:
            pass

    def endpoint(self) -> str:
        if not self._slave_name:
            raise RuntimeError("PTY backend not started")
        return self._slave_name

    def close(self) -> None:
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

    def read_line(self, timeout: float) -> Optional[bytes]:
        if self._master_fd is None:
            return None
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                chunk = os.read(self._master_fd, 1024)
                if chunk:
                    self._buf.extend(chunk)
                line = self._try_split_line()
                if line is not None:
                    return line
            except BlockingIOError:
                pass
            except OSError:
                return None
            time.sleep(0.01)
        return None

    def _try_split_line(self) -> Optional[bytes]:
        for sep in (b"\n", b"\r"):
            idx = self._buf.find(sep)
            if idx != -1:
                out = bytes(self._buf[: idx + 1])
                del self._buf[: idx + 1]
                if out.endswith(b"\r") and self._buf[:1] == b"\n":
                    del self._buf[:1]
                    out = out[:-1] + b"\n"
                return out
        return None

    def write(self, data: bytes) -> None:
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, data)
        except OSError:
            pass


class _SocketBackend(_VirtualSerialBackend):
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self.port = port
        self._srv: Optional[socket.socket] = None
        self._conn: Optional[socket.socket] = None
        self._buf = bytearray()

    def start(self) -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(1)
        srv.settimeout(0.2)
        self._srv = srv
        self.port = srv.getsockname()[1]

    def endpoint(self) -> str:
        return f"socket://{self.host}:{self.port}"

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except OSError:
                pass
            self._conn = None
        if self._srv is not None:
            try:
                self._srv.close()
            except OSError:
                pass
            self._srv = None

    def _ensure_conn(self) -> Optional[socket.socket]:
        if self._conn is not None:
            return self._conn
        if self._srv is None:
            return None
        try:
            conn, _ = self._srv.accept()
            conn.settimeout(0.2)
            self._conn = conn
            return conn
        except socket.timeout:
            return None
        except OSError:
            return None

    def read_line(self, timeout: float) -> Optional[bytes]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            conn = self._ensure_conn()
            if conn is None:
                time.sleep(0.01)
                continue
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    try:
                        conn.close()
                    except OSError:
                        pass
                    self._conn = None
                    continue
                self._buf.extend(chunk)
                line = self._try_split_line()
                if line is not None:
                    return line
            except socket.timeout:
                time.sleep(0.01)
            except OSError:
                self._conn = None
                return None
        return None

    def _try_split_line(self) -> Optional[bytes]:
        for sep in (b"\n", b"\r"):
            idx = self._buf.find(sep)
            if idx != -1:
                out = bytes(self._buf[: idx + 1])
                del self._buf[: idx + 1]
                if out.endswith(b"\r") and self._buf[:1] == b"\n":
                    del self._buf[:1]
                    out = out[:-1] + b"\n"
                return out
        return None

    def write(self, data: bytes) -> None:
        conn = self._ensure_conn()
        if conn is None:
            return
        try:
            conn.sendall(data)
        except OSError:
            self._conn = None


class _VirtualMarlinDevice:
    def __init__(self, baudrate: int):
        self._position_update_event = threading.Event()

        def _notify_position_update(_x, _y, _z, _e):
            self._position_update_event.set()

        self._proto = _VirtualMarlinProtocol(on_position_update=_notify_position_update)
        self.history = self._proto.state.history
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if os.name == "nt":
            self._backend: _VirtualSerialBackend = _SocketBackend()
        else:
            self._backend = _PtyBackend()

        self._backend.start()

        # Connect with pyserial to the exposed endpoint
        ep = self._backend.endpoint()
        if ep.startswith("socket://"):
            self.serial = serial.serial_for_url(ep, baudrate=baudrate, timeout=1, write_timeout=1)
        else:
            self.serial = serial.Serial(ep, baudrate=baudrate, timeout=1, write_timeout=1)

        # Emit a short startup banner
        for line in self._proto.startup_lines():
            self._backend.write((line + "\n").encode("utf-8"))

        self._thread = threading.Thread(target=self._run, name="VirtualMarlin", daemon=True)
        self._thread.start()

        atexit.register(self.close)

    def close(self):
        self._stop.set()
        try:
            if self._thread is not None:
                self._thread.join(timeout=0.5)
        except Exception:
            pass
        try:
            self._backend.close()
        except Exception:
            pass
        try:
            self.serial.close()
        except Exception:
            pass

    def _run(self):
        while not self._stop.is_set():
            raw = self._backend.read_line(timeout=0.1)
            if not raw:
                continue
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                continue
            for out in self._proto.handle(text):
                self._backend.write((out + "\n").encode("utf-8"))

class SerialUtils:

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


class SerialDevice:
    def __init__(self, port, baud_rate, parity=serial.PARITY_NONE,
                 stop_bits=serial.STOPBITS_ONE, byte_size=serial.EIGHTBITS):
        self._virtual_device = None
        if isinstance(port, str) and port.lower() == 'virtual':
            # Create a virtual Marlin device and attach pyserial to it.
            self._virtual_device = _VirtualMarlinDevice(baudrate=baud_rate)
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
                self._virtual_path_plotter = _VirtualStagePathPlotter(
                    self._virtual_device.history,
                    title="Virtual Stage XYZ Path",
                )
            except Exception:
                self._virtual_path_plotter = None

        if homing==True:
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
        super().write_code(code)
        response = self.serial.readline().decode('utf-8')
        if check_ok:
            while not response.startswith("ok"):
                if debug:
                    print (response.strip('\n'))
                response = self.serial.readline().decode('utf-8')
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

    def set_steps(self, xys,zs):
        self.xys = xys
        self.zs = zs
        
    def checkbox_changed(self,element):
        if element['new'] == True:
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
            if self.recording == True:
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

class ScanPatterns:
    def plot_path(path = np.array([[0,0]]), labels=True, field = (10,10), title='Path preview'):
        x=path[:, 0]
        y=path[:, 1]
        field = Rectangle((0,0),field[0],field[1])
        rectangle = Rectangle((0,0), 200, 190,
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

    def raster(cols=4, rows=3):
        return np.array(list((x,y) for y in range(rows) for x in range(cols)))

    def snake(cols=4, rows=3):
        return np.array(
            list((x,y)
                 for y in range(rows)
                 for x in range((cols-1)*(y%2),cols-(cols+1)*(y%2),((y+1)%2)-1*((y%2)))
                ))

    def random(num_points = 10, seed=1):
        x_min, x_max = 0, 180  # Range for x values
        y_min, y_max = 0, 180  # Range for y values
        np.random.seed(seed)
        return np.column_stack((
            np.random.uniform(x_min, x_max, num_points),
            np.random.uniform(y_min, y_max, num_points)))

    def spiral(num_points = 50):    
        directions = np.array([[1,0],[0,1],[-1,0],[0,-1]])
        d = 0
        i = 1 
        p = np.array([0,0])
        sp = np.array([p])
        while len(sp)<num_points:
            for j in range(i):
                p=p+directions[d]
                sp = np.append(sp,[p], axis=0)
            d = (d+1)%4
            i = i + (d%2==0)            
        return np.array(sp[:num_points])
