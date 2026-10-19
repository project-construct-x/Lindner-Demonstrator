#!/usr/bin/env bash
# 1) shipping events for a dispatch advice  2) packing events for the SSCCs in their epcList
#
#   EPCAT_URL=http://localhost:8080 EPCAT_TOKEN=... ./scripts/query-versand-packing.sh
#   ./scripts/query-versand-packing.sh https://id.gs1.org/253/40471113333333d3e4s4d5v

set -euo pipefail

EPCAT_URL="${EPCAT_URL:-https://epcat2.construct-x.prod-k8s.eecc.de}"
EPCAT_URL="${EPCAT_URL%/}"
DESADV="${1:-${DESADV:-https://id.gs1.org/253/40471113333333d3e4s4d5v}}"

auth=()
if [[ -n "${EPCAT_TOKEN:-}" ]]; then
  auth=(-H "Authorization: Bearer ${EPCAT_TOKEN}")
fi

echo "=== Versand ${DESADV} ===" >&2
versand=$(curl -fsS --get "${auth[@]}" \
  "${EPCAT_URL}/api/events" \
  --data-urlencode "EQ_bizStep=shipping" \
  --data-urlencode "EQ_bizTransaction_desadv=${DESADV}")
jq . <<<"$versand"

ssccs=$(jq -r '[.epcisBody.queryResults.resultsBody.eventList[].epcList[]?] | unique | join("|")' <<<"$versand")
if [[ -z "$ssccs" ]]; then
  echo "Versand event has no epcList." >&2
  exit 1
fi

echo "=== Packen ===" >&2
echo "SSCCs: ${ssccs}" >&2
curl -fsS --get "${auth[@]}" \
  "${EPCAT_URL}/api/events" \
  --data-urlencode "EQ_bizStep=packing" \
  --data-urlencode "MATCH_parentID=${ssccs}" \
  | jq .
