from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ErrorCode(str, Enum):
    INVALID_PARAM = "INVALID_PARAM"
    MODEL_SERVICE_ERROR = "MODEL_SERVICE_ERROR"
    SPEECH_BUSY = "SPEECH_BUSY"
    SPEECH_EXEC_ERROR = "SPEECH_EXEC_ERROR"
    ARM_SOCKET_ERROR = "ARM_SOCKET_ERROR"


class PersonDecisionRequest(BaseModel):
    person_ratio_threshold: float = Field(..., ge=0.0, le=1.0)


class PersonDecisionResponse(BaseModel):
    result: bool


class SpeechPlayRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must be non-empty")
        if len(stripped) > 50:
            raise ValueError("text length must be <= 50")
        return stripped


class SpeechPlayResponse(BaseModel):
    success: bool
    request_status: Literal["accepted", "busy", "error"]


class SpeechStopResponse(BaseModel):
    success: bool
    request_status: Literal["stop_requested", "stopped", "idle", "error"]


class SpeechStatusResponse(BaseModel):
    status: Literal["idle", "running", "stop_requested", "stopped", "error"]


class ApiErrorResponse(BaseModel):
    code: ErrorCode
    message: str


class ArmRunTrajectoryRequest(BaseModel):
    arm_ip: str
    trajectory_name: str
    arm_port: int = Field(default=8080, ge=1, le=65535)
    timeout_sec: float = Field(default=2.0, gt=0.1, le=10.0)

    @field_validator("arm_ip", "trajectory_name")
    @classmethod
    def not_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must be non-empty")
        return stripped


class ArmRunTrajectoryResponse(BaseModel):
    success: bool
    request_status: Literal["sent", "error"]
