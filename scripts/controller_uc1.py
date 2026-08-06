import re
from pathlib import Path

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

NETSIGHT_ROOT = Path("/home/student/NetSight Thesis/netsight")
INTERFACE_FILE = NETSIGHT_ROOT / "output" / "interfaces.md"


# ------------------------------------------------------------------
# Parse Markdown
# ------------------------------------------------------------------

def parse_interfaces(md_file):

    text = md_file.read_text(encoding="utf-8")

    sections = re.split(r"\n## ", text)

    interfaces = []

    for section in sections[1:]:

        lines = section.strip().splitlines()

        parameter = lines[0].strip()

        props = {}

        for line in lines:

            if not line.startswith("|"):
                continue

            cols = [c.strip() for c in line.strip("|").split("|")]

            if len(cols) != 2:
                continue

            key, value = cols

            if key == "Property" or key.startswith("---"):
                continue

            props[key] = value

        interfaces.append({

            "parameter": parameter,
            "configuration": props.get("Configuration", "N/A"),
            "runtime_api": props.get("Runtime API", "N/A"),
            "required_inputs": props.get("Required Inputs", ""),
            "constraints": props.get("Constraints", ""),
            "related_parameters": props.get("Related Parameters", ""),
            "purpose": props.get("Purpose", ""),
            "documentation": props.get("Documentation", "")

        })

    return interfaces


# ------------------------------------------------------------------
# Display Parameters
# ------------------------------------------------------------------

def display_parameters(interfaces):

    print("\nParameters identified by NetSight\n")

    for i, p in enumerate(interfaces, start=1):

        print(f"{i}. {p['parameter']}")
        print(f"   Purpose        : {p['purpose']}")
        print(f"   Constraints    : {p['constraints']}")
        print(f"   Configuration  : {p['configuration']}")
        print(f"   Runtime API    : {p['runtime_api']}")
        print()

    selection = input(
        "Select parameter(s) to modify (number or name, comma separated): "
    )

    selected = []

    for token in selection.split(","):

        token = token.strip()

        if token.isdigit():

            idx = int(token) - 1

            if 0 <= idx < len(interfaces):
                selected.append(interfaces[idx])

        else:

            for interface in interfaces:

                if interface["parameter"].lower() == token.lower():

                    selected.append(interface)
                    break

    return selected


# ------------------------------------------------------------------
# Collect User Inputs
# ------------------------------------------------------------------

def collect_inputs(selected):

    operations = []

    for p in selected:

        print("\n" + "=" * 60)
        print(f"Parameter      : {p['parameter']}")
        print(f"Purpose        : {p['purpose']}")
        print(f"Constraints    : {p['constraints']}")
        print(f"Configuration  : {p['configuration']}")
        print(f"Runtime API    : {p['runtime_api']}")
        print()

        required_inputs = {}

        if p["required_inputs"]:

            fields = re.split(r",|\bor\b", p["required_inputs"])

            for field in fields:

                field = field.replace("`", "").strip()

                if not field:
                    continue

                value = input(f"{field}: ")

                required_inputs[field] = value

        new_value = input(f"New value for {p['parameter']}: ")

        operations.append({

            "parameter": p["parameter"],
            "configuration": p["configuration"],
            "runtime_api": p["runtime_api"],
            "required_inputs": required_inputs,
            "new_value": new_value

        })

    return operations


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    interfaces = parse_interfaces(INTERFACE_FILE)

    if not interfaces:
        print("No interface definitions found.")
        return

    selected = display_parameters(interfaces)

    if not selected:
        print("\nNo parameters selected.")
        return

    actions = collect_inputs(selected)

    print("\n" + "=" * 60)
    print("Generated Controller Actions")
    print("=" * 60)

    for action in actions:

        print()

        for key, value in action.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()