"""In-memory position history and a live matplotlib XYZ path plotter for the virtual stage."""

import io
import threading
import time
import warnings
from typing import List, Tuple

import matplotlib.pyplot as plt
from IPython.display import Image


class VirtualPositionHistory:
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


class VirtualStagePathPlotter:
    """Live plot of the virtual stage XYZ path.

    Uses a Matplotlib timer to refresh from the history buffer.
    """

    def __init__(self, history: VirtualPositionHistory, title: str = "Virtual Stage Path"):
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
