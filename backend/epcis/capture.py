import logging

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


def capture_url() -> str:
    settings = get_settings()
    if not settings.epcat_base_url:
        raise ValueError("EPCAT_BASE_URL is not configured")
    return f"{settings.epcat_base_url.rstrip('/')}/capture"


def send_to_capture(document: dict) -> None:
    url = capture_url()
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=document)
        response.raise_for_status()

    logger.info("Sent EPCIS document to capture endpoint: %s", url)
