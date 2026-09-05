import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from theater import ShowError, TheaterController


class FakeBridge:
    def __init__(self):
        self.calls = []

    def call(self, method, *args):
        self.calls.append((method, args))
        return 1 if method == "arm_system" else 0


class TheaterTests(unittest.TestCase):
    def setUp(self):
        self.bridge = FakeBridge()
        self.theater = TheaterController(self.bridge, lambda _: None)

    def test_servo_name_maps_to_channel(self):
        self.theater.servo("head", 90, 500)
        self.assertEqual(self.bridge.calls[-1], ("set_servo", (0, 90, 500)))

    def test_servo_limit_is_enforced(self):
        with self.assertRaises(ShowError):
            self.theater.servo("head", 180)

    def test_rgb_light_maps_to_new_mcu_service(self):
        self.theater.rgb_light(5, 255, 128, 0)
        self.assertEqual(self.bridge.calls[-1], ("set_rgb_light", (5, 255, 128, 0)))

    def test_rgb_light_index_is_enforced(self):
        with self.assertRaises(ShowError):
            self.theater.rgb_light(6, 255, 255, 255)

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(ShowError):
            self.theater.execute({"type": "teleport"})


if __name__ == "__main__":
    unittest.main()
