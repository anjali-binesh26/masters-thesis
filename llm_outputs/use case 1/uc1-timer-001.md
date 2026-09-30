## Operator request:
Set the core-wide 5G periodic registration timer T3512 to
10 minutes using the Amarisoft Remote API.
Do not change any other setting.

# UC1-TIMER-001 — T3512 change and restoration

Date: 2026-09-30
Model: gemma4:31b
Handoff: LLM JSON manually copied into request.json

Outcome:
- Proposed JSON: correct.
- LLM explanation: partially incorrect; see assessment below.
- Change: both UEs reported T3512 = 600 seconds after re-registration.
- Restoration: both UEs reported T3512 = 1800 seconds after re-registration.

Baseline:
1800 seconds was an assumed global baseline, supported by the
documented default, configuration inspection and previous UE readings.
Previous runtime changes could not be independently excluded.

Verification scope:
Assigned timer values were checked after re-registration.
Actual periodic-update timing was not measured.

## LLM Response:
Status: READY
Interpretation: Set the core-wide T3512 periodic registration timer to 600 seconds (10 minutes).

Proposal:
```json
{
  "message": "config_set",
  "t3512": 600
}
```

Preconditions: None.

Verification: The controller can verify the change by performing a `config_get` operation, although the API reference notes that `config_get` is not guaranteed to return all global settings.

Reference: uc1_api_reference.md (config_set supported fields, p. 62)

## Assessment of the LLM response

The proposed API message correctly converted 10 minutes to 600 seconds.

However, "Preconditions: None" omitted the controller's baseline and
registered-UE requirements. The suggested config_get verification was
also insufficient for this trial.

The controller used its own verification procedure: manual
re-registration followed by ue_get checks for both original UEs.
The model's verification explanation was not executed.

## NetSight measurements

- Model: gemma4:31b
- Context: full 123-page manual plus four text attachments
- Agent elapsed time: 140.9 seconds
- Input tokens: 36,357
- Output tokens: 780
- Total tokens: 37,137

Agent elapsed time includes document loading and model generation.
It is not a pure inference measurement.

## Controller evidence
Log IDs - uc1-dc2e8ba157944511befddc827df6f6bf.json (change); uc1-5acbd6d357c2428ea91a111c0cf153e7.json (restoration)
