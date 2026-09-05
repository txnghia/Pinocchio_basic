"""High-level theater configuration; hardware pin mapping lives on the MCU."""

SERVO = {
    "head": 0,
    "left_arm_lift": 1,
    "right_arm_lift": 2,
    "left_hand_wave": 3,
    "right_hand_wave": 4,
    "left_leg": 5,
    "right_leg": 6,
    "puppet_z": 7,
}

STEPPER = {"x": 0, "y": 1, "curtain": 2}
SCENERY_MOTOR = {"left": 0, "right": 1}
STAGE_LIGHT_COUNT = 6

# Conservative software limits. Replace these after measuring the mechanisms.
SERVO_LIMITS = {name: (20, 160) for name in SERVO}
STEPPER_LIMITS = {
    "x": (-20_000, 20_000),
    "y": (-10_000, 10_000),
    "curtain": (-15_000, 15_000),
}
SCENERY_LIMITS = {"left": (-100_000, 100_000), "right": (-100_000, 100_000)}

HEARTBEAT_SECONDS = 0.5
DEFAULT_CUE_FILE = "cues.json"
