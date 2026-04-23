import unittest

from backend.app.services.arm_socket_client import ArmSocketClient


class ArmSocketClientTests(unittest.TestCase):
    def test_build_command_exact_format(self):
        cmd = ArmSocketClient.build_run_trajectory_command("1")
        self.assertEqual(cmd, '{"command":"set_run_trajectory_file","name":"1"}')


if __name__ == "__main__":
    unittest.main()
