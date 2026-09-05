"""MPU-side show controller for Arduino UNO Q."""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from config import (
    HEARTBEAT_SECONDS,
    SCENERY_LIMITS,
    SCENERY_MOTOR,
    SERVO,
    SERVO_LIMITS,
    STEPPER,
    STEPPER_LIMITS,
    STAGE_LIGHT_COUNT,
)


class ShowError(RuntimeError):
    pass


def _bounded(value: int, limits: tuple[int, int], label: str) -> int:
    value = int(value)
    if not limits[0] <= value <= limits[1]:
        raise ShowError(f"{label}={value} is outside {limits}")
    return value


class TheaterController:
    def __init__(self, bridge: Any, log: Callable[[str], None] = print):
        self.bridge = bridge
        self.log = log
        self._stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._audio: subprocess.Popen[bytes] | None = None

    def call(self, method: str, *args: Any) -> Any:
        try:
            return self.bridge.call(method, *args)
        except Exception as exc:
            raise ShowError(f"MCU call {method!r} failed: {exc}") from exc

    def start(self) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat(self) -> None:
        while not self._stop.wait(HEARTBEAT_SECONDS):
            try:
                self.call("heartbeat")
            except ShowError as exc:
                self.log(str(exc))

    def arm(self) -> None:
        state = int(self.call("arm_system", True))
        if not state & 0x01:
            raise ShowError(f"MCU refused to arm; state=0x{state:02x}")
        self.log("Actuators armed")

    def stop(self) -> None:
        self._stop.set()
        try:
            self.call("stop_all")
            self.call("arm_system", False)
        finally:
            if self._audio and self._audio.poll() is None:
                self._audio.terminate()
            self.log("Show stopped and actuators disarmed")

    def shutdown(self) -> None:
        """Stop local workers without making RPC calls during App shutdown."""
        self._stop.set()
        if self._audio and self._audio.poll() is None:
            self._audio.terminate()

    def servo(self, name: str, degrees: int, duration_ms: int = 500) -> None:
        if name not in SERVO:
            raise ShowError(f"Unknown servo {name!r}")
        degrees = _bounded(degrees, SERVO_LIMITS[name], name)
        self.call("set_servo", SERVO[name], degrees, max(20, int(duration_ms)))

    def stepper(self, name: str, target_steps: int, speed_sps: int = 800) -> None:
        if name not in STEPPER:
            raise ShowError(f"Unknown stepper {name!r}")
        target = _bounded(target_steps, STEPPER_LIMITS[name], name)
        self.call("move_stepper", STEPPER[name], target, max(1, int(speed_sps)))

    def scenery(self, side: str, target_counts: int, max_pwm: int = 120) -> None:
        if side not in SCENERY_MOTOR:
            raise ShowError(f"Unknown scenery motor {side!r}")
        target = _bounded(target_counts, SCENERY_LIMITS[side], side)
        self.call("move_dc", SCENERY_MOTOR[side], target, _bounded(max_pwm, (1, 255), "max_pwm"))

    def rgb_light(self, light: int, red: int, green: int, blue: int) -> None:
        self.call(
            "set_rgb_light",
            _bounded(light, (0, STAGE_LIGHT_COUNT - 1), "light"),
            _bounded(red, (0, 255), "red"),
            _bounded(green, (0, 255), "green"),
            _bounded(blue, (0, 255), "blue"),
        )

    def all_rgb_lights(self, red: int, green: int, blue: int) -> None:
        self.call(
            "set_all_rgb_lights",
            _bounded(red, (0, 255), "red"),
            _bounded(green, (0, 255), "green"),
            _bounded(blue, (0, 255), "blue"),
        )

    def audio(self, filename: str) -> None:
        path = Path(filename)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        if not path.exists():
            self.log(f"Audio skipped; file does not exist: {path}")
            return
        if self._audio and self._audio.poll() is None:
            self._audio.terminate()
        # aplay is available for WAV on typical Debian images. Replace this command
        # when the final audio interface and file format are selected.
        self._audio = subprocess.Popen(["aplay", str(path)])

    def execute(self, action: dict[str, Any]) -> None:
        kind = action["type"]
        if kind == "servo":
            self.servo(action["name"], action["degrees"], action.get("duration_ms", 500))
        elif kind == "stepper":
            self.stepper(action["name"], action["target_steps"], action.get("speed_sps", 800))
        elif kind == "scenery":
            self.scenery(action["side"], action["target_counts"], action.get("max_pwm", 120))
        elif kind == "light":
            self.rgb_light(action["light"], action["red"], action["green"], action["blue"])
        elif kind == "all_lights":
            self.all_rgb_lights(action["red"], action["green"], action["blue"])
        elif kind == "audio":
            self.audio(action["file"])
        elif kind == "wait":
            self._stop.wait(max(0.0, float(action["seconds"])))
        else:
            raise ShowError(f"Unknown action type {kind!r}")

    def play(self, cue_file: str | Path) -> None:
        cue_path = Path(cue_file)
        data = json.loads(cue_path.read_text(encoding="utf-8"))
        self.start()
        self.arm()
        try:
            for cue in data["cues"]:
                if self._stop.is_set():
                    break
                self.log(f"Cue: {cue['name']}")
                for action in cue["actions"]:
                    self.execute(action)
        except Exception:
            self.stop()
            raise
