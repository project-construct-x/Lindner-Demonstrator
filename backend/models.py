from pydantic import BaseModel, Field


class EventSession(BaseModel):
    sscc: str = Field(
        ...,
        description="GS1 Digital Link URI for the SSCC (stable for the whole session)",
        examples=["https://id.gs1.org/00/006141411234567890"],
    )
    lgtin1: str = Field(
        ...,
        description="GS1 Digital Link URI for the first material class (GTIN + lot)",
        examples=["https://id.gs1.org/01/04047111793267/10/a1b2"],
    )
    lgtin2: str = Field(
        ...,
        description="GS1 Digital Link URI for the second material class (GTIN + lot)",
        examples=["https://id.gs1.org/01/04047111288459/10/c3d4"],
    )
    desadv: str = Field(
        ...,
        description="GS1 Digital Link URI for the despatch advice business transaction",
        examples=["https://id.gs1.org/253/40471113333333d3e4s4d5v"],
    )
    po: str = Field(
        ...,
        description="GS1 Digital Link URI for the purchase order business transaction",
        examples=["https://id.gs1.org/253/40471112222221a2b3c4d5f"],
    )


class StepContext(BaseModel):
    eventTimeZoneOffset: str = Field(
        ...,
        description="Local timezone offset for the generated eventTime",
        examples=["+02:00"],
    )


class TriggerRequest(BaseModel):
    session: EventSession
    step: StepContext


class TriggerResponse(BaseModel):
    step_id: str
    sscc: str
    document_file: str
    event_count: int
