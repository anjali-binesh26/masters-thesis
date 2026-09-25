# UC1 lab procedure and acceptance tests

## Scope and evidence

Use the lab's ltemme.pdf, version 2024-06-15. Printed page numbers: common
messages/logging 59-60, timers 62-63, ue_get 77-79, EPS QoS 86-87, PDU QoS
87-88, GBR 33. Two registered UEs are sufficient. Use IMEI to distinguish them
if the SIMs share an IMSI; do not substitute IMEISV for IMEI.

The controller supports schemas and operation adapters, not three fixed test
commands. The input file contains one supported JSON operation per run. Parameter
values and target devices come from the operator/LLM proposal. Unknown fields,
unsupported operations and ambiguous targets are rejected before a write.
The five destructive messages quit/log_reset/ue_del/ue_detach/me_del remain blocked.
No configuration-file edits or Callbox service restarts are performed.

A model's JSON is a proposal, not evidence of execution. A request acknowledgment
is not verification. Record the exact status; pending/unknown/accepted_unverified
are NOT successful verified configuration changes. Never assume unit-test mocks
prove a feature is observable on the real Callbox.

## Ubuntu setup

For later NetSight integration, keep the repositories next to each other (manual mode only needs masters-thesis):

```
Thesis/
  ltemme.pdf
  masters-thesis/
  netsight/
```

In masters-thesis (Python 3.10+):

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/controller_uc1.py --help
```

Do not copy the Windows venv to Ubuntu. The controller defaults to localhost:9000,
which can be an existing SSH tunnel. For direct permitted LAN access append
`--host <CALLBOX_IP> --port 9000` to every online command. The endpoint must be the
MME/5GC WebSocket, not the eNB or IMS service. If com_auth is enabled, provide
AMARISOFT_PASSWORD in the controller process environment; do not put it in an
LLM prompt or command-line argument.

NetSight retains its existing .env for model/host/port. Its source is unchanged.
The new runner overrides only PROMPT_FILE and OUTPUT_FILE for this invocation.
Your original NetSight prompt and ./start.sh remain usable for experiments.

## Manual copy/paste workflow for every request

NetSight is not required for these initial controller tests. Keep its integration
for later; no `--prepare`, envelope or request_id is needed in manual mode.

1. Paste ONE raw API request into project `request.json` (or a `.txt` file passed
   with `--request PATH`). Copy only the JSON, without surrounding prose. A single
   enclosing json code fence is also accepted. The starter file is `{"message":"ue_get"}`.
2. Run `python scripts/controller_uc1.py` for offline schema validation. No connection.
3. Run `python scripts/controller_uc1.py --execute` with the correct host/port.
   `CONNECT` authorizes connection/authentication and live reads for this run.
   Any other answer cancels before connecting. The endpoint and request are shown.
4. For a write, inspect the actual plan, original values, verification limitations
   and recovery payload. Only `APPLY` authorizes the change. Any other answer
   cancels the write. Read-only requests need no second prompt.
5. Verification reads follow automatically under your read permission. A partial
   observable logging change can trigger a separate `ROLLBACK` prompt. Approving
   it rechecks state before recovery and verifies restoration afterward. Declining
   produces `recovery_pending`; the partial change has NOT been undone.
6. Keep the printed `logs/uc1-<run-id>.json` report: input path/hash, parsed request,
   confirmations, actual send intents/responses, plan and final outcome. A send
   intent is not proof the server received the request. Editing the input file
   during confirmation does not change the already-loaded request being approved.

Optional inventory: `python scripts/controller_uc1.py --inspect` asks `CONNECT`
and reads config_get plus ue_get, saving project `logs/live_state.json`.

Restore using the saved execution report:

```bash
python scripts/controller_uc1.py --restore-from logs/uc1-<run-id>.json
python scripts/controller_uc1.py --restore-from logs/uc1-<run-id>.json --execute
```

Restoration is a NEW confirmed operation at the same endpoint. Check that any
saved baseline still describes the actual current state; override with
`--baseline CURRENT.json` if needed. Timer/QoS restoration has the same evidence
requirements as the original change. Restoration is not guaranteed by its acknowledgment.

When returning to NetSight, use the optional steps in README and explicitly pass
`--proposal ../netsight/output/action.json`. This mode retains envelope/request-ID
validation. The default command always uses manual project `request.json`.

## Attachment selection and response time

For initial runs, use operator_request.json, uc1_api_reference.md and an optional
fresh live_state.json. Keep the full manual outside attachments; add relevant
manual excerpts if needed. NetSight recursively sends every attachment and
renders every PDF page each run. Adding all historical prompts/outputs as context
can add conflicting examples and unnecessary work. Do not delete your reference
files; choose the input folder deliberately. The checked-in reference and prompt
are controller contract version 1; keep them synchronized with schema changes.
No speed improvement has been benchmarked yet.

## Test 1: logging change, isolation and restoration

Prerequisites: both UEs registered; logging not locked; ordinary data connectivity
working. Choose a logging level different from the current NAS level.

Operator request: "Set NAS logging to info."
Expected API request (transport adds a unique message_id):

```json
{"message":"config_set","logs":{"layers":{"nas":{"level":"info"}}}}
```

Procedure:
1. Save config_get and ue_get via --inspect. Record both devices' identities.
2. Run the complete file-handoff workflow above.
3. Confirm the payload changes only the intended logging field.
4. Require result status verified and exact read-back of logs.layers.nas.level.
5. Check both UEs remain registered and can still use data.
6. Restore from the run report. Require another verified result and the original level.

Pass: requested level and restored level each match their read-back; unrelated
log settings and both UE connections remain intact. Repeat with at least two
paraphrases, returning to baseline between trials. Do not count a no-change trial
as evidence that a modification occurred.

## Test 2: 5G periodic registration timer on both UEs

Prerequisites: controlled lab slot because this is CORE-WIDE, both UEs registered
on NR, and a known current GLOBAL t3512 setting. Obtain the actual active baseline
from the lab operator/current runtime configuration, not from an old backup,
LLM guess, or a UE's negotiated timer alone. Check subscriber overrides and UE
requests for longer timers. Do not use authentication_mode=skip as a convenience.

Make a local operator baseline file (the following 1800 is ONLY an example):

```json
{"message":"config_set","t3512":1800}
```

Operator request: "Set the core periodic registration timer to 10 minutes."
Expected request:

```json
{"message":"config_set","t3512":600}
```

Procedure:
1. Record the known global original value and each UE's ue_get.t3512.
2. Paste the timer JSON into request.json, preview, then execute with --baseline baseline-timer.json.
3. Confirm that the UI labels the change core-wide and lists both UEs.
4. At the CHECK prompt, manually toggle airplane mode on EACH UE and wait for
   successful registration. Type CHECK only after both have re-registered.
5. Require observed t3512=600 for both original IMEISV/subscriber identities.
6. Restore from the report, repeat registration on both, and verify the original
   expected received value (assuming no UE/subscriber override).

Pass: both original devices receive the requested timer and the restored timer,
remain usable, and the reports distinguish pending registration from success.
Do not expect the timer to change on an already-registered UE immediately.
The test verifies received values, not a timed observation of the next periodic
registration. Missing UE, override, unsupported timer encoding or mismatch is a
failure/limitation to investigate, not a reason to force success. No automatic
timer rollback is claimed: restoring it requires another registration cycle.

## Test 3: refusal and human approval

Run the following subtests from a known logging baseline with both UEs connected:
- "Set NAS logging to superdebug."
- "Detach both phones."
- A valid logging request, but answer NO at APPLY.
- A valid request, but answer NO at CONNECT: no connection or API message is allowed.
- For a shared IMSI, request a UE QoS change without sufficient disambiguation.

Directly edit request.json to contain an
invalid API value and run --execute. This exercises controller validation even
without needing an LLM. Paste invalid logging JSON or {"message":"ue_detach"} for the first two cases.

Pass: no MUTATING message is sent. The controller explains invalid/blocked,
cancelled or ambiguous input; logging and UE connections remain unchanged.
Read-only preflight messages are allowed only after CONNECT. Use the report send intents as evidence;
an unchanged network alone does not prove no write was attempted.

## Additional QoS trial: change an existing non-default 5G flow

This is supported by a separate operation adapter, not config_set. It is an
additional UC1 test only when the prerequisites can be established. Two connected
phones do not by themselves guarantee a suitable non-default flow.

Prerequisites:
- An NR UE with an active PDU session and a suitable existing NON-DEFAULT flow.
  ue_get.bearers[].qos_flow_id is the DEFAULT flow; dedicated[].qos_flow_id lists
  non-default flows. Do not guess QFI or confuse QFI with 5QI.
- A complete, known CURRENT QoS baseline for ALL non-default flows in that session,
  including ARP, GBR and any explicit 5qi_qos characteristics. Obtain it from
  controlled provisioning/current decoded signalling, not ue_get or an LLM.
- For a simple 5QI transition, use an existing non-GBR profile in 5..9 and another
  non-GBR value in 5..9. Do not disrupt an IMS voice GBR flow to make this test work.
- A means to inspect decoded NAS/NGAP signalling for this exact UE/session/flow
  and the resulting QoS; a command acknowledgment or traffic speed is insufficient.
- Identify the second UE as the unaffected control device.

Local baseline-qos.json example (replace ALL identifiers and enumerate ALL flows):

```json
{
  "message":"ue_modify_pdu_session",
  "imsi":"001010123456789",
  "imei":"12345678901234",
  "pdu_session_id":1,
  "qos_flow":[
    {"qfi":2,"5qi":9,"priority_level":15,
     "pre_emption_capability":"shall_not_trigger_pre_emption",
     "pre_emption_vulnerability":"not_pre_emptable"}
  ]
}
```

Operator request: "For IMSI <IMSI>, IMEI <IMEI>, PDU session <ID>, change existing
non-default QoS flow <QFI> from 5QI 9 to 8. Preserve all other flows and settings."
The LLM proposal supplies only a patch:

```json
{"message":"ue_modify_pdu_session","imsi":"001010123456789",
 "imei":"12345678901234","pdu_session_id":1,"qos_flow":[{"qfi":2,"5qi":8}]}
```

Execute with --baseline baseline-qos.json. The controller resolves one registered
NR UE, matches the session and complete non-default QFI set, merges the patch
into the baseline, displays the FULL wire request, asks APPLY and rechecks the
session before sending. It preserves all untouched flow entries and QoS fields.

Pass for manual lab evaluation: decoded evidence confirms the requested 5QI for
the exact flow, procedure completion and connectivity; UE2/unselected flows are
unaffected; restoration is subsequently confirmed by equivalent evidence.
Save the capture/log reference with the report. The automated result remains
accepted_unverified because the manual does not document full QoS read-back in
ue_get. Do not relabel that as automatically verified. No blind QoS rollback is
sent after a timeout; inspect state before using the saved compensation.

If only default flows exist, the controller refuses this operation. Record the
trial as blocked by its prerequisite; do not invent a config_set. Creating a
new flow, changing a default flow, resource-type conversions, qos_rules edits,
and non-3GPP adapters are outside this initial implementation.

## Evidence table for the thesis

For manual trials mark model/prompt/inference fields as not used. For each trial record: exact natural-language input; input file/hash (request_id only in NetSight mode); model and
prompt/reference versions; NetSight inference duration; generated JSON; validation
outcome; operator decision; endpoint; UE identities and session/QFI where relevant;
before/after evidence; execution/verification status; restoration outcome; and any
manual steps. Reports cover controller events; add NetSight logs and manual
signalling captures separately. Record failures and unsupported cases as results.

## Offline failure/recovery tests

Run `python -m unittest discover -s tests -v`. These cover stale response IDs,
errors/timeouts, ambiguous devices, malformed JSON, invalid ranges, cancelled
confirmation, changes during confirmation, partial logging application and
separately confirmed compensation, declined recovery, and changes during recovery confirmation. Use mocked faults rather than deliberately dropping the
shared Callbox connection during a live write. All tests avoid live network access.
