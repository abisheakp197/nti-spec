# NTI-1 Conformance Test Suite & Examples

This directory contains official NTI-1 conformance JSON examples and the python validation engine.

## Contents

- `identity.json` — Conformance example for Pillar 1 (Identity), defining a CRYSTALS-Dilithium5 key specification.
- `capability_policy.json` — Conformance example for Pillar 2 (Governance), defining capabilities and caveats.
- `audit_log.json` — Conformance example for Pillar 4 (Audit), defining a SHA-256 Merkle-chained event trail.
- `validate.py` — Automated validator that validates JSON schema conformance and executes Python code blocks across the specification.

## Execution

To validate all conformance examples and run embedded code blocks:

```bash
python3 conformance/validate.py
```
