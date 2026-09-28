# Amarisoft reference excerpts: logging

Source: lab-supplied ltemme.pdf, version 2024-06-15.
This is a checked paraphrase of relevant sections, not the complete manual.
Page numbers below are printed pages; PDF viewer positions are three higher.
Use uc1_api_reference.md for the narrower set supported by the controller.

## Section 6.5: config_get (printed pages 59-60)
- config_get retrieves configuration. The MME response identifies its type as MME.
- Logging settings appear under logs.layers.
- Each layer is an object with fields such as level, max_size, key, crypto and payload; verbose may also be present.
- An optional logs.locked value of true means logging configuration cannot be changed through config_set.
- Do not assume config_get exposes every configurable core parameter.

## Section 6.5: config_set (printed page 60)
- config_set changes runtime configuration; its members are optional.
- Its logs object uses the logging structure described for config_get.
- Logging elements are optional, so specify only the requested fields.
- The vendor supports a layer name of all; the controller intentionally does not support that wildcard.
- A locked logging configuration can be reported by a logs value of locked in the response.

## Section 5.2: log_options definitions (printed pages 9-10)
- level: none, error, info or debug. Debug includes transmitted-data content.
- max_size: the maximum bytes shown in hexadecimal when dumping content. ASN.1, NAS and Diameter have special handling: a positive value enables full decoded message content.
- payload controls hexadecimal payload dumps for the documented protocols.
- key controls security-key logging; crypto controls plain/ciphered-data logging where applicable.
- verbose is described for IPSEC packet-filtering information.
- These definitions explain logging fields. The static log_options string syntax is not the Remote API JSON structure.

## Illustrative JSON structure
This is an example, not the current operator instruction. Do not copy its layer or value unless requested.

```json
{"message":"config_set","logs":{"layers":{"nas":{"level":"info"}}}}
```

Remote API requests use logs.layers.<layer>.<field>. They do not use a log_options string.
The original manual remains the full source for operations outside these excerpts.

