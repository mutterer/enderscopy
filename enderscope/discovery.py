"""Auto-discovery of stage/lights serial ports by probing candidate devices."""

import time
from typing import List

import serial

from .lights import Enderlights
from .serial_utils import SerialUtils
from .stage import Stage


def _candidate_serial_ports() -> List[str]:
    """Return a de-duplicated list of available serial device paths."""
    ports: List[str] = []
    try:
        from serial.tools import list_ports

        ports = [p.device for p in list_ports.comports() if p.device]
    except Exception:
        ports = []

    # Fallback to existing helper for platforms where list_ports may fail.
    if not ports:
        try:
            ports = SerialUtils.serial_ports()
        except Exception:
            ports = []

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(ports))


def _probe_serial_response(
    port: str,
    baud_rate: int,
    command: str,
    validator,
    attempts: int = 8,
    timeout: float = 0.35,
) -> bool:
    """Send a probe command and validate any response line with validator()."""
    ser = None
    try:
        ser = serial.Serial(port=port, baudrate=baud_rate, timeout=timeout, write_timeout=timeout)
        # Many devices emit boot text; clear it and then probe.
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except Exception:
            pass

        time.sleep(0.15)
        ser.write((command + "\n").encode("utf-8"))

        for _ in range(attempts):
            raw = ser.readline().decode("ascii", errors="replace").strip()
            if not raw:
                continue
            if validator(raw):
                return True
        return False
    except Exception:
        return False
    finally:
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass


def autoconnect(connect_stage: bool = True, connect_lights: bool = True):
    """Auto-discover and connect to stage and lights serial devices.

    Returns:
        tuple: (stage, lights), where each entry is an object or None.
    """
    ports = _candidate_serial_ports()
    stage = None
    lights = None
    stage_port = None
    lights_port = None

    if connect_stage:
        for port in ports:
            ok = _probe_serial_response(
                port=port,
                baud_rate=115200,
                command="M114",
                validator=lambda line: "X" in line,
            )
            if ok:
                stage_port = port
                break

        if stage_port is None:
            print("Error: could not auto-detect stage port (M114 response containing 'X' not found).")
        else:
            try:
                stage = Stage(stage_port, 115200)
            except Exception as e:
                print(f"Error: failed to connect stage on {stage_port}: {e}")

    if connect_lights:
        candidate_ports = [p for p in ports if p != stage_port]
        for port in candidate_ports:
            ok = _probe_serial_response(
                port=port,
                baud_rate=57600,
                command="?",
                validator=lambda line: line.startswith("ENDERLIGHTS"),
            )
            if ok:
                lights_port = port
                break

        if lights_port is None:
            print("Error: could not auto-detect lights port (reply starting with 'ENDERLIGHTS' not found).")
        else:
            try:
                lights = Enderlights(lights_port, 57600)
            except Exception as e:
                print(f"Error: failed to connect lights on {lights_port}: {e}")

    return stage, lights
