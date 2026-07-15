import json
import logging
import re
from string import Template
from pathlib import Path

from config import EPCIS_TEMPLATES_DIR, EVENTS_DIR
from epcis.steps import Step
from models import EventSession, StepContext

logger = logging.getLogger(__name__)

SSCC_URI_PATTERN = re.compile(r"^https://id\.gs1\.org/00/\d{18}$")
EVENT_TIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
)
EVENT_TIMEZONE_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")
EVENT_ID_PATTERN = re.compile(
    r"^urn:uuid:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
LGTIN_URI_PATTERN = re.compile(
    r"^https://id\.gs1\.org/01/\d{14}/10/[0-9a-z]+$"
)
DESADV_URI_PATTERN = re.compile(r"^https://id\.gs1\.org/253/.+$")


def validate_sscc(sscc: str) -> None:
    if not SSCC_URI_PATTERN.match(sscc):
        raise ValueError(
            "SSCC must be a GS1 Digital Link URI: https://id.gs1.org/00/{18-digit-sscc}"
        )


def validate_session(session: EventSession) -> None:
    validate_sscc(session.sscc)
    for lgtin in (session.lgtin1, session.lgtin2, session.lgtin3):
        if not LGTIN_URI_PATTERN.match(lgtin):
            raise ValueError(
                "LGTIN must be a GS1 Digital Link URI: https://id.gs1.org/01/{gtin}/10/{lot}"
            )
    if not DESADV_URI_PATTERN.match(session.desadv):
        raise ValueError(
            "desadv must be a GS1 Digital Link URI: https://id.gs1.org/253/{reference}"
        )


def validate_step_context(step: StepContext) -> None:
    if not EVENT_TIME_PATTERN.match(step.eventTime):
        raise ValueError("eventTime must be ISO 8601 UTC with milliseconds, e.g. 2026-04-16T14:04:53.369Z")
    if not EVENT_TIMEZONE_PATTERN.match(step.eventTimeZoneOffset):
        raise ValueError("eventTimeZoneOffset must be like +02:00 or -05:00")
    if not EVENT_ID_PATTERN.match(step.eventID):
        raise ValueError("eventID must be urn:uuid:{uuid}")


def sscc_folder_name(sscc: str) -> str:
    return sscc.rsplit("/00/", maxsplit=1)[-1]


def _template_variables(session: EventSession, step: StepContext) -> dict[str, str]:
    return {
        "sscc": session.sscc,
        "lgtin1": session.lgtin1,
        "lgtin2": session.lgtin2,
        "lgtin3": session.lgtin3,
        "desadv": session.desadv,
        "eventTime": step.eventTime,
        "eventTimeZoneOffset": step.eventTimeZoneOffset,
        "eventID": step.eventID,
    }


def render_template(template_path: Path, variables: dict[str, str]) -> dict:
    template_text = template_path.read_text(encoding="utf-8")
    rendered = Template(template_text).substitute(variables)
    event = json.loads(rendered)
    if not isinstance(event, dict):
        raise ValueError(f"Template must render to a JSON object: {template_path.name}")
    return event


def generate_event(
    step: Step,
    session: EventSession,
    step_context: StepContext,
) -> tuple[dict, Path]:
    validate_session(session)
    validate_step_context(step_context)

    template_path = EPCIS_TEMPLATES_DIR / step.template_file
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {step.template_file}")

    variables = _template_variables(session, step_context)
    event = render_template(template_path, variables)

    sscc_dir = EVENTS_DIR / sscc_folder_name(session.sscc)
    sscc_dir.mkdir(parents=True, exist_ok=True)

    event_file = sscc_dir / f"{step.id}.json"
    with event_file.open("w", encoding="utf-8") as output_file:
        json.dump(event, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    logger.info(
        "Generated EPCIS event for step=%s sscc=%s file=%s\n%s",
        step.id,
        session.sscc,
        event_file,
        json.dumps(event, indent=2, ensure_ascii=False),
    )

    return event, event_file
