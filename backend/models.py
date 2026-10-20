from pydantic import BaseModel, Field


class EventSession(BaseModel):
    sscc: str = Field(
        ...,
        description="GS1 Digital Link URI for the SSCC (stable for the whole session)",
        examples=["https://id.gs1.org/00/040471116815749833"],
    )
    lgtin1: str = Field(
        ...,
        description="GS1 Digital Link URI for the first material class (GTIN + lot)",
        examples=["https://id.gs1.org/01/04047111100751/10/a1b2"],
    )
    lgtin2: str = Field(
        ...,
        description="GS1 Digital Link URI for the second material class (GTIN + lot)",
        examples=["https://id.gs1.org/01/04047111100768/10/c3d4"],
    )
    desadv: str = Field(
        ...,
        description="GS1 Digital Link URI for the despatch advice business transaction",
        examples=["https://id.gs1.org/253/40471112d3e4s4d5v"],
    )
    po: str = Field(
        ...,
        description="GS1 Digital Link URI for the purchase order business transaction",
        examples=["https://id.gs1.org/253/40471110a2b3c4d5f"],
    )


class TriggerRequest(BaseModel):
    sscc: str = Field(
        ...,
        description="GS1 Digital Link URI for the SSCC (stable for the whole session)",
        examples=["https://id.gs1.org/00/040471116815749833"],
    )


class TriggerResponse(BaseModel):
    step_id: str
    sscc: str
    document_file: str
    event_count: int


class SsccSnapshot(BaseModel):
    sscc: str
    completed_steps: list[int]
    completed_step_ids: list[str]


class StepCompletedEvent(BaseModel):
    sscc: str
    step_number: int
    step_id: str
    step_label: str
    document_file: str
    event_count: int
    completed_steps: list[int]
    completed_step_ids: list[str]
