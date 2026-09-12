"""Top-level virtual Marlin device: wires the protocol to a real pyserial connection."""

import atexit
import os
import threading
from typing import Optional

import serial

from .backends import PtyBackend, SocketBackend, VirtualSerialBackend
from .protocol import VirtualMarlinProtocol


class VirtualMarlinDevice:
    def __init__(self, baudrate: int):
        self._position_update_event = threading.Event()

        def _notify_position_update(_x, _y, _z, _e):
            self._position_update_event.set()

        self._proto = VirtualMarlinProtocol(on_position_update=_notify_position_update)
        self.history = self._proto.state.history
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        if os.name == "nt":
            self._backend: VirtualSerialBackend = SocketBackend()
        else:
            self._backend = PtyBackend()

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
