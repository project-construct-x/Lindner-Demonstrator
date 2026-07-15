import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
EPCIS_TEMPLATES_DIR = BACKEND_DIR / "epcis"
EVENTS_DIR = DATA_DIR / "epcis"
