import json
import logging

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


def capture_url() -> str:
    settings = get_settings()
    if not settings.epcat_base_url:
        raise ValueError("EPCAT_BASE_URL is not configured")
    return f"{settings.epcat_base_url.rstrip('/')}/capture"


def _format_response_body(response: httpx.Response) -> str:
    try:
        return json.dumps(response.json(), indent=2, ensure_ascii=False)
    except ValueError:
        return response.text


def send_to_capture(document: dict) -> None:
    url = capture_url()
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=document)
        response.raise_for_status()

    logger.info(
        "EPCIS capture response from %s: status=%s\n%s",
        url,
        response.status_code,
        _format_response_body(response),
    )
