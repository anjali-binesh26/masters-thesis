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
