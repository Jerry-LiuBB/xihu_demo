from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum


class SpeechStatus(str, Enum):
    idle = "idle"
    running = "running"
    stop_requested = "stop_requested"
    stopped = "stopped"
    error = "error"


@dataclass
class SpeechTask:
    text: str
    task: asyncio.Task[None]


class SpeechBusyError(RuntimeError):
    pass


class SpeechModuleAdapter:
    """
    Adapter over existing speech module.
    For demo environment, this simulates async speaking duration.
    Replace `_do_speak_once` with real robot speech invocation.
    """

    def __init__(self) -> None:
        self._status: SpeechStatus = SpeechStatus.idle
        self._current: SpeechTask | None = None
        self._lock = asyncio.Lock()

    async def play(self, text: str) -> str:
        async with self._lock:
            if self._status in {SpeechStatus.running, SpeechStatus.stop_requested}:
                raise SpeechBusyError("speech already running")

            self._status = SpeechStatus.running
            task = asyncio.create_task(self._do_speak_once(text))
            self._current = SpeechTask(text=text, task=task)
            return "accepted"

    async def stop(self) -> str:
        async with self._lock:
            if self._status == SpeechStatus.idle:
                return "idle"
            if self._status == SpeechStatus.stopped:
                return "stopped"
            if self._current and not self._current.task.done():
                self._status = SpeechStatus.stop_requested
                self._current.task.cancel()
                return "stop_requested"
            return "stopped"

    async def status(self) -> SpeechStatus:
        if self._current and self._current.task.done():
            if self._status == SpeechStatus.stop_requested:
                self._status = SpeechStatus.stopped
            elif self._status == SpeechStatus.running:
                self._status = SpeechStatus.idle
            self._current = None
        return self._status

    async def _do_speak_once(self, text: str) -> None:
        try:
            # TODO: replace with real command, e.g. `speak --text ...`
            await asyncio.sleep(max(1.0, min(len(text) * 0.08, 6.0)))
        except asyncio.CancelledError:
            raise
        except Exception:
            self._status = SpeechStatus.error
            raise
