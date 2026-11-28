# Integrating CanaryGuard with NTI

Status: draft for discussion with Kurox AI. Not yet tested against a CanaryGuard
deployment. CanaryGuard's own figures (sub-10 ms ingress inspection, inspection
receipts with risk scores) are theirs and are treated here as claims to be
verified, not as inputs to any NTI statement.

Enforcement status: `ube-foundation` 0.2.2 adds the `RiskBelow(f32)` caveat, so
the engine evaluates the ingress score itself. Before 0.2.2 the threshold sat at
the integration boundary, in the caller's process.

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
   +-------------------------+
   |      CanaryGuard        |---- risk score + inspection receipt ----+
   |  deterministic ingress  |                                          |
   +-------------------------+                                          |
                |                                                        |
                v                                                        v
   +-------------------------+                                  +------------------+
   |     model / agent       |                                  |  policy at the   |
   |  proposes a tool call   |                                  |  integration edge|
   +-------------------------+                                  +------------------+
                |                                                        |
                | action request + ingress evidence                       | threshold
                v                                                        v
   +---------------------------------------------------------------------------+
   |                             NTI TrustEngine                               |
   |        grants - delegation chain - workload measurement - RiskBelow       |
   +---------------------------------------------------------------------------+
                |
                v
        signed receipt (RFC 0001)
```

Three rules make this composition sound.

1. **The ingress score is evidence, not authority.** CanaryGuard may raise or
   lower suspicion; only the engine's verdict authorises the action.
2. **The score travels inside the signed request.** It goes into `request.input`,
   so it is covered by `receipt_hash`. A score attached after the verdict is a
   claim the caller controls, and the receipt would no longer bind what was
   evaluated to what was decided.
3. **A Deny still produces a receipt.** RFC 0001 requirement R6. A blocked action
   that leaves no record is the case an auditor asks about first.

## Where the score enters the receipt

RFC 0001 fixes the receipt shape. The score belongs in `request`, which is
hashed; it must not become a new top-level field, because a verifier that
re-evaluates the request (R5, step 5) must see exactly what the engine saw.

`risk_score` sits at the top level of `input`, alongside the other caveat inputs
(`amount`, `path`). The CanaryGuard-specific evidence stays nested.

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
      "risk_score": 0.12,
      "canaryguard": {
        "verdict": "clean",
        "inspection_receipt_sha256": "sha256:7c1e...",
        "policy_version": "cg-2026.11"
      }
    }
  },
  "decision": "Allow",
  "reason": "granted",
  "engine": { "impl": "ube-foundation", "version": "0.2.2" },
  "issued_at": "2026-11-26T10:04:11Z",
  "prev_receipt_hash": "sha256:9d5c...",
  "receipt_hash": "sha256:41ab...",
  "signature": "ml-dsa-87:5e8c..."
}
```

`inspection_receipt_sha256` is a hash, not the CanaryGuard receipt itself. The
receipt stays with its producer; NTI commits to it. That keeps the payload small
and keeps each system's evidence verifiable by its own rules.

## How the engine enforces the score

The threshold is a caveat on the capability token. Wire form, externally tagged
and pinned by a round-trip test in the core:

```json
{
  "location": null,
  "condition": { "RiskBelow": 0.65 }
}
```

Attached at token issuance, on the issuing side:

```rust
let mut token = CapabilityToken {
    id: "tok-1".into(),
    root_actor: "issuer".into(),
    capability: "tool:shell".into(),
    caveats: vec![Caveat {
        location: None,
        condition: CaveatType::RiskBelow(0.65),
    }],
    signature: vec![],
};
token.signature = issuer_key.sign(&token.message_to_sign()).to_bytes().to_vec();
```

The engine reads `request.input.risk_score` and decides:

| Condition | Verdict | Reason recorded in the receipt |
| :--- | :--- | :--- |
| `score < threshold` | Allow | the engine's normal allow reason |
| `score >= threshold` | Deny | `caveat violation: Risk score 0.91 at or above threshold 0.65` |
| `risk_score` absent | Deny | `caveat violation: Risk caveat requires a numeric 'risk_score'` |
| `risk_score` not a number | Deny | `caveat violation: Risk caveat requires a numeric 'risk_score'` |
| threshold not finite | Deny | `caveat violation: Risk threshold must be a finite number` |

Equality denies. The last row is defence in depth: `score >= NaN` is false, so an
unguarded NaN threshold would allow everything.

Because the check now happens inside `verify_all_at`, the denial is part of the
same evaluation that produces the receipt. The reason string is covered by
`receipt_hash`, so a verifier re-evaluating the request gets the same answer.

### Signing a token that carries the caveat

The signature covers `(id, root_actor, capability, caveats)` as compact JSON with
object keys sorted, which is what `serde_json` produces without `preserve_order`.
For a threshold of 0.65 the signed bytes are:

```json
["tok-1","issuer","tool:shell",[{"condition":{"RiskBelow":0.6499999761581421},"location":null}]]
```

Note the threshold. `f32` 0.65 widened to `f64` is 0.6499999761581421, and that
is what appears in the signed bytes, while the token on the wire still carries
0.65. An issuer that signs the literal `0.65` produces a token the engine
rejects with `invalid token signature`. This was verified against the published
0.2.2 wheel.

Practical consequence: choose thresholds that are exact in `f32` (0.25, 0.5,
0.75) so the signed form equals the wire form. A threshold such as 0.65 or 0.9
must be signed in its widened form, which is easy to get wrong.

The cleaner long-term fix is an integer representation, for example basis points
(`RiskBelow(u32)`, 6500 = 0.65). That removes the widening entirely, keeps `Eq`
derivable, and makes the signed bytes identical in every implementation. It is
not in 0.2.2; the float form is what shipped.

## What the engine change does not do

**Enforcement requires a token.** `RiskBelow` is a caveat on a capability token.
A deployment that authorises with `grant(actor, capability)` and no token has no
caveats, so no threshold applies. The caveat must be attached where tokens are
issued.

**The Python binding cannot issue tokens.** `ube_foundation` exposes `grant`,
`register_*`, `evaluate`/`evaluate_at` and `audit_inclusion_proof`; there is no
token constructor and no Ed25519 signing, so a Python process cannot attach
`RiskBelow` itself. Options, in order of preference:

1. Issue the token in Rust (or any client holding the issuer key) and pass the
   signed token in the request's `token` field.
2. Keep the boundary check below for Python-only deployments, and say so.

A pure-Python deployment that calls `grant()` and stops there is not enforcing
the risk score, whatever the engine can do.

## Reference snippet

The snippet builds the request so the score is committed, then evaluates. When
the request carries a token with `RiskBelow`, the engine makes the call. The
explicit check is kept as the fallback for the grant-only case described above.

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
            "risk_score": inspection["risk_score"],
            "canaryguard": {
                "verdict": inspection["verdict"],
                "inspection_receipt_sha256": inspection["receipt_sha256"],
                "policy_version": inspection["policy_version"],
            },
        },
    }


def authorize(engine, action_input: dict, inspection: dict, token=None) -> dict:
    # The request is built first so a Deny still records what was evaluated (R6).
    request = build_request(action_input, inspection)
    if token is not None:
        request["token"] = token

    if token is not None:
        # The engine evaluates RiskBelow itself; this is the enforced path.
        raw = engine.evaluate_at(json.dumps(request), datetime.now(timezone.utc).isoformat(), "")
        result = json.loads(raw)
        decision, reason = result["decision"], result["reason"]
    elif inspection["risk_score"] >= RISK_THRESHOLD:
        # Fallback for grant-only deployments, which carry no caveats.
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
        "engine": {"impl": "ube-foundation", "version": "0.2.2"},
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
- The score is compared as `f64` against an `f32` threshold, and the signed
  token bytes contain the widened form of that threshold. A score carrying more
  precision than `f32` can hold may not reproduce on re-evaluation, and a
  threshold that is not exact in `f32` is easy to sign wrongly (see above).
- The snippet builds a receipt-shaped object for illustration. A conformant
  deployment takes the receipt from the engine (R1: one operation returns the
  verdict and its receipt), not from the caller assembling one.
