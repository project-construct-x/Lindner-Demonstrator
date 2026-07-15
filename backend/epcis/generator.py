import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from string import Template
from pathlib import Path
from uuid import uuid4

from config import EPCIS_TEMPLATES_DIR, EVENTS_DIR
from epcis.steps import Step
from models import EventSession, StepContext

logger = logging.getLogger(__name__)

SSCC_URI_PATTERN = re.compile(r"^https://id\.gs1\.org/00/\d{18}$")
EVENT_TIMEZONE_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")
LGTIN_URI_PATTERN = re.compile(
    r"^https://id\.gs1\.org/01/\d{14}/10/[0-9a-z]+$"
)
DESADV_URI_PATTERN = re.compile(r"^https://id\.gs1\.org/253/.+$")


@dataclass(frozen=True)
class _RenderedEventContext:
    eventTime: str
    eventTimeZoneOffset: str
    eventID: str


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
    if not EVENT_TIMEZONE_PATTERN.match(step.eventTimeZoneOffset):
        raise ValueError("eventTimeZoneOffset must be like +02:00 or -05:00")


def sscc_folder_name(sscc: str) -> str:
    return sscc.rsplit("/00/", maxsplit=1)[-1]


def _format_event_time(value: datetime) -> str:
    utc_value = value.astimezone(timezone.utc)
    milliseconds = utc_value.microsecond // 1000
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{milliseconds:03d}Z"


def _event_context_for_template(
    event_time_zone_offset: str,
    template_index: int,
    template_count: int,
    triggered_at: datetime,
) -> _RenderedEventContext:
    event_time = triggered_at
    hours_back = template_count - 1 - template_index
    if hours_back:
        event_time -= timedelta(hours=hours_back)

    return _RenderedEventContext(
        eventTime=_format_event_time(event_time),
        eventTimeZoneOffset=event_time_zone_offset,
        eventID=f"urn:uuid:{uuid4()}",
    )


def _template_variables(
    session: EventSession,
    event_context: _RenderedEventContext,
) -> dict[str, str]:
    return {
        "sscc": session.sscc,
        "lgtin1": session.lgtin1,
        "lgtin2": session.lgtin2,
        "lgtin3": session.lgtin3,
        "desadv": session.desadv,
        "eventTime": event_context.eventTime,
        "eventTimeZoneOffset": event_context.eventTimeZoneOffset,
        "eventID": event_context.eventID,
    }


def render_template(template_path: Path, variables: dict[str, str]) -> dict:
    template_text = template_path.read_text(encoding="utf-8")
    rendered = Template(template_text).substitute(variables)
    event = json.loads(rendered)
    if not isinstance(event, dict):
        raise ValueError(f"Template must render to a JSON object: {template_path.name}")
    return event


def _generate_single_event(
    template_file: str,
    session: EventSession,
    event_context: _RenderedEventContext,
    step_id: str,
    sscc_dir: Path,
) -> tuple[dict, Path]:
    template_path = EPCIS_TEMPLATES_DIR / template_file
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {template_file}")

    variables = _template_variables(session, event_context)
    event = render_template(template_path, variables)

    event_name = template_path.stem
    event_file = sscc_dir / f"{event_name}.json"
    with event_file.open("w", encoding="utf-8") as output_file:
        json.dump(event, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    logger.info(
        "Generated EPCIS event for step=%s sscc=%s file=%s\n%s",
        step_id,
        session.sscc,
        event_file,
        json.dumps(event, indent=2, ensure_ascii=False),
    )

    return event, event_file


def generate_step_events(
    step: Step,
    session: EventSession,
    step_context: StepContext,
) -> tuple[list[dict], list[Path]]:
    validate_session(session)
    validate_step_context(step_context)

    sscc_dir = EVENTS_DIR / sscc_folder_name(session.sscc)
    sscc_dir.mkdir(parents=True, exist_ok=True)

    events: list[dict] = []
    event_files: list[Path] = []
    template_count = len(step.template_files)
    triggered_at = datetime.now(timezone.utc)

    for index, template_file in enumerate(step.template_files):
        event_context = _event_context_for_template(
            step_context.eventTimeZoneOffset,
            index,
            template_count,
            triggered_at,
        )
        event, event_file = _generate_single_event(
            template_file,
            session,
            event_context,
            step.id,
            sscc_dir,
        )
        events.append(event)
        event_files.append(event_file)

    return events, event_files
