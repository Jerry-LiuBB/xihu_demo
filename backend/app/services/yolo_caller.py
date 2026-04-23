from __future__ import annotations

import os
from typing import Any

import httpx


class YoloServiceError(RuntimeError):
    pass


class YoloServiceCaller:
    """Backend-internal caller for resident YOLO service on Orin."""

    def __init__(self, base_url: str | None = None, timeout_sec: float = 1.5) -> None:
        self.base_url = base_url or os.getenv("YOLO_SERVICE_URL", "http://127.0.0.1:8090")
        self.timeout_sec = timeout_sec

    async def fetch_latest_detections(self) -> dict[str, Any]:
        url = f"{self.base_url}/detect/latest"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise YoloServiceError("YOLO service timeout") from exc
        except httpx.HTTPError as exc:
            raise YoloServiceError("YOLO service unreachable") from exc
        except ValueError as exc:
            raise YoloServiceError("YOLO response JSON invalid") from exc

        if not isinstance(payload, dict):
            raise YoloServiceError("YOLO response format invalid")
        if "detections" not in payload:
            raise YoloServiceError("YOLO response missing detections")
        return payload
