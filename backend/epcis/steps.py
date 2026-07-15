from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    id: str
    label: str
    template_file: str


STEPS: dict[str, Step] = {
    "ausgang-hersteller": Step(
        id="ausgang-hersteller",
        label="Ausgang beim Hersteller",
        template_file="04.json",
    ),
    "baustellen-eingang": Step(
        id="baustellen-eingang",
        label="Baustellen-Eingang",
        template_file="05.json",
    ),
    "einbau": Step(
        id="einbau",
        label="Einbau",
        template_file="06b.json",
    ),
    "rueckbau": Step(
        id="rueckbau",
        label="Rückbau",
        template_file="07a.json",
    ),
    "ausgang-baustelle": Step(
        id="ausgang-baustelle",
        label="Ausgang Baustelle",
        template_file="08.json",
    ),
    "eingang-hersteller": Step(
        id="eingang-hersteller",
        label="Eingang beim Hersteller",
        template_file="09.json",
    ),
    "aufbereitung": Step(
        id="aufbereitung",
        label="Aufbereitung",
        template_file="01.json",
    ),
}


def get_step(step_id: str) -> Step | None:
    return STEPS.get(step_id)
