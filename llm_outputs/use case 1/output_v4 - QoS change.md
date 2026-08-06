# Interface Definitions

## qci (Static Configuration)

| Property | Value |
|----------|-------|
| Interface | Configuration File |
| Location | `ue_db.pdn_list.erabs.qci` |
| Constraints | Integer: 1 to 255 |
| Dependencies | Required: `imsi` or `nai` (to identify the UE in `ue_db`) |
| Purpose | Sets the QoS Class Identifier (LTE) or 5G QoS Identifier (NR) for the UE's configured bearers. |
| Documentation | Page 31, 40 |

## 5qi (Dynamic Session Modification)

| Property | Value |
|----------|-------|
| Interface | Remote API |
| Location | `ue_modify_pdu_session.qos_rules.qos_flow.5qi` |
| Constraints | Integer: 1 to 254 |
| Dependencies | Required: `imsi` (or `nai`/`imei`) and `pdu_session_id` |
| Purpose | Modifies the 5G QoS Identifier for a specific QoS flow within an active PDU session. |
| Documentation | Page 87, 88 |

## qci (Dynamic Bearer Modification)

| Property | Value |
|----------|-------|
| Interface | Remote API |
| Location | `ue_modify_bearer.qos.qci` |
| Constraints | Integer: 1 to 255 |
| Dependencies | Required: `imsi` (or `imei`) and `erab_id` |
| Purpose | Modifies the QCI or 5G QoS Identifier for an active network-initiated EPS bearer. |
| Documentation | Page 86 |
