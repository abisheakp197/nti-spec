# RFC 0001 — Authorization Receipts

- **Status:** Draft
- **Author:** NTI maintainers
- **Created:** 2026-11-26
- **Affects:** NTI-1 §4 (Compliance Levels), §6 (Audit Layer)

## Summary

Define an **authorization receipt** as a normative NTI-1 object, and require that it be produced by the same operation that produces the authorization verdict.

Today the reference engine returns a verdict without any durable, signed record of it. A caller — or a log — can assert any verdict it likes after the fact, and no NTI verifier can tell the difference. That gap means the strongest available claim about an agent action is *"this record exists"*, not *"this is the decision the engine made"*.

The receipt *format* already exists and is already verified independently; see the next section. This RFC does not create a receipt. It makes one required property true: that the thing which gets signed is the engine's verdict, produced by the same call, rather than a payload chosen by the caller.

## Existing receipt machinery (extend this, do not reinvent it)

`conformance/vate-recovery/` already implements most of a receipt ecosystem, and it is good work:

- **`nti_receipt.json`** — `nti-receipt/1.0`: `receipt_id`, `agent_did`, `verification_method`, `action_payload` with `action_payload_sha256`, a `delegation_chain` committed by `delegation_chain_root`, a Merkle `merkle_proof`, and `ml_dsa_87_signature`.
- **`verify_receipt.py`** — a standalone verifier depending only on the standard library and `openssl` ≥ 3.5. It checks the schema, the payload binding, the RFC 6962 Merkle root, the inclusion proof and the ML-DSA-87 signature over a domain-separated, length-prefixed signing payload. It accepts `--public-key` to pin a key out of band, warns when it falls back to the self-asserted embedded key, and documents exactly what it does not check (DID authorization, VC issuer identity, whether the action took effect).
- **`generate_fixture.py`** — the producer counterpart: deterministic apart from the keypair, with `--tamper` negative cases, and it rejects Ed25519 outright because Ed25519 cannot verify against an ML-DSA-87 receipt.

So the hard parts are done: domain separation, length-prefixed signing input, identifier binding, Merkle inclusion, out-of-band key pinning, and negative cases. What is missing is narrower and sharper than "no receipts exist", and it is the whole of this RFC.

**The receipt binds an action payload chosen by the caller. It does not bind a verdict produced by the engine.** `action_payload` carries `action_id`, `type`, `contract`, `actor`, `resource`, `files`, `nonce`, `requested_at` — and no `decision`, `capability`, `policy` or `reason`. The producer is a fixture generator holding a disposable key, not `TrustEngine`, and the fixture labels itself `SYNTHETIC … not production evidence`.

That is why the invariant still has to be specified: a receipt proves that *NTI signed this action payload*. It does not yet prove that the engine *allowed* it.

This RFC closes the gap by making the verdict and its evidence one object with one producer.

## Motivation

The reason to adopt NTI is to answer one question after the fact:

> Was this agent authorized to do this, and has that answer been altered since?

Answering it needs three properties at once:

1. **Binding.** The recorded verdict is the verdict the engine computed for *that exact request*.
2. **Non-repudiation.** The record is signed by the engine that made the decision, not by whoever is writing the log.
3. **Tamper-evidence.** Changing any field of the record, or removing one, is detectable.

A plain log satisfies none of these. A signature over a log entry satisfies (2) and (3) but not (1): it proves the log writer said so, which is exactly the party whose honesty is in question.

The binding property is the one that cannot be retrofitted. If receipts are sealed after the fact by a wrapper, the wrapper holds the authority, and a receipt proves only that the wrapper was willing to sign. It must be impossible to obtain a receipt for a verdict the engine did not produce.

## Detailed Design

### The object

```json
{
  "nti": "1.0",
  "receipt_id": "6f1c0a52-2d5b-4c0e-9b2f-3f9a1b7c8d40",
  "request": { "id": "r-42", "actor": "agent-1", "capability": "tool:search", "action": "invoke", "input": { "q": "x" } },
  "decision": "Allow",
  "reason": "granted",
  "engine": { "impl": "ube-foundation", "version": "0.2.1" },
  "issued_at": "2026-11-26T10:04:11Z",
  "prev_receipt_hash": "sha256:9d5c…",
  "receipt_hash": "sha256:41ab…",
  "signature": "ml-dsa-87:5e8c…"
}
```

| Field | Meaning |
| :--- | :--- |
| `request` | The exact request as evaluated, canonically serialized. |
| `decision` | `Allow` or `Deny`. |
| `reason` | The engine's reason code for that decision. |
| `engine` | Implementation and version that produced the verdict, so a verifier can re-run it. |
| `prev_receipt_hash` | Hash of the issuer's previous receipt, or `null` for the first. |
| `receipt_hash` | `sha256` over the canonical form of every other field except `signature`. |
| `signature` | ML-DSA-87 signature by the issuer over `receipt_hash` bytes. |

### Normative requirements

- **R1.** An engine MUST expose a single operation that returns the verdict *and* its receipt. It MUST NOT expose an operation that accepts a verdict chosen by the caller.
- **R2.** `receipt_hash` MUST be computed over the canonical serialization (RFC 8785 JCS) of the receipt with `signature` and `receipt_hash` omitted.
- **R3.** The receipt MUST be signed by the engine's issuer key, registered under `engine.impl`, and MUST NOT be signed by the requesting actor's key.
- **R4.** An engine with durable audit state MUST set `prev_receipt_hash` to the hash of its previous receipt, forming a chain.
- **R5.** A verifier MUST reject a receipt when any of the following holds: the signature does not verify; `receipt_hash` does not recompute; the chain link does not match the preceding receipt; or re-evaluating `request` on the declared `engine.version` yields a different `decision`.
- **R6.** A receipt MUST be emitted for `Deny` as well as `Allow`. A denial that leaves no record is not auditable.

### Verification, in order

1. Parse the receipt; reject unknown top-level fields.
2. Recompute `receipt_hash` from the canonical form. Compare in constant time.
3. Verify `signature` against the issuer public key registered for `engine.impl`.
4. If `prev_receipt_hash` is present, confirm it equals the `receipt_hash` of the receipt the issuer published immediately before this one.
5. Re-evaluate `request` on `engine.version`. Confirm the decision matches.
6. Only then treat the receipt as evidence.

Step 5 is what separates a receipt from a signed log line, and it is why `engine` is inside the hash: a verifier that cannot reproduce the decision cannot accept the claim.

### Relationship to existing audit state

`audit_inclusion_proof` already proves that a leaf is included in a Merkle batch. Receipts become those leaves: `receipt_hash` is the leaf value. This RFC does not change the Merkle construction; it defines what is being hashed.

## Drawbacks

- **Cost.** One signature per authorization. ML-DSA-87 signing is fast but not free; high-rate agents will need batching, which trades latency for throughput.
- **Storage.** Every decision becomes durable. Deployments must choose retention and rotation policy, and `prev_receipt_hash` chains need pruning rules for rotation.
- **Breaking.** Engines that expose only `evaluate()` cannot produce conformant receipts. This is a Level 2 requirement, so it does not affect Level 1 conformance.

## Alternatives

- **Sign the log entry.** Rejected: it proves the log writer's intent, not the engine's verdict. This is the failure mode the RFC exists to prevent.
- **Receipt as a separate call after the decision.** Rejected: it creates a window in which the caller selects which verdicts to seal, which destroys binding.
- **Hash-only receipts without a chain.** Weaker but acceptable as an interim: it gives tamper-evidence without ordering. Rejected as the target state because deletion of a receipt becomes undetectable.
- **Reuse an existing attestation format (in-toto, DSSE).** Compatible, and a future RFC may define a mapping. Deferred because DSSE binds a payload to a signer but not a payload to a *recomputed verdict*, so it does not supply R5 step 5.

## Reference implementation status

**Implemented.** The receipt format (`nti-receipt/1.0`), an independent verifier (`verify_receipt.py`), a producer (`generate_fixture.py`), the RFC 6962 delegation Merkle tree, inclusion proofs, domain-separated signing payloads, out-of-band key pinning, and tamper negatives.

**Not implemented.** The binding. `TrustEngine.evaluate()` returns `{ "decision", "reason" }` and emits nothing. There is no receipt field carrying `decision`, `capability`, `policy` or `reason`, and no engine method that returns a signed receipt at all. The only producer is a fixture generator with a disposable key, which is why its own output is labelled `SYNTHETIC … not production evidence`.

Work required before this RFC can be marked Accepted, in order:

1. Extend the receipt payload (or define an authorization receipt profile) with `decision`, `capability`, `policy` and `reason`, hashed under the same domain-separated signing payload the verifier already implements.
2. Add `TrustEngine.evaluate_receipt()` returning the verdict and the receipt from one call, and no API that accepts a caller-supplied verdict.
3. Give the engine a persisted issuer key and a published issuer public key, so a receipt can be pinned out of band the way `verify_receipt.py --public-key` already supports.
4. Add vectors for R5: altered `decision`, altered `capability`, receipt signed by an actor key instead of the issuer key, and a receipt whose embedded request no longer reproduces the verdict.
5. Extend `conformance/validate.py` to run R5 end to end.

Until then, integrators must describe what they emit as *tamper-evident records of observed decisions*, not as NTI authorization receipts. The distinction is not pedantry: the first claim is defensible in front of an auditor, and the second is not.
