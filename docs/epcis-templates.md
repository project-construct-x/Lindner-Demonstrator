# EPCIS templates

Runtime files live in `backend/epcis/`. `backend/epcis-original/` and [docs/epcis-eventstrecke/](./epcis-eventstrecke/README.md) are reference copies and are not loaded.

## Document wrapper

`document.json` is an EPCIS 2.0 document. `$creationDate` is substituted and `epcisBody.eventList` is replaced with the rendered events. Context includes the GS1 EPCIS 2.0 context and `cx`.

## Placeholders

Python `string.Template` (`$variable`):

| Placeholder | Source |
| --- | --- |
| `$sscc`, `$lgtin1`, `$lgtin2`, `$desadv`, `$po` | Session for this SSCC |
| `$eventTime` | ISO 8601 UTC, staggered across the step's events |
| `$eventTimeZoneOffset` | Fixed `+02:00` in `session_store.py` |
| `$eventID` | `urn:uuid:{uuid4()}` |

Event types in the set include `TransactionEvent`, `ObjectEvent`, `TransformationEvent`, and `AggregationEvent`. Packing steps (`03.json`, `07b.json`) are aggregation events with `bizStep` `packing`. Querying those is covered in [EPCAT2](./epcat2.md).

## Adding a step

1. Add or edit JSON under `backend/epcis/`.
2. Register `template_files` and `number` in `backend/epcis/steps.py`.
3. Add the button in `frontend/src/constants/steps.ts`.
4. If the step must invent LGTINs, include its number in `step_needs_material` in `session_store.py`.
