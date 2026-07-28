import logging

import httpx
from fastapi import APIRouter, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from epcis.generator import generate_step_events
from epcis.steps import get_step_by_number
from health import check_readiness
from models import TriggerRequest, TriggerResponse

settings = get_settings()

logging.basicConfig(level=settings.log_level.upper())

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


@api.post("/trigger/{step_number}", response_model=TriggerResponse)
def trigger(step_number: int, body: TriggerRequest) -> TriggerResponse:
    step = get_step_by_number(step_number)
    if step is None:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_number}")

    try:
        document, document_file = generate_step_events(step, body.sscc)
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

    return TriggerResponse(
        step_id=step.id,
        sscc=body.sscc,
        document_file=document_file.name,
        event_count=len(document["epcisBody"]["eventList"]),
    )


app.include_router(api)
