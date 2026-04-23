from __future__ import annotations

import asyncio
import json


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

    async def send_run_trajectory(
        self,
        arm_ip: str,
        trajectory_name: str,
        arm_port: int = 8080,
        timeout_sec: float = 2.0,
    ) -> None:
        command = self.build_run_trajectory_command(trajectory_name)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(arm_ip, arm_port),
                timeout=timeout_sec,
            )
            writer.write(command.encode("utf-8"))
            await asyncio.wait_for(writer.drain(), timeout=timeout_sec)
            writer.close()
            await writer.wait_closed()
        except Exception as exc:
            raise ArmSocketError(f"socket send failed: {exc}") from exc
