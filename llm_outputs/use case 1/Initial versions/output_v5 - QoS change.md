# Interface Definitions

## qci

| Property | Value |
|----------|-------|
| Interface | Both |
| Operation | Configuration Update / Runtime API Update |
| Configuration Location | `pdn_list.<erabs>.qci` or `ue_db.<pdn_list>.<erabs>.qci` |
| Remote API Location | `ue_modify_bearer.qos.qci` |
| Constraints | Integer range 1 to 255 |
| Required Inputs | Remote API: `imsi` (or `imei`), `erab_id` |
| Related Parameters | `priority_level`, `pre_emption_capability`, `pre_emption_vulnerability` |
| Purpose | Sets the QoS Class Identifier for an E-RAB in EPS. |
| Documentation | Page 31, 86 |

## 5qi

| Property | Value |
|----------|-------|
| Interface | Both |
| Operation | Configuration Update / Runtime API Update |
| Configuration Location | `pdn_list.<slices>.<qos_flows>.5qi` |
| Remote API Location | `ue_modify_pdu_session.qos_flow.5qi` |
| Constraints | Integer range 1 to 254 |
| Required Inputs | Remote API: `imsi` (or `nai`, `imei`), `pdu_session_id` |
| Related Parameters | `priority_level` |
| Purpose | Sets the 5G QoS Identifier for a QoS flow in 5GC. |
| Documentation | Page 37, 88 |
