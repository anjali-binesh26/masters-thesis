# UC2 preparation: one-phone NR QoS-flow lifecycle

Date: 2026-09-30. Status: implemented for offline testing; not live validated.
This is preparation for UC2, not evidence that UC2 has passed. It does not call
NetSight or coordinate multiple UEs. No static config edits or restarts.

## What this establishes

Create one temporary non-GBR flow on an existing non-IMS PDU session, observe the
returned flow ID, and remove only that flow. Confirm the same original session
and default flow remain. `ue_get` cannot prove 5QI, ARP, filter installation, or
throughput. Record separate decoded NAS/NGAP evidence before claiming those.
No traffic trace or throughput collection is started automatically.

References: supplied ltemme.pdf version 2024-06-15, printed pp. 33-34 (TFT),
30 (automatic_release), 79 (ue_get), 85-86 (activation), 88-89 (deactivation).
The API uses `qci` for the 5QI in the activation request, even for a 5G UE.

## Release-policy prerequisite

The manual states that `automatic_release=true` releases the entire PDU session
when its last non-default flow is removed. The normal path requires an
operator-established `automatic_release=false` for the selected APN. The default
is false, but absence from a UE snapshot does not establish the current policy.
The documented config_get response does not promise this field.

Read the active configuration and its includes without editing them. For the
previously identified lab config, this SSH command finds relevant lines:

```bash
grep -nE 'include|access_point_name|automatic_release' /root/ltemme-linux-2024-06-15/config/Sonam_files/mmeSonam.cfg
```

This is a locator, not proof: check which APN block a value belongs to, includes,
and whether anyone changed the runtime policy. Do not enter POLICY to label an
assumption as an established runtime value.
The runner records an operator attestation, not a live verification of this flag.

After checking the relevant configuration and includes with no override found,
an operator may explicitly choose `--assume-release-default`. This replaces
POLICY with ASSUME_DEFAULT and records the baseline as an assumption. Approval
accepts that cleanup might release this test phone's internet session if runtime
policy differs. If that disruption is unacceptable, stop after read-only preflight.
No automatic re-registration or configuration change is performed to recover a
released session; the original-session verification will fail honestly.
The assumption flag is needed again for a resumed cleanup using that policy.

## Workstation commands

From the masters-thesis root with its venv active:

```bash
python -m unittest discover -s tests -v
python scripts/qos_flow_trial.py --host 192.168.20.1 --port 9000 --imsi 001010123456789 --imei 86547505216207
```

The second command asks CONNECT and only reads state. It discovers the current
internet PDU session rather than relying on an old session number. IMEI is the
first 14 digits of the observed IMEISV; do not pass the 16-digit value.

Only after the release policy is established:

```bash
python scripts/qos_flow_trial.py --host 192.168.20.1 --port 9000 --imsi 001010123456789 --imei 86547505216207 --execute
```

Approvals are CONNECT, a description of the policy evidence, POLICY, CREATE,
CHECK, CLEANUP, CHECK. Read each displayed plan. Wait for signalling to settle
before CHECK. Keep the phone registered throughout; do not toggle airplane mode
between creation and cleanup. A registration change makes the runner stop.

Default experiment profile: 5QI 9, ARP priority 15, no preemption, a bidirectional
UDP filter for remote port 55000, filter ID 0 and precedence 200. Choose an unused
test port; this is not a request to change all phone traffic or cap its bitrate.
Options `--remote-port`, `--five-qi`, and `--apn` make the chosen test explicit.
The runner deliberately refuses IMS and sessions with existing dedicated flows.

Raw evidence is saved incrementally in ignored `logs/qos-trial-<id>.json`,
including UTC timestamps, approvals, request, response, and observations.
Do not publish it unchanged. Existing UC1 exporter support does not constitute
support for this new report format.

## Interrupted runs and outcomes

- Cancellation before CREATE sends no creation.
- A returned flow ID is only an acknowledgment. CHECK requires exactly that new
  flow and the original registration/session. It does not claim QoS verification.
- If the creation reply is lost or malformed, never repeat CREATE or guess a
  cleanup ID. Inspect state and the private report first.
- If creation was recorded successfully but cleanup was declined/interrupted,
  resume with the original private report, the same endpoint, and a fresh policy
  confirmation:

```bash
python scripts/qos_flow_trial.py --host 192.168.20.1 --port 9000 --cleanup-from logs/qos-trial-REPLACE_WITH_ID.json --execute
```

- Cleanup does not recreate sessions or detach UEs. A changed registration,
  additional flow, or missing original session causes a stop, not guessed recovery.
- A lost cleanup reply requires read-only inspection; do not assume restoration.
- `session_restored` means the observable session/default-flow identifiers and
  dedicated-flow set match baseline. It does not establish unchanged performance.
- Shared hardware cannot provide an atomic guard against another operator changing
  state between the last read and the write. Coordinate the short test window.

## What remains for UC2

First qualify the lifecycle and QoS verification on one phone. Then implement a
multi-target plan, preflight every target before the first write, approve the whole
plan, track each result, and offer separately approved compensation for successful
earlier steps if a later target fails. Add LLM plan parsing only after that path is
tested. A successful one-phone run does not close UC2.
