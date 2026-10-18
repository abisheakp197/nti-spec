#!/usr/bin/env python3
"""
NTI-1 Conformance Validator & Code Block Runner
Verifies conformance examples and executes all Python code blocks embedded in Markdown specifications.
"""

import glob
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def validate_conformance_examples() -> None:
    """Validate JSON structure and Merkle chain integrity of conformance examples."""
    identity_path = ROOT_DIR / "conformance" / "identity.json"
    policy_path = ROOT_DIR / "conformance" / "capability_policy.json"
    audit_path = ROOT_DIR / "conformance" / "audit_log.json"

    print("Checking conformance examples...")

    # 1. Identity validation
    with open(identity_path, "r", encoding="utf-8") as f:
        identity = json.load(f)
    required_identity_keys = {"agent_id", "algorithm", "public_key_pem", "revocation_status", "created_at"}
    if not required_identity_keys.issubset(identity.keys()):
        raise ValueError(f"identity.json missing required keys: {required_identity_keys - set(identity.keys())}")
    if identity["algorithm"] != "CRYSTALS-Dilithium5":
        raise ValueError("identity.json must specify CRYSTALS-Dilithium5 algorithm")

    # 2. Policy validation
    with open(policy_path, "r", encoding="utf-8") as f:
        policy = json.load(f)
    required_policy_keys = {"policy_id", "agent_id", "granted_capabilities"}
    if not required_policy_keys.issubset(policy.keys()):
        raise ValueError(f"capability_policy.json missing required keys: {required_policy_keys - set(policy.keys())}")

    # 3. Audit trail Merkle chain validation
    with open(audit_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    if not isinstance(events, list) or len(events) == 0:
        raise ValueError("audit_log.json must contain a non-empty list of events")

    expected_parent = "0" * 64
    for idx, event in enumerate(events):
        if event["parent_hash"] != expected_parent:
            raise ValueError(f"Audit log chain broken at index {idx}: expected parent {expected_parent}, got {event['parent_hash']}")

        payload = f"{event['event_id']}:{event['agent_id']}:{event['request_hash']}:{event['decision']}:{event['reason']}:{event['timestamp']}:{event['parent_hash']}"
        calculated_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

        if calculated_hash != event["event_hash"]:
            raise ValueError(f"Audit log hash mismatch at index {idx}: expected {calculated_hash}, got {event['event_hash']}")

        expected_parent = event["event_hash"]

    print("✓ Conformance examples successfully validated.")


def run_code_blocks() -> None:
    """Extract and execute all Python code blocks from Markdown files."""
    print("Extracting and executing Python code blocks...")

    md_files = glob.glob(str(ROOT_DIR / "**" / "*.md"), recursive=True)
    block_count = 0

    for filepath in md_files:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Find code blocks marked with ```python ... ```
        blocks = re.findall(r"```python\s*\n(.*?)```", content, re.DOTALL)
        for idx, block in enumerate(blocks, start=1):
            block_count += 1
            print(f"  Executing Python block {idx} in {Path(filepath).relative_to(ROOT_DIR)}...")

            # Prepare global namespace for execution
            global_ns = {}
            try:
                exec(block, global_ns)
            except Exception as e:
                print(f"❌ Error executing block {idx} in {filepath}: {e}", file=sys.stderr)
                raise

    print(f"✓ Executed {block_count} Python code blocks with 0 errors.")


def main() -> None:
    try:
        validate_conformance_examples()
        run_code_blocks()
        print("\nAll conformance checks passed successfully!")
    except Exception as err:
        print(f"\n❌ Validation failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
