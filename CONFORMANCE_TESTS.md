# NTI-1 Conformance Tests

This document defines the conformance test obligations for NTI-1, organised around
the five properties articulated by Larry Lewis (`bigblackcoder`) in his
candidate contribution to the conformance suite. Each property is mapped to the
normative requirement it enforces in [`NTI-1.md`](NTI-1.md) and to the harness
that exercises it.

An implementation MUST pass every test below to claim the compliance level it
asserts. A test that cannot execute is reported as **blocked**, never as a pass.

| # | Property | Normative requirement | Enforcement harness |
| --- | --- | --- | --- |
| 1 | Identity binding | §3.1, T-1.1 | `conformance/identity.json`, `ube-foundation` key registration |
| 2 | Delegated authority | §3.2, T-2.1, T-6.1–T-6.3 | `conformance/capability_policy.json`, `nti_regressions.rs` |
| 3 | Runtime containment | §6, §6.1 (draft basis) | LGD state machine, `incomplete_check` fail-closed path |
| 4 | Workload integrity | §3.3, T-3.1 | `nti_regressions.rs` quorum shortfall case |
| 5 | Verifiable evidence | §3.4, T-4.1, T-5.1 | `conformance/audit_log.json`, hash-chain validation |

---

## Property 1 — Identity binding

A principal is bound to a cryptographic key, and an action is accepted only when
its signature verifies against the key registered for that principal. A request
signature alone cannot substitute for a registered identity.

**Test T-1.1 — unsigned action is denied.**
Submit an action carrying no signature. The result MUST be Deny.

**Test 1.2 — signature from an unregistered key is denied.**
Sign a well-formed action with a key that is not registered for the claimed
principal. The result MUST be Deny. This is the case the engine previously
accepted; the fix binds the signature to the registered key rather than to the
DID string alone.

**Test 1.3 — registered key verifies.**
Sign with the registered key. The result MUST be Allow, and the receipt MUST
name the verifying key.

Harness: `conformance/identity.json` declares the CRYSTALS-Dilithium5 key
specification; the engine test registers the public key through
`TrustEngine.register_pqc_identity_key`.

## Property 2 — Delegated authority

Authority is carried by an explicit delegation record. An action is permitted
only if a delegation record granting that capability to the acting principal is
included in the Merkle delegation chain. Possession of a valid signature is
never sufficient on its own.

**Test 2.1 — expired capability is denied.**
Submit an action whose capability has expired. The result MUST be Deny.

**Test 2.2 — unsigned capability is denied.**
Present a valid signed request with no local grant, attaching a token whose
issuer signature is empty. The result MUST be Deny: a request signature cannot
supply missing delegated authority.

**Test 2.3 — action outside the grant is denied (T-6.3).**
Request an operation outside the delegated actions or path restrictions. The
result MUST be Deny.

**Test 2.4 — action before `valid_after` is denied (T-6.2).**
Submit before the capability's `valid_after` instant. The result MUST be Deny.

**Test 2.5 — revoked delegation is denied (T-6.1).**
Submit an action referencing a revoked delegation token or identity key. The
result MUST be Deny.

Harness: `conformance/capability_policy.json` defines capabilities and caveats;
the `unsigned capability` row of `conformance/rust/nti_regressions.rs` is the
pinned regression.

## Property 3 — Runtime containment

A system that cannot complete a check MUST halt rather than proceed. Fail-closed
semantics are mandatory: an error in identity, delegation, policy, or consensus
evaluation resolves to Deny, never to Allow.

**Test 3.1 — incomplete check halts execution.**
Force an evaluation error (unreadable policy, unresolvable delegation, malformed
canonical form). The action MUST be blocked and the module MUST NOT be invoked.

**Test 3.2 — policy timing is evaluated before dispatch.**
An action evaluated after its capability window has closed MUST be blocked even
if it was valid when queued.

**Test 3.3 — resume requires a basis.**
Resuming after a halt MUST carry a `resume_basis` receipt; a resume without one
MUST be refused.

Harness: the LGD state machine in §6 of `NTI-1.md`, including the
`incomplete_check` semantics in §6.1 and the `resume_basis` field in §6.2.

**Status caveat.** The §6 state machine and the `resume_basis` field rest on the
*NTI x LGD transition-contract spec — v0.1.4*, which NTI-1 §6 records as
"draft for comment" and explicitly **not agreed** by either party. These tests
therefore describe the working basis for implementers, not a ratified normative
annex. Results against them MUST be reported with that qualification, and a
future ratified revision supersedes them.

## Property 4 — Workload integrity

Multi-agent actions execute only when the required quorum of eligible modules
authorises them. A quorum shortfall MUST refuse the action and invoke no module.

**Test 4.1 — quorum shortfall refuses and dispatches nothing (T-3.1).**
With one eligible module and a required threshold of two, the result MUST be a
refusal with zero module invocations.

**Test 4.2 — threshold-one positive control.**
With the threshold met, the action MUST execute exactly once. This control
distinguishes a correct refusal from a harness that never dispatches at all.

Harness: the `quorum shortfall` row of `conformance/rust/nti_regressions.rs`,
which observes an in-memory dispatch counter. The counter observes module
dispatch, not a real resource or completed external transaction.

## Property 5 — Verifiable evidence

Every decision produces tamper-evident, append-only evidence that survives
restart and can be independently verified.

**Test 5.1 — one receipt per action (T-4.1).**
Execute 100 actions. The chain length MUST equal 100.

**Test 5.2 — chain survives restart (T-5.1).**
Restart the system. The audit chain MUST be preserved and continue from the
prior head.

**Test 5.3 — tampering is detected.**
Alter any historical entry. Verification MUST fail and MUST identify the first
divergent index.

**Test 5.4 — truncation is detected.**
Present a valid but truncated prefix of the log. It MUST NOT be accepted as
complete: link verification alone passes any valid prefix, so completeness MUST
be anchored to the published Merkle accumulator root, the expected chain length,
or an externally witnessed final head (see `conformance/issue-18/truncation.json`).

Harness: `conformance/audit_log.json`, a SHA-256 append-only hash chain. Note
that NTI-1 §3.4 specifies the audit trail as an append-only hash chain, not a
Merkle tree; the Merkle accumulator (RFC 6962 inclusion semantics) is the
revocation registry of §6, and it supplies the anchoring that test 5.4 requires.

---

## Execution

Validate the JSON conformance examples and run the embedded code blocks:

```sh
python3 conformance/validate.py
```

Run the pinned Rust regression matrix (see
[`conformance/rust/README.md`](conformance/rust/README.md) for the exact
engine pin and toolchain):

```sh
cargo +1.90.0 test --locked \
  --manifest-path ube-foundation/Cargo.toml \
  --test nti_conformance_regressions -- --nocapture
```

## Reporting

A conformance result MUST state, for each test above, one of: **pass**,
**fail**, or **blocked**. A build failure is blocked execution, not an assertion
failure and not a successful conformance claim. No expected-panic, ignored-test,
or continue-on-error exception may be used to convert a failure into a pass.

## Attribution

The five-property framing is drawn from the candidate contribution by Larry
Lewis (`bigblackcoder`), prepared with AI assistance, which is scoped to
Properties 2 and 4. Properties 1, 3, and 5 are specified here to complete the
matrix; they are not claimed as established by that contribution.
