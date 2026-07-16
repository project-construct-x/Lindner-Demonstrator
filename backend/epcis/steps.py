from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    id: str
    label: str
    template_files: tuple[str, ...]
    number: int


STEPS: dict[str, Step] = {
    "ausgang-hersteller": Step(
        id="ausgang-hersteller",
        label="Ausgang beim Hersteller",
        template_files=("01.json", "02a.json", "03.json", "04.json"),
        number=1,
    ),
    "baustellen-eingang": Step(
        id="baustellen-eingang",
        label="Baustellen-Eingang",
        template_files=("05.json",),
        number=2,
    ),
    "einbau": Step(
        id="einbau",
        label="Einbau",
        template_files=("06a.json", "06b.json"),
        number=3,
    ),
    "rueckbau": Step(
        id="rueckbau",
        label="Rückbau",
        template_files=("07a.json",),
        number=4,
    ),
    "ausgang-baustelle": Step(
        id="ausgang-baustelle",
        label="Ausgang Baustelle",
        template_files=("07b.json", "08.json"),
        number=5,
    ),
    "eingang-hersteller": Step(
        id="eingang-hersteller",
        label="Eingang beim Hersteller",
        template_files=("09.json",),
        number=6,
    ),
    "aufbereitung": Step(
        id="aufbereitung",
        label="Aufbereitung",
        template_files=("02b.json",),
        number=7,
    ),
}


def get_step(step_id: str) -> Step | None:
    return STEPS.get(step_id)
