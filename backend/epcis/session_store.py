import random
import string
from dataclasses import dataclass

from models import EventSession

LGTIN_GTIN_1 = "04047111793267"
LGTIN_GTIN_2 = "04047111288459"
DESADV_PREFIX = "40471113333333"
PO_PREFIX = "40471112222221"
LOT_CHARS = string.digits + string.ascii_lowercase

EVENT_TIME_ZONE_OFFSET = "+02:00"

_sessions: dict[str, "_StoredSession"] = {}


@dataclass
class _StoredSession:
    sscc: str
    lgtin1: str | None = None
    lgtin2: str | None = None
    po: str | None = None
    desadv: str | None = None


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


def step_needs_material(step_number: int) -> bool:
    return step_number in {1, 3, 4, 5, 7}
