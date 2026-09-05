"""Arduino App Lab entry point, following the Blink LED with UI pattern."""

from __future__ import annotations

import threading
from pathlib import Path

from arduino.app_utils import App, Bridge, Logger
from arduino.app_bricks.web_ui import WebUI

from config import DEFAULT_CUE_FILE
from theater import TheaterController

logger = Logger("pinocchio-theater")
controller = TheaterController(Bridge, logger.info)
ui = WebUI()
show_thread = None


def get_theater_status():
    """Return JSON-friendly state for the browser UI."""
    state = int(controller.call("get_state"))
    left_command = int(controller.call("get_dc_command", 0))
    right_command = int(controller.call("get_dc_command", 1))

    def direction(command):
        if command > 0:
            return "forward"
        if command < 0:
            return "reverse"
        return "stopped"

    return {
        "armed": bool(state & 0x01),
        "estop": bool(state & 0x02),
        "watchdog_fault": bool(state & 0x04),
        "state_bits": state,
        "show_running": bool(show_thread and show_thread.is_alive()),
        "left_encoder": int(controller.call("get_encoder", 0)),
        "right_encoder": int(controller.call("get_encoder", 1)),
        "left_dc_command": left_command,
        "right_dc_command": right_command,
        "left_direction": direction(left_command),
        "right_direction": direction(right_command),
    }


def send_status(client=None, error=None):
    try:
        status = get_theater_status()
        if error:
            status["error"] = str(error)
    except Exception as exc:
        status = {"error": str(exc), "armed": False, "show_running": False}
    if client is None:
        ui.send_message("theater_status_update", status)
    else:
        ui.send_message("theater_status_update", status, client)


def on_get_initial_state(client, _data):
    send_status(client)


def on_set_arm(_client, data):
    try:
        controller.start()
        controller.arm() if bool(data.get("enabled")) else controller.stop()
        send_status()
    except Exception as exc:
        send_status(error=exc)


def on_stop(_client, _data):
    controller.stop()
    send_status()


def on_set_servo(_client, data):
    try:
        controller.servo(str(data["name"]), int(data["degrees"]), int(data.get("duration_ms", 500)))
        send_status()
    except Exception as exc:
        send_status(error=exc)


def on_move_stepper(_client, data):
    try:
        controller.stepper(str(data["name"]), int(data["target_steps"]), int(data.get("speed_sps", 800)))
        send_status()
    except Exception as exc:
        send_status(error=exc)


def on_move_scenery(_client, data):
    try:
        controller.scenery(str(data["side"]), int(data["target_counts"]), int(data.get("max_pwm", 120)))
        send_status()
    except Exception as exc:
        send_status(error=exc)


def on_set_rgb_light(_client, data):
    try:
        controller.rgb_light(
            int(data["light"]), int(data["red"]), int(data["green"]), int(data["blue"])
        )
        send_status()
    except Exception as exc:
        send_status(error=exc)


def run_example() -> None:
    try:
        controller.play(Path(__file__).resolve().parent / DEFAULT_CUE_FILE)
    except Exception as exc:
        logger.error(f"Show failed: {exc}")
        controller.stop()
        send_status(error=exc)
    else:
        send_status()


def on_play_show(_client, _data):
    global show_thread
    if show_thread and show_thread.is_alive():
        return
    show_thread = threading.Thread(target=run_example, daemon=True)
    show_thread.start()
    send_status()


def main() -> None:
    logger.info("Pinocchio theater MPU controller starting")
    logger.info("Web UI ready; hardware remains disarmed")
    try:
        App.run()
    finally:
        controller.shutdown()


# Blink LED with UI-style WebSocket message registration.
ui.on_message("get_initial_state", on_get_initial_state)
ui.on_message("set_arm", on_set_arm)
ui.on_message("stop_all", on_stop)
ui.on_message("set_servo", on_set_servo)
ui.on_message("move_stepper", on_move_stepper)
ui.on_message("move_scenery", on_move_scenery)
ui.on_message("set_rgb_light", on_set_rgb_light)
ui.on_message("play_show", on_play_show)


if __name__ == "__main__":
    main()
