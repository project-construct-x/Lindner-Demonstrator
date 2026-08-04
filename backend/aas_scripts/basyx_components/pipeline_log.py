from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class PipelineLog:
    def __init__(self, path: str | Path, echo: bool = True) -> None:
        self.path = Path(path)
        self.echo = echo
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def write(self, message: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat()} | {message}"
        with self.path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")
        if self.echo:
            print(line)

    def step(self, message: str) -> None:
        self.write(f"STEP | {message}")

    def http(self, method: str, url: str, reason: str) -> None:
        self.write(f"HTTP | {method} {url} | {reason}")

    def data(self, name: str, value: object) -> None:
        self.write(f"DATA | {name}={value}")
