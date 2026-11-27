# Integrating CanaryGuard with NTI

Status: draft for discussion with Kurox AI. Not yet tested against a CanaryGuard
deployment. CanaryGuard's own figures (sub-10 ms ingress inspection, inspection
receipts with risk scores) are theirs and are treated here as claims to be
verified, not as inputs to any NTI statement.

## The division of labour

The two systems answer different questions and should not be merged.

| | CanaryGuard | NTI |
| :--- | :--- | :--- |
| Direction | Ingress | Egress |
| Question | Is this content safe to let in? | Is this agent allowed to take this action? |
| Input | Prompts, retrieved documents, tool output, scripts | Action request, grants, delegation chain, workload measurement |
| Output | Sanitised content, risk score, inspection receipt | Allow/Deny verdict, signed receipt |
| Failure mode | Malicious content reaches the model | Unauthorised action leaves the process |

Neither substitutes for the other. A clean prompt does not authorise a payment,
and an authorised payment does not make its arguments safe to execute.

## Architecture

```text
        untrusted content
                |
                v
   +-------------------------+        risk score + inspection receipt
   |      CanaryGuard        |------------------------------+
   |  deterministic ingress  |                              |
   +-------------------------+                              |
                |                                           |
                v                                           v
   +-------------------------+                    +---------------------+
   |     model / agent       |                    |  policy at the      |
   |  proposes a tool call   |                    |  integration edge   |
   +-------------------------+                    +---------------------+
                |                                           |
                | action request + ingress evidence         | threshold
                v                                           v
   +---------------------------------------------------------------+
   |                        NTI TrustEngine                        |
   |   grants - delegation chain - workload measurement - verdict  |
   +---------------------------------------------------------------+
                |
                v
        signed receipt (RFC 0001)
```

Three rules make this composition sound.

1. **The ingress score is evidence, not authority.** CanaryGuard may raise or
   lower suspicion; only the engine's verdict authorises the action.
2. **The score travels inside the signed request.** It goes into `request.input`,
   so it is covered by `receipt_hash`. A score that is attached after the verdict
   is a claim the caller controls, and the receipt would no longer bind what was
   evaluated to what was decided.
3. **A Deny still produces a receipt.** RFC 0001 requirement R6. A blocked action
   that leaves no record is the case an auditor asks about first.

## Where the score enters the receipt

RFC 0001 fixes the receipt shape. The score belongs in `request`, which is
hashed; it must not become a new top-level field, because a verifier that
re-evaluates the request (R5, step 5) must see exactly what the engine saw.

```json
{
  "nti": "1.0",
  "receipt_id": "6f1c0a52-2d5b-4c0e-9b2f-3f9a1b7c8d40",
  "request": {
    "id": "r-42",
    "actor": "did:webvh:agent-7:agents.example.com",
    "capability": "tool:shell",
    "action": "bash",
    "input": {
      "command": "ls -la",
      "canaryguard": {
        "risk_score": 0.12,
        "verdict": "clean",
        "inspection_receipt_sha256": "sha256:7c1e...",
        "policy_version": "cg-2026.11"
      }
    }
  },
  "decision": "Allow",
  "reason": "granted",
  "engine": { "impl": "ube-foundation", "version": "0.2.1" },
  "issued_at": "2026-11-26T10:04:11Z",
  "prev_receipt_hash": "sha256:9d5c...",
  "receipt_hash": "sha256:41ab...",
  "signature": "ml-dsa-87:5e8c..."
}
```

`inspection_receipt_sha256` is a hash, not the CanaryGuard receipt itself. The
receipt stays with its producer; NTI commits to it. That keeps the payload small
and keeps each system's evidence verifiable by its own rules.

## Reference snippet

```python
import hashlib
import json
import uuid
from datetime import datetime, timezone

import ube_foundation

ACTOR = "did:webvh:agent-7:agents.example.com"
RISK_THRESHOLD = 0.65


def canonical(obj) -> bytes:
    # RFC 8785 JCS. For the value types used here (strings, ints, floats,
    # nested objects) sorted keys with compact separators agrees with JCS.
    # A conforming implementation must use a JCS library.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def receipt_hash(receipt: dict) -> str:
    body = {k: v for k, v in receipt.items() if k not in ("receipt_hash", "signature")}
    return "sha256:" + hashlib.sha256(canonical(body)).hexdigest()


def build_request(action_input: dict, inspection: dict) -> dict:
    """Embed the ingress evidence so the receipt commits to it."""
    return {
        "id": "r-42",
        "actor": ACTOR,
        "capability": "tool:shell",
        "action": "bash",
        "input": {
            **action_input,
            "canaryguard": {
                "risk_score": inspection["risk_score"],
                "verdict": inspection["verdict"],
                "inspection_receipt_sha256": inspection["receipt_sha256"],
                "policy_version": inspection["policy_version"],
            },
        },
    }


def authorize(engine, action_input: dict, inspection: dict) -> dict:
    # The request is built first so a Deny still records what was evaluated (R6).
    request = build_request(action_input, inspection)

    # Boundary policy: a high-risk ingress blocks before the engine is asked.
    # See "What is missing" below for why this is not a caveat yet.
    if inspection["risk_score"] >= RISK_THRESHOLD:
        decision, reason = "Deny", "ingress risk above threshold"
    else:
        raw = engine.evaluate_at(json.dumps(request), datetime.now(timezone.utc).isoformat(), "")
        result = json.loads(raw)
        decision, reason = result["decision"], result["reason"]

    receipt = {
        "nti": "1.0",
        "receipt_id": str(uuid.uuid4()),
        "request": request,
        "decision": decision,
        "reason": reason,
        "engine": {"impl": "ube-foundation", "version": "0.2.1"},
        "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prev_receipt_hash": None,
    }
    receipt["receipt_hash"] = receipt_hash(receipt)
    return receipt


if __name__ == "__main__":
    engine = ube_foundation.TrustEngine()
    engine.grant(ACTOR, "tool:shell")
    clean = {"risk_score": 0.12, "verdict": "clean",
             "receipt_sha256": "sha256:7c1e", "policy_version": "cg-2026.11"}
    risky = {"risk_score": 0.91, "verdict": "injection",
             "receipt_sha256": "sha256:aa01", "policy_version": "cg-2026.11"}
    print(json.dumps(authorize(engine, {"command": "ls -la"}, clean), indent=2)[:400])
    print("high risk ->", authorize(engine, {"command": "ls -la"}, risky)["reason"])
```

## What is missing, and it is the important part

**The engine cannot evaluate a risk score today.** `CaveatType` in
`ube-foundation` 0.2.1 is `Expires`, `MaxExecutions`, `ValueLimit`,
`PathRestricted`. There is no risk caveat, so the threshold check above sits at
the integration boundary, in the caller's process.

That is a real gap, not a detail. A boundary check is code the caller can skip;
a caveat is evaluated by the engine and appears in the receipt's `reason`. Until
a caveat exists, the honest description of this integration is:

> CanaryGuard's score is committed into the signed request, so tampering with it
> is detectable. It is *enforced* by the integrating policy layer, not by the
> engine.

The natural core change is a fifth variant, roughly:

```rust
/// Deny when the caller-supplied risk score is at or above this value.
RiskBelow(f32),
```

evaluated against `request.input` before dispatch, with the observed score
recorded in the receipt's `reason`. That would move enforcement inside the
binding property, which is the only place it is worth having.

## Open questions for Kurox AI

1. Does CanaryGuard sign its inspection receipt, and with which algorithm? NTI
   commits to a hash, so the verifier needs the receipt and its key to close the
   loop.
2. Is `risk_score` deterministic for identical input? A score that drifts across
   replays breaks RFC 0001 R5 step 5, where a verifier re-evaluates the request.
3. What is the score's range and meaning at the boundaries, so a threshold has a
   defined interpretation rather than a tuned one?
4. Can the inspection receipt be fetched by a third party, or is it only
   available to the caller? Independent verification requires the former.

## Limits of this document

- No joint test exists. Nothing here has been run against a CanaryGuard instance.
- The latency claim (sub-10 ms) is theirs; NTI adds one engine evaluation per
  action, which is not free and should be measured in the same harness.
- The snippet builds a receipt-shaped object for illustration. A conformant
  deployment takes the receipt from the engine (R1: one operation returns the
  verdict and its receipt), not from the caller assembling one.
