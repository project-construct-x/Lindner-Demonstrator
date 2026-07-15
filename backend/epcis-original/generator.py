import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from config import EPCIS_TEMPLATES_DIR, EVENTS_DIR
from epcis.steps import Step

logger = logging.getLogger(__name__)

SSCC_URI_PATTERN = re.compile(r"^https://id\.gs1\.org/00/\d{18}$")
TEMPLATE_SSCC_PATTERN = re.compile(r"^https://id\.gs1\.org/00/\d+$")


def validate_sscc(sscc: str) -> None:
    if not SSCC_URI_PATTERN.match(sscc):
        raise ValueError(
            "SSCC must be a GS1 Digital Link URI: https://id.gs1.org/00/{18-digit-sscc}"
        )


def sscc_folder_name(sscc: str) -> str:
    return sscc.rsplit("/00/", maxsplit=1)[-1]


def _replace_sscc_values(value: object, sscc: str) -> object:
    if isinstance(value, dict):
        return {key: _replace_sscc_values(item, sscc) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_sscc_values(item, sscc) for item in value]
    if isinstance(value, str) and TEMPLATE_SSCC_PATTERN.match(value):
        return sscc
    return value


def _refresh_event_metadata(event: dict) -> None:
    now = datetime.now(timezone.utc)
    event["eventTime"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    event["eventID"] = f"urn:uuid:{uuid4()}"


def generate_event(step: Step, sscc: str) -> tuple[dict, Path]:
    validate_sscc(sscc)

    template_path = EPCIS_TEMPLATES_DIR / step.template_file
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found: {step.template_file}")

    with template_path.open(encoding="utf-8") as template_file:
        event = json.load(template_file)

    event = _replace_sscc_values(deepcopy(event), sscc)
    if isinstance(event, dict):
        _refresh_event_metadata(event)

    sscc_dir = EVENTS_DIR / sscc_folder_name(sscc)
    sscc_dir.mkdir(parents=True, exist_ok=True)

    event_file = sscc_dir / f"{step.id}.json"
    with event_file.open("w", encoding="utf-8") as output_file:
        json.dump(event, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")

    logger.info(
        "Generated EPCIS event for step=%s sscc=%s file=%s\n%s",
        step.id,
        sscc,
        event_file,
        json.dumps(event, indent=2, ensure_ascii=False),
    )

    return event, event_file
