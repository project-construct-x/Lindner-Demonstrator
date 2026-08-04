#!/usr/bin/env python3
"""Run the EPCIS-to-AAS pipeline, then map values into the prepared submodel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .basyx_components import sme
from .basyx_components.pipeline_log import PipelineLog
from .basyx_components import sm_server


DEFAULT_AAS_ENVIRONMENT = "http://132.195.160.222:8081"
DEFAULT_LOG_FILE = Path(__file__).with_suffix(".log")


def map_event_to_aas(
    epcis_event: dict,
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: PipelineLog | None = None,
) -> dict:
    if log:
        log.step("start EPCIS-to-AAS pipeline")
    target = sm_server.ensure_event_submodel(epcis_event, aas_environment, log)
    if target["status"] == "skipped":
        if log:
            log.step("pipeline finished: skipped")
        return target

    result = sme.map_event(
        epcis_event,
        target["submodel_id"],
        target["sml_path"],
        aas_environment,
        log,
    )
    result["aas_id"] = target["aas_id"]
    result["submodel_id"] = target["submodel_id"]
    if log:
        log.step("pipeline finished: mapped")
    return result


def events(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [event for event in payload if isinstance(event, dict)]
    if not isinstance(payload, dict):
        return []
    if payload.get("eventID") or payload.get("epcList"):
        return [payload]

    body = payload.get("epcisBody", {})
    direct_events = body.get("eventList", [])
    query_events = (
        body.get("queryResults", {})
        .get("resultsBody", {})
        .get("eventList", [])
    )
    found = direct_events or query_events
    return [event for event in found if isinstance(event, dict)]


def map_payload_to_aas(
    payload: object,
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: PipelineLog | None = None,
) -> list[dict]:
    results = []
    found = events(payload)
    if log:
        log.data("event_count", len(found))
    for event in found:
        try:
            results.append(map_event_to_aas(event, aas_environment, log))
        except Exception as exc:
            if log:
                log.step("event failed; continue with next event")
                log.data("event_id", event.get("eventID"))
                log.data("error", str(exc))
            results.append(
                {
                    "status": "error",
                    "event_id": event.get("eventID"),
                    "error": str(exc),
                }
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_json")
    parser.add_argument("--aas-environment", default=DEFAULT_AAS_ENVIRONMENT)
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--quiet-log", action="store_true")
    args = parser.parse_args()

    log = PipelineLog(args.log_file, echo=not args.quiet_log)
    event = sme.load_event(args.event_json)
    log.data("event_file", args.event_json)
    log.data("aas_environment", args.aas_environment)
    result = map_event_to_aas(event, args.aas_environment, log)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
