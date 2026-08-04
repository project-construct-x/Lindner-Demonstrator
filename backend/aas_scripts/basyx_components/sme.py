#!/usr/bin/env python3
"""Map an EPCIS event into the last existing SMC of a SubmodelElementList."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote


DEFAULT_AAS_ENVIRONMENT = "http://132.195.160.222:8081"
TIMEOUT = 30


def b64url(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def http_json(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    log: Any | None = None,
    reason: str = "",
) -> Any:
    if log:
        log.http(method, url, reason)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as exc:
        text = exc.read().decode(errors="replace")
        if log:
            log.data("http_error_status", exc.code)
            log.data("http_error_body", text)
        raise


def find_co2e(event: dict[str, Any]) -> Any:
    for sensor_element in event.get("sensorElementList", []):
        for report in sensor_element.get("sensorReport", []):
            if report.get("cx:property") == "co2e":
                return report["value"]
    raise ValueError("missing co2e")


def value_id_for_biz_step(biz_step: str) -> dict[str, Any]:
    return {
        "type": "ExternalReference",
        "keys": [
            {
                "type": "GlobalReference",
                "value": f"https://ref.gs1.org/cbv/BizStep-{biz_step}",
            }
        ],
    }


def child(element: dict[str, Any], id_short: str) -> dict[str, Any]:
    for item in element["value"]:
        if item.get("idShort") == id_short:
            return item
    raise ValueError(f"missing {id_short}")


def find_child(element: dict[str, Any], id_short: str) -> dict[str, Any] | None:
    for item in element.get("value", []):
        if item.get("idShort") == id_short:
            return item
    return None


def update_full_smc(smc: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    source_event_id = child(smc, "SourceEventId")
    source_event_id["value"] = event["eventID"]

    business_step = child(smc, "BusinessStep")
    business_step["value"] = event["bizStep"]
    business_step["valueId"] = value_id_for_biz_step(event["bizStep"])

    environmental_impact = child(smc, "EnvironmentalImpact")
    co2e = child(environmental_impact, "CO2e")
    co2e["value"] = str(find_co2e(event))
    return smc


def event_exists(values: list[dict[str, Any]], event_id: str) -> bool:
    for entry in values:
        for item in entry.get("value", []):
            if item.get("idShort") == "SourceEventId" and item.get("value") == event_id:
                return True
    return False


def payload_for(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "SourceEventId": event["eventID"],
        "BusinessStep": event["bizStep"],
        "EnvironmentalImpact": {
            "CO2e": find_co2e(event),
        },
    }


def map_event(
    epcis_event: dict[str, Any],
    submodel_id: str,
    sml_path: str,
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: Any | None = None,
) -> dict[str, Any]:
    base = aas_environment.rstrip("/")
    submodel = b64url(submodel_id)
    if log:
        log.step("map EPCIS event into last existing SMC")
        log.data("submodel_id", submodel_id)
        log.data("sml_path", sml_path)
    sml = http_json(
        "GET",
        f"{base}/submodels/{submodel}/submodel-elements/{quote(sml_path, safe='')}",
        log=log,
        reason="read SubmodelElementList before choosing last SMC",
    )
    sml = sml.get("result", sml)
    values = sml["value"]

    if event_exists(values, epcis_event["eventID"]):
        if log:
            log.step("event already mapped in target SML; skip value mapping")
        return {"status": "skipped", "reason": "event_already_mapped"}

    last_index = len(values) - 1
    last_path = f"{sml_path}[{last_index}]"
    payload = payload_for(epcis_event)
    if log:
        log.data("last_smc_index", last_index)
        log.data("mapping_payload", payload)

    smc = update_full_smc(values[last_index], epcis_event)
    put_result = http_json(
        "PUT",
        f"{base}/submodels/{submodel}/submodel-elements/{quote(last_path, safe='')}",
        smc,
        log=log,
        reason="replace complete SMC with mapped EPCIS values",
    )
    response = {
        "smc_put": put_result,
    }

    return {
        "status": "mapped",
        "last_index": last_index,
        "payload": payload,
        "response": response,
    }


def load_event(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_json")
    parser.add_argument("--submodel-id", required=True)
    parser.add_argument("--sml-path", required=True)
    parser.add_argument("--aas-environment", default=DEFAULT_AAS_ENVIRONMENT)
    args = parser.parse_args()

    result = map_event(load_event(args.event_json), args.submodel_id, args.sml_path, args.aas_environment)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
