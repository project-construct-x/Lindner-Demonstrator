import random
import string
from dataclasses import dataclass, field

from epcis.steps import get_step_by_number
from models import EventSession

LGTIN_GTIN_1 = "04047111793267"
LGTIN_GTIN_2 = "04047111288459"
DESADV_PREFIX = "40471113333333"
PO_PREFIX = "40471112222221"
LOT_CHARS = string.digits + string.ascii_lowercase

EVENT_TIME_ZONE_OFFSET = "+02:00"
MAX_STEP_NUMBER = 7

_sessions: dict[str, "_StoredSession"] = {}


@dataclass
class _StoredSession:
    sscc: str
    lgtin1: str | None = None
    lgtin2: str | None = None
    po: str | None = None
    desadv: str | None = None
    completed_steps: set[int] = field(default_factory=set)


def _random_token(length: int) -> str:
    return "".join(random.choice(LOT_CHARS) for _ in range(length))


def _to_lgtin(gtin: str, lot: str) -> str:
    return f"https://id.gs1.org/01/{gtin}/10/{lot}"


def _generate_biz_transaction(prefix: str) -> str:
    return f"https://id.gs1.org/253/{prefix}{_random_token(10)}"


def ensure_material_fields(sscc: str) -> None:
    session = _sessions.setdefault(sscc, _StoredSession(sscc=sscc))
    if session.lgtin1 is not None:
        return

    lot = _random_token(4)
    session.lgtin1 = _to_lgtin(LGTIN_GTIN_1, lot)
    session.lgtin2 = _to_lgtin(LGTIN_GTIN_2, lot)
    session.po = _generate_biz_transaction(PO_PREFIX)


def ensure_desadv(sscc: str) -> None:
    session = _sessions.setdefault(sscc, _StoredSession(sscc=sscc))
    if session.desadv is not None:
        return

    session.desadv = _generate_biz_transaction(DESADV_PREFIX)


def get_session(sscc: str) -> EventSession:
    stored = _sessions.setdefault(sscc, _StoredSession(sscc=sscc))
    return EventSession(
        sscc=stored.sscc,
        lgtin1=stored.lgtin1 or "",
        lgtin2=stored.lgtin2 or "",
        desadv=stored.desadv or "",
        po=stored.po or "",
    )


def get_completed_steps(sscc: str) -> list[int]:
    session = _sessions.get(sscc)
    if session is None:
        return []
    return sorted(session.completed_steps)


def get_sscc_snapshot(sscc: str) -> dict:
    completed_steps = get_completed_steps(sscc)
    completed_step_ids = []
    for step_number in completed_steps:
        step = get_step_by_number(step_number)
        if step is not None:
            completed_step_ids.append(step.id)

    return {
        "sscc": sscc,
        "completed_steps": completed_steps,
        "completed_step_ids": completed_step_ids,
    }


def validate_step_can_run(sscc: str, step_number: int) -> None:
    if step_number < 1 or step_number > MAX_STEP_NUMBER:
        raise ValueError(f"Step number must be between 1 and {MAX_STEP_NUMBER}")

    session = _sessions.get(sscc)

    if step_number == 1:
        if session is not None and 1 in session.completed_steps:
            raise ValueError("Step 1 was already completed for this SSCC")
        return

    if session is None or not session.completed_steps:
        raise ValueError(
            f"SSCC has no completed steps. Trigger step 1 before step {step_number}."
        )

    required_previous_step = step_number - 1
    if required_previous_step not in session.completed_steps:
        raise ValueError(
            f"Step {required_previous_step} must be completed before step {step_number}."
        )

    if step_number in session.completed_steps:
        raise ValueError(f"Step {step_number} was already completed for this SSCC")


def mark_step_completed(sscc: str, step_number: int) -> None:
    session = _sessions.setdefault(sscc, _StoredSession(sscc=sscc))
    session.completed_steps.add(step_number)


def step_needs_material(step_number: int) -> bool:
    return step_number in {1, 3, 4, 5, 7}
