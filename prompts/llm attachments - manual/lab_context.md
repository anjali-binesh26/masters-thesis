# Lab context

## Environment
- This is a master's thesis on AI-assisted Amarisoft MME/5GC management.
- The lab uses a shared Amarisoft Callbox Classic.
- Its config_get response reports software version 2024-06-15.
- Two phones can register on NR. They may share an IMSI; IMSI alone may not identify one phone.
- Network access is through the Remote API. Static configuration edits and service restarts are outside scope.

## Current experiment
- The current trial is manual LLM-assisted logging configuration.
- Read operator_request.txt for the requested layer, field and value.
- Produce one proposal. The human copies only the API JSON into request.json.
- The controller validates it, asks CONNECT before live reads, reads current values, displays the plan and asks APPLY before changing anything.
- The controller verifies supported logging values through config_get. Recovery writes require separate approval.
- You have no direct connection to the Callbox and must not claim execution or success.

## Observed controller behaviour
- NAS and NGAP logging-level changes have worked in lab trials.
- IP max_size changed from 32 to 16 and was restored to 32 with verified read-back.
- These are historical results, not statements of current configuration.
- The Callbox returns layer names such as NAS, NGAP and IP. The controller accepts supported layer names regardless of capitalization and resolves them to the server's exact spelling.
- Logging changes affect diagnostic output. They do not change UE QoS, MTU or bandwidth.

## Current-state limits
- No live_state.json is required for a fully specified logging request: the controller reads the original value during preflight.
- Do not invent the current value or use historical trial values as a baseline.
- For ambiguous requests, ask which layer, field or value is intended.
- Timer and QoS trials need additional documentation and prerequisites; this attachment package focuses on logging.

