# Amarisoft UC1 controller

Start with the manual copy/paste workflow. NetSight is optional.

1. Paste one Amarisoft API JSON object into `request.json` in this project.
   The supplied file contains the read-only request `{"message":"ue_get"}`.
   No request ID, envelope, or NetSight setup is required. Copy only the JSON;
   surrounding explanation and multiple requests are rejected.
2. From the project directory, preview without connecting:

   ```bash
   python scripts/controller_uc1.py
   ```

3. Run against the lab endpoint:

   ```bash
   python scripts/controller_uc1.py --execute --host <CALLBOX_IP> --port 9000
   ```

   Type `CONNECT` to authorize connection and read-only requests for this run.
   For changes, review the live plan and type `APPLY`. Recovery writes require
   a separate `ROLLBACK` confirmation. Anything else cancels that step; declining
   recovery leaves the partially applied state for manual investigation.
   There is no unattended approval flag. Verification reads are covered by the
   run's read permission. Read-only requests need only `CONNECT`.

Use `--request path/to/message.txt` to select a different JSON/text file.
The default file is resolved relative to the project, even from another directory.
Reports are saved in `logs/`; `--inspect` saves `logs/live_state.json` after consent.
Use localhost (the default) if accessing the API through an existing SSH tunnel.

## First-time setup (Ubuntu, Python 3.10+)

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

See [the lab procedure and tests](tests/UC1_LAB_TESTS.md) for logging, timer,
refusal and optional QoS trials, including baselines and restoration.
Logging supports read-back verification and confirmed compensation. Timers need
UE re-registration and, where unreadable globally, a trusted operator baseline.
QoS changes require a complete current baseline and manual signalling evidence;
an acknowledgment is never labelled verified success.

## Export controller evidence into an LLM run document

Raw controller reports remain private in `logs/`. The offline exporter produces
an allowlisted summary: UTC timestamps, run ID, supported parameter changes,
approval decisions, verification results and request/response operation names.
It omits subscriber/device identifiers, endpoints, license details, local paths,
raw API responses and free-text errors. Detailed errors stay in the private report.
Targets are omitted, so a QoS summary alone cannot establish correct device selection.

List reports chronologically (timestamps help selection; they do not prove linkage):

```bash
python scripts/export_uc1_evidence.py --list
```

Preview an append to an existing run document, then repeat with `--write` to save:

```bash
python scripts/export_uc1_evidence.py logs/uc1-RUN-ID.json --output "llm_outputs/use case 1/uc1 outputs v1.md" --kind llm-trial
python scripts/export_uc1_evidence.py logs/uc1-RUN-ID.json --output "llm_outputs/use case 1/uc1 outputs v1.md" --kind llm-trial --write
```

Use `--kind llm-trial` only when you associate the actual LLM proposal with this
execution; this records your association, not automatic proof of unchanged input.
Use `--kind restoration` for a restore report, or the default `independent` for
a separately performed controller test. Multiple explicit report files can be
passed together; they are sorted by start time within that export. Already recorded
run IDs are skipped. Existing document sections retain their original order.
Without `--output`, `--write` creates a timestamped file under
`llm_outputs/controller evidence/` for each selected report.

The exporter does not contact the network or alter raw reports. The raw-report
SHA-256 fingerprint allows later comparison with the privately retained original;
it is not a digital signature. Review the complete Markdown before publishing:
existing LLM/terminal text is preserved and is NOT sanitized. The exporter does
not infer a failure reason from omitted text or turn unverified outcomes into success.

## Interactive trial record (operator request + LLM response + controller evidence)

To build one combined Markdown trial record — operator request, LLM response,
NetSight measurements and sanitized controller evidence in a single file — run:

```bash
python scripts/export_uc1_evidence.py --interactive
```

This reads `attachments/operator_request.txt`, `output/interfaces.md` and any
`logs/netsight_*.log` from the sibling `../netsight` repository (override with
`--netsight-dir`), lets you pick a controller change report and an optional
restoration report from `logs/uc1-*.json`, previews the assembled record, and
only saves it under `llm_outputs/use case 1/` after you confirm. It never
connects to the Callbox, calls an LLM, or modifies the source files it reads.
Missing expected files are never invented; you are asked for a path or can
skip. Existing files are never overwritten, and only plain filenames inside
`llm_outputs/use case 1/` are accepted. This mode creates new records only;
it does not rewrite the append/export workflow above.

## Optional NetSight handoff (later)

```bash
python scripts/controller_uc1.py --prepare "Set NAS logging to info"
bash scripts/run_netsight_uc1.sh
python scripts/controller_uc1.py --proposal ../netsight/output/action.json
python scripts/controller_uc1.py --proposal ../netsight/output/action.json --execute
```

This explicit mode still requires the versioned envelope and matching request ID.
For manual mode, paste only its inner `request` object into `request.json`.
To supply live context to NetSight later, deliberately copy the relevant current
`logs/live_state.json` into its attachments; `--inspect` no longer writes there.

The API client is `controller.amarisoft_api`. Historical `scripts/mme_ws_test.py`
is not imported by this pipeline. Supported fields are based on the supplied
ltemme.pdf version 2024-06-15. Tests use mocks; live lab verification remains pending.
