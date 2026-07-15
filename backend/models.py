from pydantic import BaseModel, Field


class TriggerRequest(BaseModel):
    sscc: str = Field(
        ...,
        description="GS1 Digital Link URI for the SSCC",
        examples=["https://id.gs1.org/00/006141411234567890"],
    )


class TriggerResponse(BaseModel):
    step_id: str
    sscc: str
    event_file: str
