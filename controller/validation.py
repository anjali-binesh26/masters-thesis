"""
Input validation module for Amarisoft MME Remote API messages.

Validates message dictionaries before transmission to ensure required fields
are present, types are correct, and values are within acceptable bounds.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import re


class ValidationError(Exception):
    """Raised when an API request dictionary fails validation against its schema."""
    pass


# ----------------------------------------------------------------------
# Message Schemas Definition
# ----------------------------------------------------------------------
# Schema layout per message:
#   "parameters": {
#       "<param_name>": {
#           "type": type or tuple of types (e.g. str, int, bool, dict, list),
#           "required": bool (default: False),
#           "min_value": number (optional, for numeric range),
#           "max_value": number (optional, for numeric range),
#           "min_length": int (optional, for strings/sequences),
#           "max_length": int (optional, for strings/sequences),
#           "pattern": str (optional regex, for strings),
#           "choices": list or set (optional allowed enum values),
#           "schema": dict (optional nested object schema),
#           "item_schema": dict (optional schema for items in a list),
#           "validator": callable(val) -> Optional[str] (optional custom check),
#       }
#   },
#   "required_one_of": list of lists (e.g. [["imsi", "nai"]]),
#   "allow_unknown_fields": bool (default: False)

MESSAGE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "ue_get": {
        "parameters": {
            "imsi": {
                "type": str,
                "required": False,
                "min_length": 14,
                "max_length": 15,
                "pattern": r"^\d{14,15}$",
            },
            "nai": {
                "type": str,
                "required": False,
            },
            "imei": {
                "type": str,
                "required": False,
                "min_length": 14,
                "max_length": 16,
            },
            "type": {
                "type": str,
                "required": False,
                "choices": ["3gpp", "n3gpp", "both"],
            },
            "stats": {
                "type": bool,
                "required": False,
            },
            "radio_capabilities": {
                "type": bool,
                "required": False,
            },
        },
        "allow_unknown_fields": False,
    },
    "config_set": {
        "parameters": {
            "relative_capacity": {
                "type": int,
                "required": False,
                "min_value": 0,
                "max_value": 255,
            },
            "log_options": {
                "type": str,
                "required": False,
            },
            "authentication_mode": {
                "type": str,
                "required": False,
                "choices": ["auto", "force", "skip"],
            },
        },
        "allow_unknown_fields": False,
    },
    "config_get": {
        "parameters": {},
        "allow_unknown_fields": False,
    },
    "stats": {
        "parameters": {},
        "allow_unknown_fields": False,
    },
    "ue_modify_bearer": {
        "parameters": {
            "imsi": {
                "type": str,
                "required": True,
            },
            "erab_id": {
                "type": int,
                "required": True,
                "min_value": 1,
            },
            "qos": {
                "type": dict,
                "required": False,
                "schema": {
                    "parameters": {
                        "qci": {
                            "type": int,
                            "required": False,
                            "min_value": 1,
                            "max_value": 255,
                        },
                        "priority_level": {
                            "type": int,
                            "required": False,
                            "min_value": 1,
                            "max_value": 15,
                        },
                        "pre_emption_capability": {
                            "type": str,
                            "required": False,
                            "choices": [
                                "shall_not_trigger_pre_emption",
                                "may_trigger_pre_emption",
                            ],
                        },
                        "pre_emption_vulnerability": {
                            "type": str,
                            "required": False,
                            "choices": [
                                "not_pre_emptable",
                                "pre_emptable",
                            ],
                        },
                    },
                    "allow_unknown_fields": False,
                },
            },
        },
        "allow_unknown_fields": False,
    },
    "ue_activate_dedicated_bearer": {
        "parameters": {
            "imsi": {
                "type": str,
                "required": False,
            },
            "nai": {
                "type": str,
                "required": False,
            },
            "apn": {
                "type": str,
                "required": True,
            },
            "qci": {
                "type": int,
                "required": True,
                "min_value": 1,
                "max_value": 255,
            },
            "gbr": {
                "type": dict,
                "required": False,
            },
            "priority_level": {
                "type": int,
                "required": False,
                "min_value": 1,
                "max_value": 15,
            },
        },
        "required_one_of": [["imsi", "nai"]],
        "allow_unknown_fields": False,
    },
    "ue_modify_pdu_session": {
        "parameters": {
            "imsi": {
                "type": str,
                "required": False,
            },
            "nai": {
                "type": str,
                "required": False,
            },
            "pdu_session_id": {
                "type": int,
                "required": True,
                "min_value": 1,
            },
            "qos_flow": {
                "type": list,
                "required": False,
                "item_schema": {
                    "parameters": {
                        "qfi": {
                            "type": int,
                            "required": False,
                            "min_value": 0,
                            "max_value": 63,
                        },
                        "5qi": {
                            "type": int,
                            "required": False,
                            "min_value": 1,
                            "max_value": 254,
                        },
                    },
                    "allow_unknown_fields": False,
                },
            },
        },
        "required_one_of": [["imsi", "nai"]],
        "allow_unknown_fields": False,
    },
}


# ----------------------------------------------------------------------
# Validation Logic
# ----------------------------------------------------------------------

def _validate_field(field_name: str, value: Any, rule: Dict[str, Any], context_name: str) -> None:
    """Validate a single field's type, range, length, pattern, choices, nested schema, and custom rules."""
    expected_type = rule.get("type")
    if expected_type is not None:
        # Guard: In Python, bool is a subclass of int. Prevent booleans from passing as int.
        if (
            expected_type is int
            or (
                isinstance(expected_type, tuple)
                and int in expected_type
                and bool not in expected_type
            )
        ) and isinstance(value, bool):
            type_repr = (
                expected_type.__name__
                if hasattr(expected_type, "__name__")
                else str(expected_type)
            )
            raise ValidationError(
                f"Field '{field_name}' in '{context_name}' must be of type {type_repr}, got bool."
            )

        if not isinstance(value, expected_type):
            type_repr = (
                expected_type.__name__
                if hasattr(expected_type, "__name__")
                else tuple(t.__name__ for t in expected_type)
                if isinstance(expected_type, tuple)
                else str(expected_type)
            )
            raise ValidationError(
                f"Field '{field_name}' in '{context_name}' must be of type {type_repr}, "
                f"got {type(value).__name__}."
            )

    # Nested object schema validation
    if "schema" in rule and isinstance(value, dict):
        _validate_object(value, rule["schema"], f"{context_name}.{field_name}")

    # List of objects item schema validation
    if "item_schema" in rule and isinstance(value, list):
        for idx, item in enumerate(value):
            if not isinstance(item, dict):
                raise ValidationError(
                    f"Item at index {idx} in '{field_name}' of '{context_name}' must be a dictionary, "
                    f"got {type(item).__name__}."
                )
            _validate_object(item, rule["item_schema"], f"{context_name}.{field_name}[{idx}]")

    # Numeric range validation
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        min_val = rule.get("min_value")
        max_val = rule.get("max_value")
        if min_val is not None and value < min_val:
            raise ValidationError(
                f"Field '{field_name}' value {value} in '{context_name}' is below minimum allowed value of {min_val}."
            )
        if max_val is not None and value > max_val:
            raise ValidationError(
                f"Field '{field_name}' value {value} in '{context_name}' exceeds maximum allowed value of {max_val}."
            )

    # String / sequence length validation
    if isinstance(value, (str, list, dict)):
        min_len = rule.get("min_length")
        max_len = rule.get("max_length")
        if min_len is not None and len(value) < min_len:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} in '{context_name}' is shorter than minimum allowed length {min_len}."
            )
        if max_len is not None and len(value) > max_len:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} in '{context_name}' exceeds maximum allowed length {max_len}."
            )

    # String regex pattern validation
    pattern = rule.get("pattern")
    if pattern and isinstance(value, str):
        if not re.match(pattern, value):
            raise ValidationError(
                f"Field '{field_name}' with value '{value}' in '{context_name}' does not match required pattern '{pattern}'."
            )

    # Choices / enum validation
    choices = rule.get("choices")
    if choices is not None and value not in choices:
        raise ValidationError(
            f"Field '{field_name}' value '{value}' in '{context_name}' is invalid. Allowed choices: {choices}."
        )

    # Custom callable validator
    validator: Optional[Callable[[Any], Optional[str]]] = rule.get("validator")
    if callable(validator):
        error_msg = validator(value)
        if error_msg:
            raise ValidationError(
                f"Field '{field_name}' in '{context_name}' failed validation: {error_msg}"
            )


def _validate_object(data: dict, schema: dict, context_name: str) -> None:
    """Validate a dictionary against an object schema (checking required, one-of, unexpected, and field rules)."""
    param_rules = schema.get("parameters", {})
    allow_unknown = schema.get("allow_unknown_fields", False)

    # 1. Check for missing required parameters
    for param_name, rule in param_rules.items():
        if rule.get("required", False) and param_name not in data:
            raise ValidationError(
                f"Missing required parameter '{param_name}' for '{context_name}'."
            )

    # 2. Check for required_one_of constraint groups
    for group in schema.get("required_one_of", []):
        if not any(field in data for field in group):
            group_str = " or ".join(f"'{f}'" for f in group)
            raise ValidationError(
                f"Message '{context_name}' requires at least one of: {group_str}."
            )

    # 3. Check for unexpected / unknown fields
    if not allow_unknown:
        for param_name in data:
            if param_name not in param_rules:
                allowed_keys = list(param_rules.keys())
                raise ValidationError(
                    f"Unexpected parameter '{param_name}' for '{context_name}'. Allowed parameters: {allowed_keys}."
                )

    # 4. Validate each supplied parameter against its rules
    for param_name, value in data.items():
        if param_name in param_rules:
            _validate_field(param_name, value, param_rules[param_name], context_name)


def validate_message(request: dict) -> None:
    """
    Validate a message dictionary before sending to AmarisoftAPI.

    Parameters:
        request (dict): The request payload containing at least a 'message' key.

    Raises:
        ValidationError: If request is not a dict, 'message' is missing/invalid,
                         an unknown message is specified, required fields are missing,
                         types mismatch, or values are out of range.
    """
    if not isinstance(request, dict):
        raise ValidationError(f"Request must be a dictionary, got {type(request).__name__}.")

    raw_message = request.get("message")
    if not raw_message or not isinstance(raw_message, str):
        raise ValidationError("Request dictionary must contain a non-empty string 'message' key.")

    message_name = raw_message.strip().lower()

    if message_name not in MESSAGE_SCHEMAS:
        valid_types = list(MESSAGE_SCHEMAS.keys())
        raise ValidationError(
            f"Unknown or unsupported message type '{raw_message}'. Supported types: {valid_types}."
        )

    # Validate optional top-level 'message_id' if present
    if "message_id" in request:
        msg_id = request["message_id"]
        if not isinstance(msg_id, (int, str)):
            raise ValidationError(
                f"'message_id' must be an integer or string, got {type(msg_id).__name__}."
            )

    schema = MESSAGE_SCHEMAS[message_name]

    # Extract parameters to validate
    # Supports both top-level fields (e.g. {"message": "...", "imsi": "..."})
    # and nested parameters dictionary (e.g. {"message": "...", "parameters": {"imsi": "..."}})
    if "parameters" in request:
        if not isinstance(request["parameters"], dict):
            raise ValidationError(
                f"'parameters' field must be a dictionary, got {type(request['parameters']).__name__}."
            )
        params_to_validate = dict(request["parameters"])
        top_extra = {k: v for k, v in request.items() if k not in ("message", "message_id", "parameters")}
        params_to_validate.update(top_extra)
    else:
        params_to_validate = {k: v for k, v in request.items() if k not in ("message", "message_id")}

    _validate_object(params_to_validate, schema, raw_message)
