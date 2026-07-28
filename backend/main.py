import asyncio
import logging

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from config import get_settings
from epcis.generator import generate_step_events, validate_sscc
from epcis.session_store import (
    get_sscc_snapshot,
    mark_step_completed,
    validate_step_can_run,
)
from epcis.steps import get_step_by_number
from health import check_readiness
from models import SsccSnapshot, TriggerRequest, TriggerResponse
from subscriptions import (
    HEARTBEAT_INTERVAL_SECONDS,
    format_heartbeat,
    format_sse,
    publish,
    subscribe,
    unsubscribe,
)

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Construct-X Demonstrator API",
    description="Generates EPCIS events from templates for GS1 SSCC lifecycle steps.",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api")


@app.get("/health")
def health() -> Response:
    return Response(content="ok\n", media_type="text/plain")


@app.get("/ready")
def ready() -> Response:
    is_ready, issues = check_readiness()
    if not is_ready:
        return Response(
            content="\n".join(issues) + "\n",
            media_type="text/plain",
            status_code=503,
        )
    return Response(content="ok\n", media_type="text/plain")


@api.get("/sscc/stream")
async def sscc_stream(
    sscc: str = Query(..., description="GS1 Digital Link URI for the SSCC"),
) -> StreamingResponse:
    try:
        validate_sscc(sscc)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    async def event_generator():
        queue = subscribe(sscc)
        try:
            yield format_sse("snapshot", get_sscc_snapshot(sscc))
            while True:
                try:
                    event_type, data = await asyncio.wait_for(
                        queue.get(),
                        timeout=HEARTBEAT_INTERVAL_SECONDS,
                    )
                except asyncio.TimeoutError:
                    yield format_heartbeat()
                    continue

                yield format_sse(event_type, data)
        finally:
            unsubscribe(sscc, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@api.get("/sscc/status", response_model=SsccSnapshot)
def sscc_status(
    sscc: str = Query(..., description="GS1 Digital Link URI for the SSCC"),
) -> SsccSnapshot:
    try:
        validate_sscc(sscc)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    snapshot = get_sscc_snapshot(sscc)
    return SsccSnapshot(**snapshot)


@api.post("/trigger/{step_number}", response_model=TriggerResponse)
async def trigger(step_number: int, body: TriggerRequest) -> TriggerResponse:
    step = get_step_by_number(step_number)
    if step is None:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_number}")

    try:
        validate_sscc(body.sscc)
        validate_step_can_run(body.sscc, step_number)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    try:
        document, document_file = await asyncio.to_thread(
            generate_step_events,
            step,
            body.sscc,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"EPCAT capture endpoint returned {error.response.status_code}",
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail=f"EPCAT capture endpoint unreachable: {error}",
        ) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    mark_step_completed(body.sscc, step_number)

    snapshot = get_sscc_snapshot(body.sscc)
    step_event = {
        "sscc": body.sscc,
        "step_number": step_number,
        "step_id": step.id,
        "step_label": step.label,
        "document_file": document_file.name,
        "event_count": len(document["epcisBody"]["eventList"]),
        "completed_steps": snapshot["completed_steps"],
        "completed_step_ids": snapshot["completed_step_ids"],
    }
    await publish(body.sscc, "step_completed", step_event)

    return TriggerResponse(
        step_id=step.id,
        sscc=body.sscc,
        document_file=document_file.name,
        event_count=len(document["epcisBody"]["eventList"]),
    )


app.include_router(api)
