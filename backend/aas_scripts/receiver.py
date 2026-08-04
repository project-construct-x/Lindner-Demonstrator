#!/usr/bin/env python3
"""Generic JSON webhook receiver."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable


HOST = "0.0.0.0"
PORT = 8088
PATH = "/epcis-events"
DEFAULT_AAS_ENVIRONMENT = "http://132.195.160.222:8081"
DEFAULT_LOG_FILE = Path(__file__).with_name("receiver-aas-link.log")


def print_payload(payload: Any) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False), flush=True)
    return 1


def aas_link_payload(aas_environment: str, log_file: Path, quiet_log: bool) -> Callable[[Any], int]:
    import aas_link
    from basyx_components.pipeline_log import PipelineLog

    log = PipelineLog(log_file, echo=not quiet_log)

    def on_payload(payload: Any) -> int:
        log.step("received webhook payload")
        results = aas_link.map_payload_to_aas(payload, aas_environment, log)
        print(json.dumps(results, indent=2, ensure_ascii=False), flush=True)
        return len(results)

    return on_payload


def handler(path: str, on_payload: Callable[[Any], int]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path.split("?", 1)[0] != path:
                self.send_response(404)
                self.end_headers()
                return

            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                payload = json.loads(raw.decode("utf-8"))
                count = on_payload(payload)
                print(f"[{datetime.now(timezone.utc).isoformat()}] received {count} event(s)")
            except Exception as exc:
                print(f"receiver failed: {exc}", file=sys.stderr, flush=True)
                self.send_response(500)
                self.end_headers()
                return

            response = json.dumps({"received": count}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, fmt: str, *args: object) -> None:
            print(f"http: {fmt % args}", file=sys.stderr)

    return Handler


def serve(
    on_payload: Callable[[Any], int],
    host: str = HOST,
    port: int = PORT,
    path: str = PATH,
) -> None:
    print(f"listening: http://{host}:{port}{path}")
    server = ThreadingHTTPServer((host, port), handler(path, on_payload))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping")
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Receive JSON webhook payloads and print them.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--path", default=PATH)
    parser.add_argument("--aas-link", action="store_true", help="map received EPCIS events to AAS")
    parser.add_argument("--aas-environment", default=DEFAULT_AAS_ENVIRONMENT)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--quiet-log", action="store_true")
    args = parser.parse_args()

    on_payload = print_payload
    if args.aas_link:
        on_payload = aas_link_payload(args.aas_environment, args.log_file, args.quiet_log)

    serve(on_payload, args.host, args.port, args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
