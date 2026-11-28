# Integrating CanaryGuard with NTI

Status: draft for discussion with Kurox AI. Not yet tested against a CanaryGuard
deployment. CanaryGuard's own figures (sub-10 ms ingress inspection, inspection
receipts with risk scores) are theirs and are treated here as claims to be
verified, not as inputs to any NTI statement.

Enforcement status: `ube-foundation` 0.3.0 adds `RiskBelow(u32)`, a threshold in
basis points, so the engine evaluates the ingress score itself. Python callers
can issue the token that carries it with `TokenBuilder`; before 0.3.0 the Python
binding had no token issuance and the threshold sat at the integration boundary,
in the caller's process.

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
   |                              NTI TrustEngine                              |
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
  "engine": { "impl": "ube-foundation", "version": "0.3.0" },
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

The threshold is a caveat on the capability token, expressed in basis points:
6500 is 0.65. Wire form, externally tagged and pinned by a round-trip test in
the core:

```json
{
  "location": null,
  "condition": { "RiskBelow": 6500 }
}
```

Attached at token issuance. In Rust:

```rust
let mut token = CapabilityToken {
    id: "tok-1".into(),
    root_actor: "issuer".into(),
    capability: "tool:shell".into(),
    caveats: vec![Caveat {
        location: None,
        condition: CaveatType::RiskBelow(6500),
    }],
    signature: vec![],
};
token.signature = issuer_key.sign(&token.message_to_sign()).to_bytes().to_vec();
```

In Python, with the issuer key:

```python
import json

import ube_foundation

issuer = "did:webvh:issuer:agents.example.com"
key = ube_foundation.Ed25519KeyPair()

builder = ube_foundation.TokenBuilder("tok-1", issuer, "tool:shell")
builder.risk_below(6500)
token = json.loads(builder.sign(key.private_key_bytes()))
assert token["caveats"] == [{"location": None, "condition": {"RiskBelow": 6500}}]
```

The engine reads `request.input.risk_score`, requires a finite number on the
0.0 to 1.0 scale, converts it to basis points by rounding to the nearest one, and
compares integers:

| Condition | Verdict | Reason recorded in the receipt |
| :--- | :--- | :--- |
| `score_bps < threshold_bps` | Allow | the engine's normal allow reason |
| `score_bps >= threshold_bps` | Deny | `caveat violation: Risk score 9100 bps at or above threshold 6500 bps` |
| `risk_score` absent | Deny | `caveat violation: Risk caveat requires a numeric 'risk_score'` |
| `risk_score` not a number | Deny | `caveat violation: Risk caveat requires a numeric 'risk_score'` |
| `risk_score` outside 0.0..=1.0 | Deny | `caveat violation: Risk score 65 must be a finite number in 0.0..=1.0` |
| threshold above 10000 bps | Deny | `caveat violation: Risk threshold out of range: 20000 basis points must be 0..=10000` |

Equality denies. The scale check matters: a producer that passes 65 meaning 65
percent would otherwise be read as a score of 65 and fail open, so an
out-of-scale value is a violation instead.

### Signed bytes are the wire form

The signature covers `(id, root_actor, capability, caveats)` as compact JSON with
object keys sorted, which is what `serde_json` produces without `preserve_order`.
With an integer threshold the signed bytes are exactly the token's caveat as
written:

```json
["tok-1","issuer","tool:shell",[{"condition":{"RiskBelow":6500},"location":null}]]
```

This is the change from 0.2.2. There the threshold was an `f32`, and `0.65`
widened to `f64` and signed as `0.6499999761581421`, so an issuer that signed the
literal value produced a token the engine rejected. Basis points remove the
widening: the value in the JSON is the value that is signed, in every language.

## Reference snippet

Issue a token with the caveat, then let the engine decide. The receipt is
assembled from the verdict so a Deny is recorded with the same evidence as an
Allow.

```python
import hashlib
import json
import uuid
from datetime import datetime, timezone

import ube_foundation

ISSUER = "did:webvh:issuer:agents.example.com"
ACTOR = "did:webvh:agent-7:agents.example.com"
CAPABILITY = "tool:shell"
RISK_THRESHOLD_BPS = 6500  # 0.65


def canonical(obj) -> bytes:
    # RFC 8785 JCS. For the value types used here (strings, ints, floats,
    # nested objects) sorted keys with compact separators agrees with JCS.
    # A conforming implementation must use a JCS library.
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def receipt_hash(receipt: dict) -> str:
    body = {k: v for k, v in receipt.items() if k not in ("receipt_hash", "signature")}
    return "sha256:" + hashlib.sha256(canonical(body)).hexdigest()


def issue_token(issuer_key, threshold_bps: int) -> dict:
    builder = ube_foundation.TokenBuilder("tok-" + uuid.uuid4().hex[:8], ISSUER, CAPABILITY)
    builder.risk_below(threshold_bps)
    return json.loads(builder.sign(issuer_key.private_key_bytes()))


def authorize(engine, action_input: dict, inspection: dict, token: dict) -> dict:
    """Embed the ingress evidence, ask the engine, record what it decided."""
    request = {
        "id": "r-42",
        "actor": ACTOR,
        "capability": CAPABILITY,
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
        "token": token,
    }

    now = datetime.now(timezone.utc).isoformat()
    result = json.loads(engine.evaluate_at(json.dumps(request), now, ""))

    receipt = {
        "nti": "1.0",
        "receipt_id": str(uuid.uuid4()),
        "request": request,
        "decision": result["decision"],
        "reason": result["reason"],
        "engine": {"impl": "ube-foundation", "version": "0.3.0"},
        "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prev_receipt_hash": None,
    }
    receipt["receipt_hash"] = receipt_hash(receipt)
    return receipt


issuer_key = ube_foundation.Ed25519KeyPair()
engine = ube_foundation.TrustEngine()
engine.register_issuer_key(ISSUER, issuer_key.public_key_bytes())
engine.grant(ISSUER, CAPABILITY)

token = issue_token(issuer_key, RISK_THRESHOLD_BPS)

clean = {"risk_score": 0.12, "verdict": "clean",
         "receipt_sha256": "sha256:7c1e", "policy_version": "cg-2026.11"}
risky = {"risk_score": 0.91, "verdict": "injection",
         "receipt_sha256": "sha256:aa01", "policy_version": "cg-2026.11"}

allowed = authorize(engine, {"command": "ls -la"}, clean, token)
denied = authorize(engine, {"command": "ls -la"}, risky, token)

print("clean  ->", allowed["decision"], "|", allowed["reason"])
print("risky  ->", denied["decision"], "|", denied["reason"])
print("same receipt mechanics, different verdicts:", allowed["receipt_hash"] != denied["receipt_hash"])
```

## What is and is not enforced

**Enforcement requires a token.** `RiskBelow` is a caveat on a capability token.
A deployment that authorises with `grant(actor, capability)` and no token carries
no caveats, so no threshold applies. The caveat lives where tokens are issued, so
a grant-only deployment should say plainly that the score is not enforced by the
engine.

**The issuer key must be pinned.** A token signed by a key the engine has not
registered through `register_issuer_key` is denied with `untrusted token issuer`,
whatever its caveats say. Pinning is what stops an agent issuing itself a
permissive threshold.

**The caveat is signed.** Editing `RiskBelow` after signing, for example raising
6500 to 10000, invalidates the signature and the token is denied.

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
- The score is rounded to the nearest basis point before comparison. A score
  within half a basis point of the threshold may therefore deny, which is the
  fail-closed direction but should be stated when a threshold is chosen.
- The snippet assembles a receipt-shaped object for illustration. A conformant
  deployment takes the receipt from the engine (R1: one operation returns the
  verdict and its receipt), not from the caller assembling one.
