# Supported UC1 contract

Authority: local ltemme.pdf, version 2024-06-15. Page numbers below are PRINTED
manual pages, three less than their PDF viewer positions. This is a bounded
implementation policy; omission does not mean the vendor lacks the feature.

## Read operations
- config_get: no parameters (pp. 59-60). Returned logs.layers.<layer>.<field>
  supports logging read-back; do NOT assume it returns all global settings.
- ue_get: optional imsi OR nai, optional imei (14/15 digits), type
  (3gpp/n3gpp/both), radio_capabilities boolean (pp. 77-79).
  ue_list contains imsi/nai, imeisv, rat_type, registered, t3512 for registered
  NR UEs, t3412 for registered EPS UEs, and bearers. A 5GS bearer/session has
  pdu_session_id, qos_flow_id (default flow), and dedicated entries containing
  qos_flow_id for non-default flows. There is no documented 5QI read-back here.
- stats: no parameters.
- log_get: optional min/max, timeout in seconds, allow_empty, ue_id, layers,
  short, headers, max_size, start_timestamp/end_timestamp (milliseconds).
  For bounded reads use min=0, max=100, timeout=1, allow_empty=true (pp. 72-73).

## config_set supported fields
- logs.layers.<explicit layer>.level: none/error/info/debug.
- logs.layers.<explicit layer>.max_size: integer >= -1.
- logs.layers.<explicit layer>.key/crypto/payload/verbose: boolean.
- Layers: nas, ip, s1ap, ngap, gtpu, rx, s6, cx, s13, sgsap, sbcap,
  lcsap, lppa, n12, n13, n8, n17, n50, n5, nl1, nrppa, epdg, ikev2, ipsec, n20.
  Wildcard all is intentionally not supported; use explicit layers.
- relative_capacity: integer 0..255 (p. 60).
- authentication_mode: auto/force/skip (p. 66); security-affecting CORE-WIDE
  operation, not a routine connectivity test.
- t3402, t3412, t3412_low_priority, t3512: seconds, integer >= -1 (p. 62).
- t3501: integer 1..30 seconds (p. 62).
- psm, mico_support: boolean (p. 62).
These are core-wide changes. No qci, 5qi, gbr, pdn_list QoS or log_options string
is accepted under config_set. The JSON logging field is logs, not log_options.
Timer values received by UEs may depend on their requests/subscriber overrides.

## QoS modification proposals
ue_modify_pdu_session (pp. 87-88): imsi OR nai, optional imei, pdu_session_id
(integer 1..15), qos_flow (nonempty list). Each proposal item must contain qfi
(integer 0..63) plus requested changes among 5qi (1..254), priority_level (1..15),
pre_emption_capability, pre_emption_vulnerability, gbr, 5qi_qos.
The controller currently permits 5QI transitions only within non-GBR profiles
5..9. Other transitions need an explicitly qualified resource-type policy.
Changes to ARP/GBR of an existing baseline are supported subject to validation.

ue_modify_bearer (pp. 86-87): imsi, optional imei, erab_id (5..15), qos object
containing the requested qci/ARP/GBR changes. EPS only. QCI transitions currently
have the same 5..9 operational restriction.

ARP enums:
- pre_emption_capability: shall_not_trigger_pre_emption / may_trigger_pre_emption
- pre_emption_vulnerability: not_pre_emptable / pre_emptable
GBR object (p. 33): maximum_bitrate_dl, maximum_bitrate_ul,
guaranteed_bitrate_dl, guaranteed_bitrate_ul: positive integer bits/s;
guaranteed must not exceed maximum in each direction.
The final wire flow needs qfi, 5qi, priority_level and both pre-emption fields;
missing unchanged values come from the operator baseline, never guesses.
No flow creation/deletion, default-flow replacement or qos_rules edits are supported.

## Output examples (values illustrative, never substitute them for missing inputs)
Logging request: {"message":"config_set","logs":{"layers":{"nas":{"level":"info"}}}}
Timer request: {"message":"config_set","t3512":600}
QoS patch: {"message":"ue_modify_pdu_session","imsi":"001010123456789",
"imei":"12345678901234","pdu_session_id":1,"qos_flow":[{"qfi":2,"5qi":8}]}
