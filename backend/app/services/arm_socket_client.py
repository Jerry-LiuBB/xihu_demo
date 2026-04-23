from __future__ import annotations

import asyncio
import json
import socket


class ArmSocketError(RuntimeError):
    pass


class ArmSocketClient:
    """Simple TCP socket sender for robotic arm JSON commands."""

    @staticmethod
    def build_run_trajectory_command(trajectory_name: str) -> str:
        payload = {
            "command": "set_run_trajectory_file",
            "name": trajectory_name,
        }
        # keep exact compact JSON format like:
        # {"command":"set_run_trajectory_file","name":"1"}
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def build_run_trajectory_wire_message(cls, trajectory_name: str) -> bytes:
        # arm controller requires CRLF terminated line protocol
        return (cls.build_run_trajectory_command(trajectory_name) + "\r\n").encode("utf-8")

    async def send_run_trajectory(
        self,
        arm_ip: str,
        trajectory_name: str,
        arm_port: int = 8080,
        timeout_sec: float = 2.0,
    ) -> None:
        command = self.build_run_trajectory_command(trajectory_name)
        wire_message = self.build_run_trajectory_wire_message(trajectory_name)

        try:
            await asyncio.to_thread(
                self._send_once,
                arm_ip,
                arm_port,
                wire_message,
                timeout_sec,
            )
        except Exception as first_exc:
            # retry once for transient network jitter
            try:
                await asyncio.sleep(0.1)
                await asyncio.to_thread(
                    self._send_once,
                    arm_ip,
                    arm_port,
                    wire_message,
                    timeout_sec,
                )
            except Exception as second_exc:
                raise ArmSocketError(
                    f"socket send failed to {arm_ip}:{arm_port}, "
                    f"command={command}, first_error={first_exc}, retry_error={second_exc}"
                ) from second_exc

    @staticmethod
    def _send_once(arm_ip: str, arm_port: int, wire_message: bytes, timeout_sec: float) -> None:
        with socket.create_connection((arm_ip, arm_port), timeout=timeout_sec) as sock:
            sock.sendall(wire_message)
