from pathlib import Path

from config import EPCIS_TEMPLATES_DIR, get_settings
from epcis.generator import DOCUMENT_TEMPLATE_PATH
from epcis.steps import STEPS


def check_readiness() -> tuple[bool, list[str]]:
    issues: list[str] = []
    settings = get_settings()

    if not settings.epcat_base_url:
        issues.append("EPCAT_BASE_URL is not configured")

    if not EPCIS_TEMPLATES_DIR.is_dir():
        issues.append(f"EPCIS templates directory missing: {EPCIS_TEMPLATES_DIR}")
    else:
        if not DOCUMENT_TEMPLATE_PATH.is_file():
            issues.append(f"Missing EPCIS document template: {DOCUMENT_TEMPLATE_PATH.name}")
        for step in STEPS.values():
            for template_file in step.template_files:
                template_path = EPCIS_TEMPLATES_DIR / template_file
                if not template_path.is_file():
                    issues.append(f"Missing template: {template_file}")

    output_dir = settings.events_dir
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".ready"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as error:
        issues.append(f"Output directory not writable: {output_dir} ({error})")

    return len(issues) == 0, issues
