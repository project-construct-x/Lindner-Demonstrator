#!/usr/bin/env python3
"""Find or create an AAS by EPC globalAssetId."""

from __future__ import annotations

import argparse
import base64
import json
import re
import urllib.request
from typing import Any
from urllib.parse import urlencode, urlsplit, unquote


DEFAULT_AAS_ENVIRONMENT = "http://132.195.160.222:8081"
LIMIT = 100
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
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        text = resp.read().decode()
        return json.loads(text) if text else None


def compact_asset_id(epc: str) -> str:
    parts = [unquote(part) for part in urlsplit(epc).path.split("/") if part]
    if "00" in parts and parts.index("00") + 1 < len(parts):
        return parts[parts.index("00") + 1]
    return re.sub(r"[^A-Za-z0-9_]", "_", epc).strip("_")


def aas_id_for_epc(epc: str) -> str:
    return f"https://example.com/ids/AssetAdministrationShell_{compact_asset_id(epc)}"


def result_list(body: Any, fallback_key: str) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return body
    if isinstance(body.get("result"), list):
        return body["result"]
    return body.get(fallback_key, [])


def cursor(body: Any) -> str | None:
    return (
        body.get("paging_metadata", {}).get("cursor")
        or body.get("pagingMetadata", {}).get("cursor")
    )


def all_aas(base: str, log: Any | None = None) -> list[dict[str, Any]]:
    shells = []
    next_cursor = None
    while True:
        query = {"limit": LIMIT}
        if next_cursor:
            query["cursor"] = next_cursor
        body = http_json(
            "GET",
            f"{base}/shells?{urlencode(query)}",
            log=log,
            reason="list all AAS shells to compare globalAssetId with epcList[0]",
        )
        shells.extend(result_list(body, "assetAdministrationShells"))
        next_cursor = cursor(body)
        if not next_cursor:
            return shells


def find_aas(shells: list[dict[str, Any]], epc: str) -> dict[str, Any] | None:
    for shell in shells:
        if shell.get("assetInformation", {}).get("globalAssetId") == epc:
            return shell
    return None


def create_aas(base: str, epc: str, log: Any | None = None) -> dict[str, Any]:
    shell = {
        "id": aas_id_for_epc(epc),
        "idShort": "AssetAdministrationShell",
        "assetInformation": {
            "assetKind": "Instance",
            "globalAssetId": epc,
        },
    }
    if log:
        log.data("new_aas_id", shell["id"])
    http_json("POST", f"{base}/shells", shell, log=log, reason="create AAS for missing epcList[0]")
    return shell


def get_aas(base: str, aas_id: str, log: Any | None = None) -> dict[str, Any]:
    shell = http_json(
        "GET",
        f"{base}/shells/{b64url(aas_id)}",
        log=log,
        reason="fetch full AAS shell to extract submodel references",
    )
    return shell.get("result", shell)


def submodel_ids(shell: dict[str, Any]) -> list[str]:
    ids = []
    for ref in shell.get("submodels", []):
        for key in ref.get("keys", []):
            if key.get("type") == "Submodel":
                ids.append(key["value"])
    return ids


def link_submodel(
    aas_id: str,
    submodel_id: str,
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: Any | None = None,
) -> None:
    base = aas_environment.rstrip("/")
    ref = {
        "type": "ModelReference",
        "keys": [{"type": "Submodel", "value": submodel_id}],
    }
    if log:
        log.data("linked_submodel_id", submodel_id)
    http_json(
        "POST",
        f"{base}/shells/{b64url(aas_id)}/submodel-refs",
        ref,
        log=log,
        reason="register newly created submodel on the AAS",
    )


def resolve_aas(
    epc: str,
    aas_environment: str = DEFAULT_AAS_ENVIRONMENT,
    log: Any | None = None,
) -> dict[str, Any]:
    base = aas_environment.rstrip("/")
    if log:
        log.step("resolve AAS for epcList[0]")
        log.data("epc", epc)
    shell = find_aas(all_aas(base, log), epc)
    status = "found"
    if shell is None:
        if log:
            log.step("no AAS matched epcList[0]; create AAS")
        shell = create_aas(base, epc, log)
        status = "created"
        aas_id = shell["id"]
        ids: list[str] = []
        if log:
            log.data("aas_id", aas_id)
            log.data("submodel_ids", ids)
        return {
            "status": status,
            "epc": epc,
            "aas_id": aas_id,
            "submodel_ids": ids,
        }
    elif log:
        log.step("matching AAS found")

    aas_id = shell["id"]
    full_shell = get_aas(base, aas_id, log)
    ids = submodel_ids(full_shell)
    if log:
        log.data("aas_id", aas_id)
        log.data("submodel_ids", ids)
    return {
        "status": status,
        "epc": epc,
        "aas_id": aas_id,
        "submodel_ids": ids,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("epc", help="the EPCIS epcList[0] value")
    parser.add_argument("--aas-environment", default=DEFAULT_AAS_ENVIRONMENT)
    args = parser.parse_args()

    print(json.dumps(resolve_aas(args.epc, args.aas_environment), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
