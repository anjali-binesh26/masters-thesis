# QoS Configuration Parameters

This document identifies the configuration parameters required to modify the Quality of Service (QoS) settings within the Amarisoft 5G Core network, based on the provided technical documentation.

## Parameter: qci (Global PDN/ERAB)

**Configuration File**

`mme.cfg`

**Configuration Section**

`pdn_list` $\rightarrow$ `erabs`

**Purpose**

Defines the QoS Class Identifier (QCI) for an E-RAB associated with a specific PDN. It determines the packet delay budget, packet error loss rate, and priority.

**Valid Values**

Integer range: 1 to 255.

**Default Value**

Undocumented.

**Dependencies**

Related to `priority_level`, `pre_emption_capability`, and `pre_emption_vulnerability` within the same `erabs` object.

**Constraints**

Must be a valid QCI as per 3GPP standards for the corresponding bearer type.

**Restart Required**

Undocumented.

**Example**

```cfg
pdn_list: [
  {
    access_point_name: "internet",
    erabs: [
      {
        qci: 9,
        priority_level: 15,
      },
    ],
  },
]
```

**Documentation Reference**

Page 31, Section 5.2.1 (PDN options).

**Confidence**

Documented

---

## Parameter: 5qi (Global PDN/Slice)

**Configuration File**

`mme.cfg`

**Configuration Section**

`pdn_list` $\rightarrow$ `slices` $\rightarrow$ `qos_flows`

**Purpose**

Defines the 5G QoS Identifier (5QI) for a QoS flow within a network slice. This is the 5GC equivalent of QCI.

**Valid Values**

Integer range: 1 to 255.

**Default Value**

Undocumented.

**Dependencies**

Associated with a specific `snssai` (S-NSSAI) within the slice configuration.

**Constraints**

Must be compatible with the 5G QoS flow requirements.

**Restart Required**

Undocumented.

**Example**

```cfg
slices: [
  {
    snssai: { sst: 1 },
    qos_flows: [
      {
        "5qi": 6,
        priority_level: 9,
      },
    ],
  },
]
```

**Documentation Reference**

Page 37, Section 5.2.1 (PDN options).

**Confidence**

Documented

---

## Parameter: priority_level

**Configuration File**

`mme.cfg` (and `ue_db.cfg`)

**Configuration Section**

`pdn_list` $\rightarrow$ `erabs` OR `pdn_list` $\rightarrow$ `slices` $\rightarrow$ `qos_flows`

**Purpose**

Sets the Allocation and Retention Priority (ARP) level. Lower values indicate higher priority.

**Valid Values**

Integer range: 1 to 15.

**Default Value**

Undocumented.

**Dependencies**

Used in conjunction with `pre_emption_capability` and `pre_emption_vulnerability`.

**Constraints**

None specified beyond the range.

**Restart Required**

Undocumented.

**Example**

```cfg
erabs: [
  {
    qci: 9,
    priority_level: 15,
  },
]
```

**Documentation Reference**

Page 31 and Page 37, Section 5.2.1.

**Confidence**

Documented

---

## Parameter: pre_emption_capability

**Configuration File**

`mme.cfg` (and `ue_db.cfg`)

**Configuration Section**

`pdn_list` $\rightarrow$ `erabs` OR `pdn_list` $\rightarrow$ `slices` $\rightarrow$ `qos_flows`

**Purpose**

Part of the ARP settings. Defines whether the bearer can pre-empt other bearers with lower priority.

**Valid Values**

Enumeration: `shall_not_trigger_pre_emption`, `can_trigger_pre_emption` (inferred from context/standard 3GPP).

**Default Value**

Undocumented.

**Dependencies**

Linked to `priority_level`.

**Constraints**

Must be a valid ARP capability value.

**Restart Required**

Undocumented.

**Example**

```cfg
erabs: [
  {
    pre_emption_capability: "shall_not_trigger_pre_emption",
  },
]
```

**Documentation Reference**

Page 31 and Page 37, Section 5.2.1.

**Confidence**

Documented

---

## Parameter: pre_emption_vulnerability

**Configuration File**

`mme.cfg` (and `ue_db.cfg`)

**Configuration Section**

`pdn_list` $\rightarrow$ `erabs` OR `pdn_list` $\rightarrow$ `slices` $\rightarrow$ `qos_flows`

**Purpose**

Part of the ARP settings. Defines whether the bearer can be pre-empted by other bearers.

**Valid Values**

Enumeration: `not_pre_emptable`, `pre_emptable`.

**Default Value**

Undocumented.

**Dependencies**

Linked to `priority_level`.

**Constraints**

Must be a valid ARP vulnerability value.

**Restart Required**

Undocumented.

**Example**

```cfg
erabs: [
  {
    pre_emption_vulnerability: "not_pre_emptable",
  },
]
```

**Documentation Reference**

Page 31 and Page 37, Section 5.2.1.

**Confidence**

Documented

---

## Parameter: gbr (Guaranteed Bit Rate)

**Configuration File**

`mme.cfg`

**Configuration Section**

`pdn_list` $\rightarrow$ `erabs` $\rightarrow$ `gbr`

**Purpose**

An optional object used to configure the bitrates for Guaranteed Bit Rate (GBR) bearers.

**Valid Values**

Object containing:
- `maximum_bitrate_dl`: Integer (bits/s)
- `maximum_bitrate_ul`: Integer (bits/s)
- `guaranteed_bitrate_dl`: Integer (bits/s)
- `guaranteed_bitrate_ul`: Integer (bits/s)

**Default Value**

Undocumented.

**Dependencies**

Only applicable if the `qci` assigned to the bearer is a GBR-capable QCI.

**Constraints**

Bitrate values must be positive integers.

**Restart Required**

Undocumented.

**Example**

```cfg
erabs: [
  {
    qci: 1,
    gbr: {
      guaranteed_bitrate_dl: 128000,
      guaranteed_bitrate_ul: 64000,
      maximum_bitrate_dl: 1000000,
      maximum_bitrate_ul: 500000,
    },
  },
]
```

**Documentation Reference**

Page 33, Section 5.2.1.

**Confidence**

Documented

---

## Parameter: ue_aggregate_max_bitrate_dl / ul

**Configuration File**

`ue_db.cfg` (User database file)

**Configuration Section**

`ue_db` $\rightarrow$ [User Object]

**Purpose**

Sets the UE Aggregate Maximum Bit Rate (UE-AMBR) for downlink and uplink. This limits the total bandwidth a specific UE can consume across all non-GBR bearers.

**Valid Values**

Integer (bits/s).

**Default Value**

Undocumented.

**Dependencies**

Overwrites the default network-wide QoS settings for the specific UE.

**Constraints**

Must be a positive integer.

**Restart Required**

Undocumented.

**Example**

```cfg
ue_db: [
  {
    imsi: "123456789012345",
    ue_aggregate_max_bitrate_dl: 10000000,
    ue_aggregate_max_bitrate_ul: 5000000,
  },
]
```

**Documentation Reference**

Page 39, Section 5.2.2 (User database options).

**Confidence**

Documented

---

## Parameter: qci_dscp_mapping

**Configuration File**

`mme.cfg`

**Configuration Section**

Top-level Properties

**Purpose**

Allows the definition of a specific IP-layer Differentiated Services Code Point (DSCP) value for a specific QCI or 5QI.

**Valid Values**

An array of objects, each containing:
- `qci`: Integer (1 to 254)
- `dscp`: Integer (0 to 255)

**Default Value**

Default DSCP is 0 if not explicitly configured.

**Dependencies**

Affects how packets are marked in the user plane.

**Constraints**

QCI/5QI must be within the 1-254 range.

**Restart Required**

Undocumented.

**Example**

```cfg
qci_dscp_mapping: [
  { qci: 1, dscp: 46 },
  { qci: 9, dscp: 0 },
]
```

**Documentation Reference**

Page 21, Section 5.2.

**Confidence**

Documented
