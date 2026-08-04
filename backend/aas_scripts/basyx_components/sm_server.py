#!/usr/bin/env python3
"""Create a TrackingAndTracing submodel for an EPCIS event if it is not mapped yet."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:
    from . import aas_server
except ImportError:
    import aas_server


DEFAULT_AAS_ENVIRONMENT = "http://132.195.160.222:8081"
TEMPLATE_ID = "https://example.com/ids/SubmodelTemplate/TrackingAndTracing/1/0"
TRACKING_ID_SHORT = "TrackingAndTracing"
SML_PATH = "TraceabilityEvents"
TIMEOUT = 30


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
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode()
        return json.loads(text) if text else None


def event_epc(event: dict[str, Any]) -> str | None:
    epc_list = event.get("epcList")
    if isinstance(epc_list, list) and epc_list:
        return epc_list[0]
    return event.get("parentID") or event.get("parentId")


def submodel_id_for_epc(epc: str) -> str:
    asset = aas_server.compact_asset_id(epc)
    return f"https://example.com/ids/SubmodelInstance_{asset}/TrackingAndTracing/1/0"


def unwrap(body: Any) -> Any:
    return body.get("result", body)


def get_submodel(base: str, submodel_id: str, log: Any | None = None) -> dict[str, Any]:
    return unwrap(
        http_json(
            "GET",
            f"{base}/submodels/{aas_server.b64url(submodel_id)}",
            log=log,
            reason="read submodel content",
        )
    )


def get_template(base: str, log: Any | None = None) -> dict[str, Any]:
    return get_submodel(base, TEMPLATE_ID, log)


def has_source_event_id(value: Any, event_id: str) -> bool:
    if isinstance(value, dict):
        if value.get("idShort") == "SourceEventId" and value.get("value") == event_id:
            return True
        return any(has_source_event_id(item, event_id) for item in value.values())
    if isinstance(value, list):
        return any(has_source_event_id(item, event_id) for item in value)
    return False


def source_event_id_value(smc: dict[str, Any]) -> Any:
    for child in smc.get("value", []):
        if child.get("idShort") == "SourceEventId":
            return child.get("value")
    return None


def direct_child(element: dict[str, Any] | None, id_short: str) -> dict[str, Any] | None:
    if not element:
        return None
    for child in element.get("value", []):
        if child.get("idShort") == id_short:
            return child
    return None


def blank_traceability_event_smc(smc: dict[str, Any]) -> dict[str, Any]:
    blank = copy.deepcopy(smc)
    source_event_id = direct_child(blank, "SourceEventId")
    business_step = direct_child(blank, "BusinessStep")
    environmental_impact = direct_child(blank, "EnvironmentalImpact")
    co2e = direct_child(environmental_impact, "CO2e")

    if source_event_id is not None:
        source_event_id["value"] = ""
    if business_step is not None:
        business_step["value"] = ""
        business_step.pop("valueId", None)
    if co2e is not None:
        co2e["value"] = "0"
    return blank


def copy_template(template: dict[str, Any], submodel_id: str) -> dict[str, Any]:
    submodel = copy.deepcopy(template)
    submodel["id"] = submodel_id
    submodel["idShort"] = TRACKING_ID_SHORT
    submodel["kind"] = "Instance"
    for key in ("administration", "createdAt", "updatedAt"):
        submodel.pop(key, None)
    return submodel


def post_submodel(base: str, submodel: dict[str, Any], log: Any | None = None) -> None:
    try:
        http_json("POST", f"{base}/submodels", submodel, log=log, reason="post copied submodel instance")
    except urllib.error.HTTPError as exc:
        if exc.code != 409:
            raise
        if log:
            log.step("submodel already exists; continue with value mapping")


def get_sml(base: str, submodel_id: str, log: Any | None = None) -> dict[str, Any]:
    return unwrap(
        http_json(
            "GET",
            f"{base}/submodels/{aas_server.b64url(submodel_id)}/submodel-elements/{quote(SML_PATH, safe='')}",
            log=log,
            reason="read TraceabilityEvents before appending an SMC",
        )
    )


def put_sml(
    base: str,
    submodel_id: str,
    sml: dict[str, Any],
    log: Any | None = None,
) -> None:
    http_json(
        "PUT",
        f"{base}/submodels/{aas_server.b64url(submodel_id)}/submodel-elements/{quote(SML_PATH, safe='')}",
        sml,
        log=log,
        reason="replace TraceabilityEvents after appending an SMC",
    )


def append_traceability_event_smc(
    base: str,
    submodel_id: str,
    log: Any | None = None,
) -> int:
    sml = get_sml(base, submodel_id, log)
    values = sml["value"]
    if not values:
        raise ValueError(f"{SML_PATH} is empty; cannot append an SMC")

    if not source_event_id_value(values[-1]):
        if log:
            log.step("last TraceabilityEvents SMC is empty; reuse it")
        return len(values) - 1

    values.append(blank_traceability_event_smc(values[-1]))
    index = len(values) - 1
    if log:
        log.step("append new TraceabilityEvents SMC for new event")
        log.data("new_smc_index", index)
    put_sml(base, submodel_id, sml, log)
    return index


def ensure_event_submodel(
    epcis_event: dict[str, Any],
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: Any | None = None,
) -> dict[str, Any]:
    base = aas_environment.rstrip("/")
    epc = event_epc(epcis_event)
    if not epc:
        if log:
            log.step("event has no epcList[0] or parentID; skip")
        return {
            "status": "skipped",
            "reason": "missing_epc_or_parent_id",
            "event_id": epcis_event.get("eventID"),
        }

    event_id = epcis_event["eventID"]
    if log:
        log.step("resolve or create submodel for EPCIS event")
        log.data("event_id", event_id)
    aas = aas_server.resolve_aas(epc, aas_environment, log)
    submodel_id = submodel_id_for_epc(epc)
    existing_tracking_submodel_id = None

    for existing_submodel_id in aas["submodel_ids"]:
        if log:
            log.step("check existing submodel for SourceEventId")
            log.data("submodel_id", existing_submodel_id)
        submodel = get_submodel(base, existing_submodel_id, log)
        if has_source_event_id(submodel, event_id):
            if log:
                log.step("event already mapped; skip submodel creation and value mapping")
            return {
                "status": "skipped",
                "reason": "event_already_mapped",
                "aas_id": aas["aas_id"],
                "submodel_id": existing_submodel_id,
            }
        if existing_submodel_id == submodel_id:
            existing_tracking_submodel_id = existing_submodel_id

    if existing_tracking_submodel_id:
        if log:
            log.step("SSCC TrackingAndTracing submodel exists; append event SMC if needed")
        append_traceability_event_smc(base, existing_tracking_submodel_id, log)
        return {
            "status": "ready",
            "aas_id": aas["aas_id"],
            "submodel_id": existing_tracking_submodel_id,
            "sml_path": SML_PATH,
        }

    if log:
        if aas["submodel_ids"]:
            log.step("SSCC TrackingAndTracing submodel missing; copy template")
        else:
            log.step("AAS has no submodels; copy template")
        log.data("new_submodel_id", submodel_id)
    submodel = copy_template(get_template(base, log), submodel_id)
    post_submodel(base, submodel, log)
    aas_server.link_submodel(aas["aas_id"], submodel_id, aas_environment, log)

    return {
        "status": "created",
        "aas_id": aas["aas_id"],
        "submodel_id": submodel_id,
        "sml_path": SML_PATH,
    }


def load_event(path: str) -> dict[str, Any]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_json")
    parser.add_argument("--aas-environment", default=DEFAULT_AAS_ENVIRONMENT)
    args = parser.parse_args()

    print(json.dumps(ensure_event_submodel(load_event(args.event_json), args.aas_environment), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
