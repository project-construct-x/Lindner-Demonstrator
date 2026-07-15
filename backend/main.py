import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from epcis.generator import generate_event
from epcis.steps import get_step
from models import TriggerRequest, TriggerResponse

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Construct-X Demonstrator API",
    description="Generates EPCIS events from templates for GS1 SSCC lifecycle steps.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/trigger/{step_id}", response_model=TriggerResponse)
def trigger(step_id: str, body: TriggerRequest) -> TriggerResponse:
    step = get_step(step_id)
    if step is None:
        raise HTTPException(status_code=404, detail=f"Unknown step: {step_id}")

    try:
        _, event_file = generate_event(step, body.sscc)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    return TriggerResponse(
        step_id=step.id,
        sscc=body.sscc,
        event_file=event_file.name,
    )
