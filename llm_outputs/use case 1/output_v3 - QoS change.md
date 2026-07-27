# Interface Definitions

## relative_capacity

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.relative_capacity` <br> API: `config_set.relative_capacity` |
| Valid Values | 0 to 255 |
| Related Parameters | mme_group_id, mme_code |
| Description | Relative capacity value used for MME or AMF load balancing in S1AP and NGAP setup/update messages. |
| Documentation | Page 12, 60 |

---

## qci

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.pdn_list.erabs.qci` <br> API: `ue_modify_bearer.qos.qci` |
| Valid Values | 1 to 255 |
| Related Parameters | priority_level, pre_emption_capability, pre_emption_vulnerability |
| Description | QoS Class Identifier for an E-RAB or 5G QoS Identifier for a QoS flow. |
| Documentation | Page 31, 86 |

---

## 5qi

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.pdn_list.slices.qos_flows.5qi` <br> API: `ue_modify_pdu_session.qos_flow.5qi` |
| Valid Values | 1 to 255 |
| Related Parameters | priority_level, gbr |
| Description | 5G QoS Identifier for a QoS flow. |
| Documentation | Page 31, 88 |

---

## log_options

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.log_options` <br> API: `config_set.logs` |
| Valid Values | String (e.g., `layer.level=verbosity,layer.max_size=n`) |
| Related Parameters | log_filename |
| Description | Comma separated list of assignments to configure log verbosity and hex dump size per layer. |
| Documentation | Page 9, 59, 60 |

---

## authentication_mode

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.authentication_mode` <br> API: `config_set.authentication_mode` |
| Valid Values | auto, force, skip |
| Related Parameters | dummy_authentication_autn_mac |
| Description | Sets the NAS authentication procedure behavior. |
| Documentation | Page 19, 66 |

---

## access_point_name

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.pdn_list.access_point_name` <br> API: `config_set.pdn_list.apn` |
| Valid Values | String |
| Related Parameters | pdn_type, dns_addr |
| Description | The Access Point Name (APN) or Data Network Name (DNN) identifier. |
| Documentation | Page 26, 68 |

---

## priority_level

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.pdn_list.erabs.priority_level` <br> API: `ue_modify_bearer.qos.priority_level` |
| Valid Values | 1 to 15 |
| Related Parameters | qci, pre_emption_capability |
| Description | ARP priority level for the bearer or QoS flow. |
| Documentation | Page 31, 86 |

---

## ue_aggregate_max_bitrate_dl

| Property | Value |
|----------|-------|
| Interface | Configuration File |
| Location | `mme.cfg.ue_db.ue_aggregate_max_bitrate_dl` |
| Valid Values | Integer (bits/s) |
| Related Parameters | ue_aggregate_max_bitrate_ul |
| Description | UE aggregate maximum bitrate for downlink. |
| Documentation | Page 39 |

---

## sst

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.nssai.sst` <br> API: `ue_modify_pdu_session.sst` |
| Valid Values | 1 to 255 |
| Related Parameters | sd |
| Description | Slice Service Type for an S-NSSAI. |
| Documentation | Page 22, 88 |

---

## sd

| Property | Value |
|----------|-------|
| Interface | Both |
| Location | Config: `mme.cfg.nssai.sd` <br> API: `ue_modify_pdu_session.sd` |
| Valid Values | 0 to 0xFFFFFFE |
| Related Parameters | sst |
| Description | Slice Differentiator for an S-NSSAI. |
| Documentation | Page 22, 88 |
