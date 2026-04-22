import unittest

try:
    from pydantic import ValidationError
    from backend.app.models import ArmRunTrajectoryRequest
except ModuleNotFoundError:  # pragma: no cover - local env without deps
    ValidationError = Exception
    ArmRunTrajectoryRequest = None


@unittest.skipIf(ArmRunTrajectoryRequest is None, "pydantic not installed in current env")
class ArmModelsTests(unittest.TestCase):
    def test_arm_request_ok(self):
        req = ArmRunTrajectoryRequest(arm_ip="192.168.1.18", trajectory_name="123")
        self.assertEqual(req.arm_port, 8080)

    def test_arm_request_empty_ip(self):
        with self.assertRaises(ValidationError):
            ArmRunTrajectoryRequest(arm_ip="", trajectory_name="123")


if __name__ == "__main__":
    unittest.main()
