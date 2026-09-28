# Interface Definitions

## qci

| Property | Value |
|----------|-------|
| Configuration | `mme.cfg.pdn_list.erabs.qci` |
| Runtime API | `ue_modify_bearer.qos.qci` |
| Required Inputs | `imsi`, `erab_id` |
| Constraints | Integer 1-255. QoS Class Identifier of the E-RAB. |
| Related Parameters | `priority_level` |
| Purpose | Sets the QoS Class Identifier for an E-RAB. |
| Documentation | Page 31, 86 |

## 5qi

| Property | Value |
|----------|-------|
| Configuration | `mme.cfg.pdn_list.slices.qos_flows.5qi` |
| Runtime API | `ue_modify_pdu_session.qos_flow.5qi` |
| Required Inputs | `imsi` (or `nai`, `imei`), `pdu_session_id` |
| Constraints | Integer 1-254. 5G QoS Identifier of the QoS flow. |
| Related Parameters | `priority_level` |
| Purpose | Sets the 5G QoS Identifier for a QoS flow. |
| Documentation | Page 37, 88 |
