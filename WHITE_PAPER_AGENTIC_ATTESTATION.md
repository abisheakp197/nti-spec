# Attestation Gaps in Agentic AI Platforms

## A Case Study of Apple's Agent Layer, and a Blueprint for Verifiable Action Authorization

**Author:** Abisheak P.
**Date:** November 19, 2026
**Status:** Draft for public review
**License:** CC BY 4.0
**Companion spec:** NTI-1 (`VERSION` 1.0.0-draft)

---

## Abstract

Agentic AI platforms have converged on a two-tier security model. The **inference tier** is
well defended: Apple's Private Cloud Compute ships hardware-rooted attestation, a
transparency log, and per-request cryptographic evidence. The **action tier** — the layer
where a model's intent becomes a real operation on a real system — is not defended to the
same standard.

This paper makes three contributions.

First, it documents a specific and recurring failure pattern in the action tier:
**identity asserted by a mutable name rather than bound cryptographically.** We source three
instances from Apple's own published Private Cloud Compute release notes, including an
attestation blind spot in which a secure-configuration value selected whether a tool ran in
an isolated worker or on the agent node, and an open bypass in which a caller evades policy
enforcement by altering its invocation path.

Second, it specifies the NTI action-authorization pattern: a fail-closed sidecar that
evaluates policy as a deterministic function of a signed canonical request, key state, policy
state, and a pinned timestamp, emitting an RFC 6962 Merkle receipt for every decision.

Third, it provides an implementation blueprint for the Apple ecosystem — Swift FFI bindings
over the Rust core, an App Intents interception point, and PCC runtime-configuration
verification — together with an explicit account of what remains unbuilt.

The central claim is deliberately narrow. NTI does not make language models deterministic
and does not prevent prompt injection. It bounds the blast radius: an injected agent can
still *attempt* a forbidden action; the attempt is denied, and the denial is recorded in an
append-only log the agent cannot rewrite. We argue that this narrower claim is the one
enterprise buyers can actually verify.

---

## 1. Executive Verdict

Agentic platform security is currently split across two standards of evidence.

At the inference tier, Apple's PCC architecture is exemplary. A user's device verifies
hardware attestation before sending a request; nodes are stateless; releases are published to
a transparency log. The security properties are **cryptographically checkable by the user**,
not merely asserted by the vendor.

At the action tier, the same rigour is absent. The question *"was this specific tool call,
with these specific arguments, authorized by this specific principal, under this specific
policy?"* is answered today by a combination of:

- a model's judgement about whether a confirmation prompt is warranted,
- a policy engine keyed on names and paths,
- an audit log written after the fact.

Each of these is a **probabilistic or asserted** control standing in for a **deterministic and
verifiable** one. The result is a tier mismatch: the platform can prove which code ran on a
server, but not which actions an agent was permitted to take on a user's behalf.

This mismatch is the opportunity. It is also the risk: as agentic features acquire more
capability — file system access, cross-app operations, delegated tool execution — the action
tier becomes the higher-value target, while remaining the weaker tier.

**Our verdict:** the industry needs a verifiable action-authorization layer that is
complementary to, not competitive with, existing platform security. NTI is a reference
implementation of that layer.

---

## 2. The Real Apple Attestation Gaps

The findings below are drawn from Apple's **published** PCC Release Notes. Each carries an
Apple issue number and can be independently verified at the cited source.

> **Scope note.** Every finding in this section is a *known issue* that Apple has documented
> publicly. Per Apple's bounty guidelines, known issues are not eligible for reward, and we
> are not submitting them as vulnerabilities. They are cited here as **evidence of a design
> pattern**, in the same spirit as citing a post-mortem. Two of the three are already fixed.
> We credit Apple for documenting them openly; that openness is what makes this analysis
> possible.

### 2.1 Unattested configuration selects tool execution isolation

**Apple issue 178863006** — resolved in PCC 6A535100; listed as a known issue in
6A5272/6AX5221. Quoting the release notes:

> A secure-configuration value that selects whether a delegation-eligible tool runs in an
> isolated worker node or locally on the agent node is now attested. **Previously, this value
> was read without attestation, so modifying it could cause a tool intended for an isolated
> workload to instead run on the agent and weaken the security isolation between use cases.**

This is the clearest available example of the pattern. The security-relevant question —
*which workload executes this tool, and under what isolation?* — was answered by a value
outside the attested measurement. An attacker who could influence that value could downgrade
the isolation of a delegated tool **without altering any measured code**.

Note the structure of the flaw precisely. It is not a memory-safety bug and not a logic error
in the ordinary sense. It is a **coverage gap in the attestation**: a field that participates
in a security decision was not included in the set of fields the attestation commits to.

The general lesson is that attestation is only as strong as its coverage. Every input that
can change a security outcome must be inside the attested payload, or the attestation proves
the wrong thing.

### 2.2 Policy enforcement keyed on process name and caller-supplied path

**Apple issue 187893777** — known issue, open, PCC on Google Cloud. Quoting:

> The script-execution policy recognizes Python interpreters by process name, which limits
> its coverage in two ways: eBPF programs match process names derived from caller-supplied
> paths **without verifying file identities, so a caller can alter its invocation path to
> avoid policy enforcement.**

This is a textbook instance of **string identity substituting for bound identity**. The
policy asks "is this a Python interpreter?" and answers by comparing a name that the caller
supplies. A name is not a binding: anyone who controls the string controls the answer.

Cryptographic identity is different in kind. A signature over a canonical payload, verified
against a registered public key, cannot be satisfied by choosing a different string — the
attacker would need the private key.

This finding is the strongest single argument for the NTI approach, and it is Apple's own
description of the problem. It is also, notably, still open.

### 2.3 Transparency inclusion proofs not enforced at every verifier

**Apple issue 167793384** — known issue, open. Quoting:

> Verification of a certificate's inclusion in the log is not yet enforced: a user's device,
> a PCC proxy node, and an ensemble leader each validate the DCA CA signature on a node's
> certificate, **but don't yet enforce the presence of transparency inclusion proofs.**

Apple operates the log but does not yet require proof of inclusion at each verification
point. A signature proves *who* signed; an inclusion proof proves *that the signer's
certificate was published where anyone could see it*. Without enforcement, the log is a
record rather than a constraint.

This is directly relevant to NTI's receipt design, and it is the gap most amenable to
reuse: the fix is a verification discipline at existing checkpoints, not a new subsystem.

### 2.4 Related findings

| Issue | Description | Relevance |
| --- | --- | --- |
| 176864434 | Private Filter Service node attestations omitted from the Apple Intelligence Report | Attestation completeness |
| 181951488 | Cost-token signing keys not published to the transparency service | Selective verifiability — some claims checkable, others not |
| 184553308 | `pccvre` caches release assets by filename; a later release can pick up an earlier image | Content-addressed identity replaced by a mutable name |
| 178401486 | Recitation-prevention blocks miscategorised as infrastructure blocks and logged to Apple | Telemetry accuracy affecting privacy claims |

Issue 184553308 is worth dwelling on because it is the same failure mode in a different
layer: an artefact identified by a **name** (`image.tar.gz`) rather than by its **content
hash**. The consequence — booting the wrong OS image — is exactly the class of error that
content addressing eliminates.

### 2.5 The pattern

Across five distinct subsystems — attestation coverage, script policy, transparency
verification, release tooling, and telemetry categorisation — the same structural weakness
recurs: **a security decision depends on a value that is asserted, mutable, or named, rather
than bound to a cryptographic commitment.**

We do not claim this is unique to Apple. It is characteristic of agent platforms generally,
because the action tier evolved faster than its verification model. Apple is simply unusual
in documenting the gaps in public, which makes the pattern visible and the case for a
standard concrete.

---

## 3. NTI Architecture

### 3.1 Design goals

NTI is specified in NTI-1. Its goals, in priority order:

1. **Fail closed.** Absent a positive verification, deny. Ambiguity is denial.
2. **Bind the payload.** The authorization decision must cover the exact arguments that will
   execute, not a summary of them.
3. **Bind the identity.** Identity must be a key, not a name or a path.
4. **Make the record immutable.** Every decision produces a receipt that cannot be
   retroactively edited without detection.
5. **Change nothing else.** No kernel modification, no model modification, no API breakage.

Goal 5 is what makes the approach deployable. A control that requires replacing the platform
is a research project; a control that runs beside it is a product.

### 3.2 Components

**Rust core (`ube-foundation`).** The reference implementation is a Rust library with no
mandatory Python dependency (`default = []`; the `python` feature enables PyO3). It provides:

- ML-DSA-87 (Dilithium5) signing and verification via `pqcrypto-dilithium`, with secret key
  material zeroized on drop.
- ML-KEM-1024 (Kyber1024) for key establishment.
- RFC 6962 Merkle operations: `merkle_root`, `inclusion_proof`, `verify_inclusion`, with
  domain separation via `MerkleDomain`.
- Canonical serialisation via `canonical_json_bytes`.
- `TrustEngine::evaluate(&ActionRequest) -> PolicyDecision`, plus `evaluate_at(request, now)`
  which pins the clock so a decision cannot straddle a token-expiry boundary.

The pinned-clock detail is worth noting because it is a correctness property that is easy to
get wrong: re-reading the clock deeper in the verification stack lets a slow path straddle an
expiry boundary, so a token valid on arrival is denied, or a decision recorded earlier than
it was made.

**Action request.** The unit of authorization is a structured request, not a string:

```rust
pub struct ActionRequest {
    pub id: String,
    pub actor: String,
    pub capability: String,
    pub action: String,
    pub input: serde_json::Value,
    pub signature: Option<Vec<u8>>,
    pub pqc_signature: Option<PqcSignature>,
    pub public_key: Option<Vec<u8>>,
    pub pqc_public_key: Option<Vec<u8>>,
    pub token: Option<CapabilityToken>,
    pub identity_claim: Option<IdentityClaim>,
}

pub struct PolicyDecision {
    pub decision: Decision,
    pub reason: String,
}
```

**Capability tokens with caveats.** Tokens carry constraints — `Expires`, `MaxExecutions`,
`ValueLimit`, `PathRestricted` — evaluated as part of the deterministic decision.

**Framework adapters.** Reference wrappers exist for CrewAI, LangChain, AutoGen, and
OpenHands, each exposing a verification entry point and failing closed by raising
`PermissionError` in strict mode.

### 3.3 Decision semantics

The security property NTI claims rests on one statement: **the verdict is a deterministic
function of its inputs.**

```text
Decision = f( canonical(request), key_state, policy_state, pinned_timestamp )
```

`f` contains no sampling, no model inference, and no clock reads. Given the same inputs, it
returns the same verdict. This is what makes the decision auditable: a third party can
recompute it.

This is also the precise sense in which NTI is *not* a probabilistic guard. Model-mediated
confirmation is probabilistic by construction — the same input may be judged differently
across runs. A deterministic policy function is not.

### 3.4 Receipts

Every decision emits a receipt committing to:

- the hash of the canonical request,
- the decision and its reason,
- the policy version and key identifiers,
- the pinned timestamp,
- the previous receipt hash.

Receipts are chained and periodically sealed into an RFC 6962 Merkle tree, producing an
inclusion proof against a published root. An operator can therefore demonstrate, to an
auditor or a regulator, that a given action was (or was not) authorized, and that the record
has not been altered since.

The receipt does **not** prevent the action. It makes denial of the action, and the record of
the decision, non-repudiable. Those are different properties and it is important not to
conflate them.

---

## 4. The Honest Limits of NTI

A security architecture that does not state its limits is not a serious one. The following
are true as of this writing.

### 4.1 NTI does not prevent prompt injection

Injection succeeds at the model layer. An attacker who controls retrieved content can induce
the agent to *attempt* a harmful action. NTI's contribution is that the attempt fails and is
recorded. If the injected instruction maps onto an action the principal has legitimately
granted, NTI will allow it — correctly, by its own model, and that is a residual risk the
deployer must address through capability minimisation.

Stated plainly: **NTI converts a compromise into a denied, attributable event. It does not
prevent the compromise.**

### 4.2 NTI is only as strong as the interception point

Every guarantee depends on the call path passing through the sidecar. A tool invoked by a
path that bypasses interception is unmediated. This is the same structural caveat as
issue 187893777: enforcement keyed on a property the caller can influence is not enforcement.
Deployments must therefore treat interception coverage as a first-class security property and
monitor for unmediated paths.

### 4.3 Canonicalisation is not yet normatively specified

`canonical_json_bytes` produces compact JSON with sorted object keys, via `serde_json`. This
is deterministic **within a single serializer**, and because `preserve_order` is not enabled,
object keys are sorted, which removes the most common source of divergence.

It is **not** a normative cross-language canonical form. RFC 8785 (JSON Canonicalization
Scheme) additionally specifies number serialisation and string escaping. Two independent
implementations diverge on floating-point rendering, producing different bytes — and
therefore different signatures — for semantically identical payloads.

This is not hypothetical. Comparing JCS against compact sorted JSON on four cases:

| Input | RFC 8785 JCS | Compact sorted JSON | Result |
| --- | --- | --- | --- |
| `{"amt": 1.0}` | `{"amt":1}` | `{"amt":1.0}` | **diverges** |
| `{"n": 1e-7}` | `{"n":1e-7}` | `{"n":1e-07}` | **diverges** |
| `{"amt": 1e30}` | `{"amt":1e+30}` | `{"amt":1e+30}` | same |
| `{"b":1,"a":2}` | `{"a":2,"b":1}` | `{"a":2,"b":1}` | same |

Key ordering already agrees, because `serde_json`'s map is a `BTreeMap` without
`preserve_order`. Number formatting does not. An amount of `1.0` and an amount of `1` are the
same value but different bytes, so a receipt produced by one implementation fails
verification under another — and, worse, an attacker who can choose the representation can
produce a payload that one implementation reads as authorized and another reads as different.

This matters for a standard whose value depends on independent implementations agreeing.
**Recommendation:** NTI-1 should adopt RFC 8785 JCS as the normative canonical form, with
`canonical_json_bytes` treated as one conforming implementation pending verification against
the JCS test vectors. Until then, cross-language interoperability must not be assumed, and
deployments should pin a single canonicaliser.

### 4.4 Key management is the hard part

Binding identity to keys moves the problem rather than dissolving it. Who provisions the
agent's key? Where does it live? What is the revocation path, and how quickly does it take
effect? NTI specifies the mechanics (registration, revocation, capability tokens) but the
operational answers are deployment-specific. A lost key is a denied action — the correct
fail-closed behaviour, and also an availability event.

### 4.5 NTI does not run on Apple platforms today

This is the most important limit for the audience of this paper.

The reference implementation is Rust with **PyO3** bindings. There is no Swift or
Objective-C binding, no App Intents extension, no Shortcuts integration, and no PCC node
integration. `pip install openhands-nti` installs a Python package that cannot execute on an
iPhone or a PCC node.

The following section is therefore a **blueprint, not a description of shipped
functionality.** We mark it as such deliberately: a security architecture presented as
deployed when it is not would be dismissed by exactly the reviewers whose attention this
paper seeks.

---

## 5. Implementing NTI in the Apple Ecosystem

The integration strategy follows the same principle as the architecture: **add a verification
layer beside existing components; do not replace them.** Nothing below requires a kernel
change, a model change, or a breaking API change.

### 5.1 Swift FFI binding

The Rust core is already structured for this. Two viable paths:

**Option A — UniFFI.** UniFFI generates Swift and Kotlin bindings from a UDL or proc-macro
interface. It handles object lifetimes, error mapping, and async, and produces idiomatic
Swift. Suited to exposing `TrustEngine` as a Swift class.

**Option B — swift-bridge.** Lighter weight, generates a C header plus Swift glue, and gives
finer control over the ABI. Suited to a minimal, auditable surface.

Either requires a `cdylib`/`staticlib` crate type. The core already builds without Python
(`default = []`), so no feature gymnastics are needed:

```toml
[lib]
crate-type = ["staticlib", "cdylib", "rlib"]
```

A UniFFI interface would look approximately like this:

```rust
// ube-foundation/src/uniffi_api.rs  (illustrative)
#[derive(uniffi::Record)]
pub struct ActionRequestFfi {
    pub id: String,
    pub actor: String,
    pub capability: String,
    pub action: String,
    pub input_json: String,
    pub pqc_signature_hex: Option<String>,
    pub pqc_public_key_hex: Option<String>,
}

#[derive(uniffi::Enum)]
pub enum VerdictFfi {
    Allow { receipt_hex: String },
    Deny { reason: String },
}

#[uniffi::export]
pub fn evaluate_action(req: ActionRequestFfi, now_rfc3339: String) -> VerdictFfi { /* … */ }
```

Swift then calls it directly:

```swift
import UbeFoundation

let verdict = evaluateAction(
    req: ActionRequestFfi(
        id: requestID,
        actor: principalID,
        capability: "calendar.delete",
        action: "delete",
        inputJson: canonicalJSON,
        pqcSignatureHex: signature,
        pqcPublicKeyHex: agentPublicKey
    ),
    nowRfc3339: ISO8601DateFormatter().string(from: Date())
)

switch verdict {
case .deny(let reason):
    throw NTIError.denied(reason)   // fail closed
case .allow:
    break                            // proceed to execution
}
```

Two ABI notes for implementers. First, ML-DSA-87 public keys are 2592 bytes and signatures
are 4627 bytes. The current Python binding returns signatures as a 9254-character hex string;
across an FFI boundary that should be `Data`/`Vec<u8>` instead, since hex doubles the payload
and adds a parse step on every verification. Second, the FFI boundary must not become a place
where canonicalisation is re-implemented in Swift — the canonical form should be produced
once, by the core, so that the bytes signed are the bytes verified.

### 5.2 App Intents integration

The interception point must sit where an intent resolves to an executable action, before
execution. Conceptually:

```swift
struct TransferFundsIntent: AppIntent {
    static var title: LocalizedStringResource = "Transfer Funds"

    @Parameter(title: "Amount")  var amount: Decimal
    @Parameter(title: "Account") var account: String

    func perform() async throws -> some IntentResult {
        // 1. Build the canonical payload from the RESOLVED parameters.
        //    Note: parameters, not the user's utterance. The model's
        //    interpretation is already baked in by this point, which is
        //    precisely why we must bind what will actually execute.
        let payload = CanonicalPayload(
            capability: "finance.transfer",
            action: "execute",
            parameters: ["amount": "\(amount)", "account": account],
            principal: currentPrincipalID,
            intentID: UUID().uuidString
        )

        // 2. Ask the NTI sidecar for a decision. Deterministic; no model call.
        let receipt = try NTISidecar.shared.authorize(payload)

        // 3. Fail closed. Absence of a positive verdict is denial.
        guard receipt.isValid, receipt.verdict == .allow else {
            throw IntentError.unauthorized(receipt.reason)
        }

        // 4. Execute only after verification, and attach the receipt so
        //    the audit chain records the exact bytes that were authorized.
        return try await performTransfer(amount: amount,
                                         account: account,
                                         ntiReceipt: receipt)
    }
}
```

Three properties of this sketch deserve emphasis.

**The signature covers resolved parameters, not the utterance.** Prompt injection operates on
the utterance; binding operates on the resolved call. An injected instruction that changes
the amount produces a different canonical payload, hence a different signature, hence a
receipt that does not match the authorized one.

**Verification precedes execution.** The ordering is the control. A check after the fact is
telemetry, not authorization.

**The receipt travels with the action.** Downstream systems can verify that the operation
they are performing was the one that was authorized, rather than trusting a boolean handed
across a boundary.

What this does *not* do is prevent the model from proposing a bad action. It ensures that a
proposal outside policy cannot execute, and that the refusal is recorded.

### 5.3 PCC integration: verifying runtime configuration

Issue 178863006 describes a secure-configuration value that decided whether a delegated tool
ran in an isolated worker or on the agent node, and was read without attestation. Apple has
since attested that value. The NTI pattern generalises the fix and adds independent
verifiability.

The mechanism is a commitment chain with no new subsystem:

1. **Canonicalise the security-relevant configuration.** The isolation selector, tool
   delegation policy, and any other field that can change a security outcome are serialised
   into a canonical form.
2. **Commit to it in the attested measurement.** The hash of that canonical form is included
   in the node's attestation payload, so it is covered by the hardware-rooted measurement.
3. **Emit a receipt per delegated tool execution.** The receipt commits to the configuration
   hash actually in force at execution time, the tool identity, and the canonical arguments.
4. **Seal receipts into a Merkle tree and publish the root.** Inclusion proofs let a third
   party verify that a specific execution occurred under a specific configuration, without
   trusting the node's own logging.
5. **Verify before executing.** The worker validates the receipt against the attested root. A
   mismatch — configuration changed, tool substituted — is a denial.

The property gained is not merely "the configuration is attested" but "**any observer can
prove which configuration was in force for a specific tool execution, and cannot be shown a
different story later.**" That closes the coverage gap in the direction that matters: not
just measuring the value, but making the measurement checkable after the fact.

The same construction applies to issues 167793384 and 184553308 — enforce inclusion proofs at
existing verifiers, and identify artefacts by content hash rather than filename.

### 5.4 Deployment shape and non-regression

| Concern | NTI's position |
| --- | --- |
| Kernel | Untouched. NTI runs in user space. |
| Foundation Model | Untouched. No weights, no fine-tuning, no prompt changes. |
| Existing APIs | Unchanged. App Intents keep their signatures; the sidecar is additive. |
| Latency | One ML-DSA-87 verify plus a Merkle proof check per action. Measurable, bounded, and independent of model latency. |
| Failure mode | Deny. A missing or unverifiable receipt blocks the action. |
| Rollout | Per-capability. Start with high-value intents; leave the rest unmediated. |

The last row is the practical path to adoption: a deployment can begin with a single
capability — say, financial transfers — and expand, with no platform-wide change.

### 5.5 The business case

The argument for standardising this is not that Apple's engineers have been careless. It is
that **enterprise buyers are beginning to demand evidence that no current platform can
produce.**

Consider what a regulated buyer must answer before deploying an agent with real authority:

- Which actions did the agent take, with what arguments, under which policy version?
- Can you prove the record was not altered after the fact?
- Can you demonstrate that an action outside policy was refused?

Today these are answered with vendor assertions and application logs. With a receipt chain
they are answered with a proof a third-party auditor can check independently. That is a
different category of answer, and procurement processes in financial services, healthcare,
and the public sector are already shaped around exactly this kind of evidence.

The strategic value is therefore not "first to ship agentic features" — a race Apple is
already in — but **first to make agentic authorization independently verifiable.** That is a
durable position, because it is a property of the architecture rather than of a release.

We should be careful with the competitive framing. Claims that a standard will "crush" a
competitor are rhetoric, and enterprise buyers discount rhetoric. The defensible claim is
narrower and stronger: if verifiable action authorization becomes a procurement requirement,
platforms that can produce receipts will be eligible and platforms that cannot will not. The
work of this paper is to make that requirement concrete enough to be specified, and cheap
enough to be adopted.

---

## 6. What Remains Unbuilt

Stated plainly, so that no reader mistakes a blueprint for a product:

| Component | Status |
| --- | --- |
| Rust core: ML-DSA-87, Merkle, `TrustEngine`, canonical JSON | **Built**, `ube-foundation` 0.1.9 on PyPI |
| Python adapters: CrewAI, LangChain, AutoGen, OpenHands | **Built**, published, CI green |
| Swift / Objective-C bindings | **Not built** |
| App Intents interception | **Not built** — requires an Apple-private integration point |
| PCC tool-gateway integration | **Not built** — protocol appendix not public |
| RFC 8785 JCS canonicalisation | **Not adopted** — recommended above |
| Independent third-party implementation | **None yet** — the real test of a standard |

The last row is the one that determines whether NTI-1 is a standard or a vendor document. A
specification with a single implementation is a product description. We would welcome
independent implementations, and we consider the JCS gap the first obstacle to enabling them.

---

## 7. Conclusion

The agentic stack has a tier mismatch. Inference is attested; action is asserted. Apple's own
release notes document the consequences across five subsystems, in each case reducing to the
same root cause: a security decision resting on a name, a path, or a mutable configuration
rather than a cryptographic commitment.

NTI's contribution is modest and specific. It makes the authorization decision a
deterministic function of signed inputs, and it makes the record of that decision
tamper-evident. It does not stop prompt injection, and it does not replace anything.

The opportunity is to standardise the action tier before it becomes the next decade's attack
surface. That work is best done in the open, with independent implementations and a normative
canonical form. This paper is an invitation to that work, not an announcement of its
completion.

---

## Appendix A: Cited Apple Issues

All quotations are from Apple's published PCC Release Notes
(<https://security.apple.com/documentation/private-cloud-compute/releasenotes>), retrieved
2026-11-19.

| Issue | Status | Layer | Pattern |
| --- | --- | --- | --- |
| 178863006 | Resolved (6A535100) | Attestation coverage | Security value outside attested measurement |
| 187893777 | Open | Script policy | Identity by caller-supplied name/path |
| 167793384 | Open | Transparency | Inclusion proof not enforced |
| 176864434 | Open | Attestation completeness | Attestation omitted from report |
| 181951488 | Open | Transparency | Keys not published; claim unverifiable |
| 184553308 | Open | Release tooling | Artefact identified by filename, not hash |
| 178401486 | Open | Telemetry | Miscategorised blocks affect privacy claims |

Per Apple's guidelines, known issues are not eligible for bounty. These are cited as design
evidence, not submitted as vulnerabilities.

## Appendix B: References

- NTI-1 specification — `nti-spec/NTI-1.md`
- Reference implementation — `ube-foundation` 0.1.9, PyPI
- RFC 6962 — Certificate Transparency
- RFC 8785 — JSON Canonicalization Scheme
- NIST FIPS 204 — ML-DSA
- NIST FIPS 203 — ML-KEM
- Apple, Private Cloud Compute Security Guide
- Apple, Security Bounty Guidelines and Categories
