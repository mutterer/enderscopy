"""OS-level transports (PTY on POSIX, TCP socket on Windows) used by the virtual Marlin device."""

import os
import socket
import time
from typing import Optional


class VirtualSerialBackend:
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


class PtyBackend(VirtualSerialBackend):
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


class SocketBackend(VirtualSerialBackend):
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
