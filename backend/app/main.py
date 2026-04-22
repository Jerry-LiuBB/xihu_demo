from __future__ import annotations

import uuid
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import (
    ApiErrorResponse,
    ErrorCode,
    PersonDecisionRequest,
    PersonDecisionResponse,
    SpeechPlayRequest,
    SpeechPlayResponse,
    SpeechStatusResponse,
    SpeechStopResponse,
)
from .services.decision import DecisionService
from .services.speech_adapter import SpeechBusyError, SpeechModuleAdapter
from .services.yolo_caller import YoloServiceCaller, YoloServiceError

app = FastAPI(title="xihu demo backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

speech_adapter = SpeechModuleAdapter()
yolo_caller = YoloServiceCaller()
decision_service = DecisionService(confidence_threshold=0.5)

detect_lock = None


@app.on_event("startup")
async def startup() -> None:
    global detect_lock
    import asyncio

    detect_lock = asyncio.Lock()


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - start) * 1000, 2)
    response.headers["x-request-id"] = request_id
    response.headers["x-duration-ms"] = str(duration_ms)
    return response


@app.post("/api/detect/person-decision", response_model=PersonDecisionResponse)
async def person_decision(req: PersonDecisionRequest, request: Request) -> PersonDecisionResponse:
    if detect_lock.locked():
        raise HTTPException(status_code=409, detail={"code": "DETECT_BUSY", "message": "detect in progress"})

    async with detect_lock:
        try:
            yolo_result = await yolo_caller.fetch_latest_detections()
        except YoloServiceError as exc:
            raise HTTPException(
                status_code=502,
                detail=ApiErrorResponse(code=ErrorCode.MODEL_SERVICE_ERROR, message=str(exc)).model_dump(),
            )

        result = decision_service.make_person_decision(yolo_result, req.person_ratio_threshold)
        return PersonDecisionResponse(result=result)


@app.post("/api/speech/play", response_model=SpeechPlayResponse)
async def speech_play(req: SpeechPlayRequest) -> SpeechPlayResponse:
    try:
        state = await speech_adapter.play(req.text)
        return SpeechPlayResponse(success=True, request_status=state)
    except SpeechBusyError:
        raise HTTPException(
            status_code=409,
            detail=ApiErrorResponse(code=ErrorCode.SPEECH_BUSY, message="speech is busy").model_dump(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=ApiErrorResponse(code=ErrorCode.SPEECH_EXEC_ERROR, message=str(exc)).model_dump(),
        )


@app.post("/api/speech/stop", response_model=SpeechStopResponse)
async def speech_stop() -> SpeechStopResponse:
    state = await speech_adapter.stop()
    return SpeechStopResponse(success=True, request_status=state)


@app.get("/api/speech/status", response_model=SpeechStatusResponse)
async def speech_status() -> SpeechStatusResponse:
    state = await speech_adapter.status()
    return SpeechStatusResponse(status=state.value)


app.mount("/ui", StaticFiles(directory="frontend", html=True), name="ui")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")
