# EPCIS reference samples

`docs/epcis-eventstrecke/` holds the Lindner event path as individual EPCIS JSON files (`01_Fertigung.json` through `09_Empfang_bei_Lindner.json`), `example.json`, and `lindner.zip`.

The same named templates are copied under `backend/epcis-original/`. The running app uses the shortened names in `backend/epcis/` (`01.json`, `02a.json`, …) registered by `backend/epcis/steps.py`. Edit those when changing what the demonstrator emits.
