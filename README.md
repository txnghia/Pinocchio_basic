# Pinocchio Puppet Theater — Arduino UNO Q starter

This project splits the theater controller across both processors in the UNO Q:

- `python/`: Python show control, cue sequencing, audio, microphone hooks, WebUI callbacks, and operator output.
- `sketch/`: real-time servo, stepper, encoded DC motor, lighting, sensor, watchdog, and emergency-stop control.
- `assets/`: operator Web UI following Arduino's **Blink LED with UI** example.
- `app.yaml`: registers the official `arduino:web_ui` Brick.

The starter targets the current inventory: eight servos, three steppers, two quadrature-encoder DC motors, lights, audio, microphone, sensors, and a display. Hardware-specific values are deliberately centralized because the exact motors, drivers, sensors, and display have not been selected yet.

## Safety first

Do not connect motors or servos directly to the UNO Q. Use external drivers and separately fused motor/servo supplies. Join signal ground to the controller ground at the intended common point. A normally-closed physical emergency-stop should remove actuator power independently of this software; the MCU E-stop input is only an additional layer.

Test with belts, strings, and puppet disconnected. Confirm direction and travel limits one actuator at a time.

## Assumed starter hardware

- PCA9685 board at I2C address `0x40`, dedicated to the eight servos.
- Six daisy-chained SM16823E RGB projection modules driven from D19 through a
  3.3 V-to-5 V logic buffer.
- Three step/direction stepper drivers.
- Two bare DRV8871 channels using PWM on both IN1 and IN2.
- Two quadrature encoders.
- Normally-closed E-stop input.
- USB or Media Carrier audio/microphone on Linux.
- Terminal logging as the initial display; a physical display adapter can be added later.

The SM16823E data input is controlled from D19/A5 (PC0). If the modules run
their logic at 5 V, do not connect D19 directly: the SM16823E datasheet's
minimum HIGH threshold is 0.7 × VDD, so use a fast 3.3 V-to-5 V buffer such as
one channel of a 74AHCT125. Connect the modules in data-out to data-in order and
join the module and UNO Q signal grounds. Power the projection LEDs from a
properly sized, fused external supply; do not power them from the UNO Q.

Suggested aiming is a symmetrical six-light layout: far-left crosslight toward
stage right, left wash, two center lights, right crosslight toward stage left,
and a far-right fill toward stage right. The UI labels show these roles. If the
physical chain ultimately has five modules, change `STAGE_LIGHT_COUNT` in both
`sketch/HardwareConfig.h` and `python/config.py`.

DRV8871 wiring: left scenery motor `IN1=D3`, `IN2=D5`; right scenery
motor `IN1=D6`, `IN2=D9`. The stepper pin map was adjusted to reserve these
four PWM-capable outputs; use `sketch/HardwareConfig.h` as the wiring source of
truth.

All three A4988 `ENABLE` inputs share UNO Q pin D13. A4988 enable is active-low:
D13 is LOW while the theater is armed and HIGH during startup, disarm, E-stop,
watchdog timeout, and STOP ALL. Tie the three driver grounds to the MCU signal
ground; do not leave `ENABLE` floating.

## Project map

```text
python/
  main.py             Python App Lab entry point
  theater.py          show engine and Bridge wrapper
  config.py           names, limits, and timing
  cues.json           editable example show
tests/
  test_theater.py     hardware-free tests
sketch/
  sketch.ino
  HardwareConfig.h    pin map and calibration
```

## First setup

1. In Arduino App Lab, duplicate the **Blink LED with UI** example.
2. Replace its `python/` directory with this project's `python/` directory.
3. Replace its UI files with this project's `assets/index.html`, `assets/style.css`, and `assets/app.js`. Retain the example's `assets/libs` files.
4. Replace its `sketch/` directory with this project's `sketch/` directory.
4. Review every value in `HardwareConfig.h` before wiring.
5. Replace the example's `app.yaml` with this project's `app.yaml`.
6. Run `python tests/test_theater.py` on a PC for the hardware-free checks.
7. Start the app with all actuator power off. Confirm that the UI reports the MCU state.
8. Turn actuator power on, release the physical E-stop, arm, and test one channel at a time.

To automatically play the example show when the app starts, set `PUPPET_AUTOSTART=1` in the app environment. It is off by default.

## Bridge commands

Python calls these MCU services:

| Service | Arguments | Purpose |
|---|---|---|
| `heartbeat` | none | Keeps the MCU command watchdog alive |
| `arm_system` | enabled | Enables/disables actuator commands |
| `set_servo` | channel, degrees, duration_ms | Smooth servo movement |
| `move_stepper` | axis, target_steps, speed_sps | Absolute X/Y/curtain movement |
| `move_dc` | motor, target_counts, max_pwm | Absolute scenery movement |
| `set_rgb_light` | light, red, green, blue | Set one daisy-chain module; values 0–255 |
| `set_all_rgb_lights` | red, green, blue | Set all front-light modules together |
| `stop_all` | none | Controlled software stop |
| `get_state` | none | Bit-field: armed, E-stop, watchdog fault |
| `get_encoder` | motor | Encoder position |
| `get_dc_command` | motor | Signed live PWM command for direction monitoring |

## What must be calibrated later

- Servo safe angles and pulse widths.
- X/Y travel in steps for the 36 × 24 inch theater.
- Curtain travel and direction.
- DC encoder counts for each scene position.
- Stepper speeds and acceleration profile.
- Mechanical home/limit switches.
- SM16823E current gain, module cooling, aiming, white balance, and final chain count.
- Audio device, microphone behavior, and display model.

This is a safe architectural starting point, not a final wiring-approved machine configuration.
