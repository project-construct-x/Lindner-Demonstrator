from pathlib import Path

from config import EPCIS_TEMPLATES_DIR, get_settings
from epcis.steps import STEPS


def check_readiness() -> tuple[bool, list[str]]:
    issues: list[str] = []
    settings = get_settings()

    if not EPCIS_TEMPLATES_DIR.is_dir():
        issues.append(f"EPCIS templates directory missing: {EPCIS_TEMPLATES_DIR}")
    else:
        for step in STEPS.values():
            template_path = EPCIS_TEMPLATES_DIR / step.template_file
            if not template_path.is_file():
                issues.append(f"Missing template: {step.template_file}")

    output_dir = settings.events_dir
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".ready"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as error:
        issues.append(f"Output directory not writable: {output_dir} ({error})")

    return len(issues) == 0, issues
