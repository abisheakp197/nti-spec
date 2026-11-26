# Security Limits: What Contains a Compromised Agent

This document states the architectural limits that bound the autonomy of a
compromised agent — including one that is more capable than its operators, plans
across long horizons, and controls its own tool calls.

It exists because the phrase "AI safety" is usually discussed as a property of
the model, and NTI makes no claim about model behaviour. NTI is a control plane
that sits between an agent and the actions it attempts. The relevant question is
therefore narrower and answerable: **if the model is fully compromised, what can
it still not do?**

This document is written to be falsifiable. Each section states a limit, the
mechanism that enforces it, and — importantly — what the limit does *not*
establish. A security document that claims no gaps is not describing a real
system.

---

## 1. Thermodynamic limits of cryptography

### 1.1 The claim

An agent cannot forge an authorization signature. Not because the model is
unwilling, but because forging one requires solving a problem whose cost exceeds
the energy available in the observable universe.

### 1.2 The mechanism

NTI authorizes actions with ML-DSA-87 (FIPS 204), which rests on the hardness of
module-lattice problems at NIST category 5. The engine accepts an action only
when a signature verifies against the public key registered for the actor.

Signature forgery without the private key is not a partial-credit operation. There
is no "close enough" verification, no gradient to descend, and no reward signal
that a more capable model could exploit. Verification is a bit comparison; the
search for a forgery is a brute-force search over a keyspace.

### 1.3 The arithmetic

Landauer's principle sets a floor on the energy cost of irreversibly erasing one
bit: `kT ln 2`.

At 300 K this is approximately `2.87 × 10⁻²¹ J` per bit. Searching a 256-bit
keyspace requires at most `2²⁵⁶` such operations:

| Quantity | Value |
| --- | --- |
| Energy per bit erased at 300 K | 2.87 × 10⁻²¹ J |
| Total for 2²⁵⁶ erasures at 300 K | 3.3 × 10⁵⁶ J |
| Total solar output over 10 Gyr | 1.2 × 10⁴⁴ J |
| Ratio (search cost ÷ solar lifetime output) | 2.8 × 10¹² |

Exhausting a 256-bit space at room temperature costs roughly **2.8 trillion times
the entire energy output of the Sun over its remaining lifetime**. Cooling to 4 K
reduces the per-bit cost to `3.8 × 10⁻²³ J` and the total to `4.4 × 10⁵⁴ J`, which
is still eleven orders of magnitude above the Sun's total output and about ten
orders of magnitude below the mass-energy of the observable universe
(~4 × 10⁶⁹ J).

Two honest qualifications belong here, because the naive version of this argument
is wrong:

**The relevant target is 128 bits, not 256.** Grover's algorithm quadratically
speeds up unstructured search, so a 256-bit space offers about 128 bits of
post-quantum security. The correct figure is therefore `2¹²⁸` operations, about
`9.8 × 10¹⁷ J` at 300 K. That is roughly two weeks of total global primary energy
production — well within human reach — which is why the argument must not rest on
the `2²⁵⁶` figure. It rests instead on the fact that `2¹²⁸` *classical*
evaluations of a lattice problem is not an energy problem but a
parallelism-and-memory problem: the attack is not retrieval from a table, it is
running a hard computation, and Landauer's bound is only the floor for the
irreversible part of it.

**Landauer's principle bounds irreversible erasure, not reversible computation.**
A reversible computer could in principle approach zero dissipation. This does not
rescue the attack, because the memory to hold a superposition of `2¹²⁸` states
exceeds the Bekenstein bound for a region the size of the Earth by an enormous
margin. The constraint moves from energy to space, and space does not help.

### 1.4 What this limit does not establish

This bound covers **key recovery and signature forgery**. It does not cover:

- **Implementation defects.** A bug in signature parsing, canonicalisation, or
  key registration bypasses the mathematics entirely. This is the realistic
  attack surface, and it is why the conformance suite exists.
- **Side channels.** Timing, power, and cache behaviour can leak key material
  without any brute force. NTI zeroizes secret key material on drop and uses
  constant-time comparison for equality checks, but has not been evaluated
  against a physical attacker.
- **Key theft.** See Section 2 and Section 5.

The correct statement is narrow: *given a correctly implemented verifier and a
private key the agent does not hold, the agent cannot produce an accepted
signature.* It is not "cryptography makes the system safe."

---

## 2. Separation of context

### 2.1 The claim

An agent cannot use a credential it has never been given. Prompt injection,
jailbreaking, and instruction hijacking operate on the model's context window.
They cannot exfiltrate material that was never placed there.

### 2.2 The mechanism

Private key material lives in the sidecar process, not in the agent's context.
Concretely, in the reference wrappers the signing key is held by the guardrail
object and used through a signing call:

```text
signature = self.key_pair.sign_bytes(message)
```

The agent's tool calls pass *intent* to the guardrail. The guardrail constructs
the canonical request, signs it, and evaluates policy. The model never receives
the secret key bytes, and no prompt — however crafted — can cause it to emit
something it does not possess.

This is the structural difference between "the agent is instructed to check
permissions" and "the agent is incapable of bypassing the check." Instructions
are inside the attack surface. Absence of capability is not.

### 2.3 Why this matters beyond model alignment

A model that has been fully persuaded to exfiltrate its credentials will still
fail, because the operation it needs — read the private key — is not available to
it. The attack has to leave the model layer and compromise the *process*, which is
a different and much narrower attack surface.

This is also why the boundary must be a process boundary rather than a prompt
boundary. If the key is in the context and the agent is merely told not to reveal
it, the control is advisory. If the key is in another process that the agent can
only call through a policy-checked interface, the control is structural.

### 2.4 What this limit does not establish

- **Host compromise.** If the attacker gains code execution in the sidecar
  process, the key is reachable. Separation of context is not separation of
  privilege; it assumes the sidecar runs in a less-compromised domain than the
  model, which must be engineered (separate container, separate credentials,
  least privilege on the sidecar's own host).
- **Confused deputy.** An agent that cannot read the key can still *ask* the
  sidecar to sign things, up to the limits of its granted capabilities. This is
  why capability minimisation matters: the sidecar signs what policy permits, and
  a broadly-granted agent delegates broadly.
- **Supply chain.** If the signer is a malicious build, the key is exfiltrated at
  construction time. This is why the release pipeline produces SLSA provenance
  and Sigstore signatures; see [`RELEASE.md`](RELEASE.md).

---

## 3. Fail-closed architecture

### 3.1 The claim

The engine defaults to Deny. Every path that does not reach an explicit,
positive verification decision returns a denial. There is no code path that
returns "allow" as an initialised default.

### 3.2 The mechanism

`TrustEngine::evaluate` returns a `PolicyDecision` whose `decision` field is
`Allow` only when every applicable check has passed. The checks are ordered so
that the absence of information is a denial, not a pass:

| Condition | Result |
| --- | --- |
| Signature verifies but key is not pinned for the actor | Deny |
| Public key presented without a signature | Deny |
| Unsigned capability token attached to a signed request | Deny |
| Capability granted but expired at the pinned time | Deny |
| Caveat that cannot be evaluated | Deny |
| Workload measurement registered but not presented | Deny |
| Workload measurement does not match registered value | Deny |
| No rule matched | Deny |

Two properties of this design are worth naming explicitly.

**Ambiguity resolves to denial.** A caveat type the engine does not recognise, a
malformed timestamp, a hash that fails to parse — each terminates the evaluation
with Deny rather than being skipped. Skipping an unparseable constraint is the
single most common way a policy engine becomes a no-op.

**The clock is pinned.** `evaluate_at(request, now)` fixes the timestamp at entry
so that a slow verification path cannot straddle a token expiry boundary and
produce a decision that is neither the state at arrival nor the state at
completion. This is a correctness property that is easy to lose: re-reading the
clock deeper in the stack makes the verdict depend on how long the check took.

### 3.3 What this limit does not establish

- **Fail-closed is only as strong as the interception point.** An action that
  never reaches the engine is unmediated. Every guarantee in this document is
  conditional on the call path passing through the sidecar, and coverage must be
  treated as a first-class security property. This is the same structural caveat
  as enforcement keyed on a property the caller can influence.
- **Fail-closed is an availability risk.** A denial is safe but it is also an
  outage. A lost key, an expired token, or a stale measurement stops work. This
  is the correct trade for high-authority actions and the wrong one for low-value
  ones, which is why policy is per-capability.
- **Denial is not prevention of the attempt.** The agent can still propose the
  action, and may retry, rephrase, or attempt a bypass. Fail-closed means the
  action does not execute, not that the agent stops trying.

---

## 4. Immutable audit trail

### 4.1 The claim

An agent cannot erase its tracks. Every decision produces a record that is
hash-chained to its predecessor and periodically sealed into an RFC 6962 Merkle
tree. Editing history is detectable; deleting it is detectable.

### 4.2 The mechanism

Each receipt commits to the hash of the canonical request, the decision and its
reason, policy and key identifiers, the pinned timestamp, and the previous
receipt hash. Receipts accumulate into batches, and each batch has an RFC 6962
Merkle root computed with domain separation:

```rust
pub const AUDIT_DOMAIN: MerkleDomain = MerkleDomain {
    leaf: DOMAIN_LEAF,
    node: DOMAIN_NODE,
};
```

Because each event commits to the hash of the event before it, altering event
`n` invalidates every hash from `n` onward. Because batches are sealed into a
Merkle tree, an auditor can verify a single decision with an inclusion proof
against a published root rather than being handed the entire log and asked to
trust it.

Two details that are commonly gotten wrong, and that this implementation gets
right:

**Domain separation.** Leaf hashes and interior-node hashes are prefixed
differently, so a leaf cannot be reinterpreted as an interior node. Without this,
a second-preimage attack can construct a tree with a chosen root.

**Odd-node promotion, not duplication.** RFC 6962 promotes an unpaired node to
the next level rather than duplicating it. Duplication is the Bitcoin-style
construction; it is vulnerable to a different class of proof forgery, and mixing
the two conventions across implementations breaks verification.

### 4.3 What this limit does not establish

- **Tamper-evident is not tamper-proof.** An attacker with write access to the log
  can rewrite the entire chain consistently. Detection requires the root to be
  published somewhere the attacker cannot also rewrite — a transparency log, a
  counterparty, or a timestamping authority. NTI provides the mechanism; the
  deployment must provide the anchor.
- **The record does not prevent the action.** A receipt proves that a decision was
  made and has not been altered. It does not stop execution, and it does not by
  itself establish that the decision was *correct* — only that it was the decision.
- **Logging is subject to the interception caveat.** Unmediated actions leave no
  receipt, so absence of a record proves nothing unless coverage is known and
  monitored.

---

## 5. Workload binding: closing the key-replay gap

### 5.1 The claim

A stolen key is not sufficient to act. Identity is bound to a workload
measurement as well as to a key, so a credential replayed from an unregistered
host is denied.

### 5.2 Why this section exists

Sections 1 through 4 bound what an agent can *compute, obtain, bypass, and erase*.
They do not bound where a stolen credential can be *used*, and that gap was
identified in peer review: binding identity only to a key means an attacker who
obtains the private key and a capability token can replay both from any machine
and be authorized. The signature verifies; the actor is pinned; the decision is
`Allow`. Every check passes because every check was about the key.

A key answers *who is calling*. It does not answer *what is calling*.

### 5.3 The mechanism

`register_pqc_identity_key` accepts an optional workload measurement — the
SHA-256 digest of the container image or build artefact expected to hold the
credential. When a measurement is registered, `evaluate` requires the request to
carry a matching value and denies otherwise:

| Registered | Presented | Result |
| --- | --- | --- |
| `sha256:aaaa…` | `sha256:aaaa…` | Allow |
| `sha256:aaaa…` | `sha256:bbbb…` | Deny |
| `sha256:aaaa…` | (absent) | Deny |
| `sha256:aaaa…` | malformed | Deny |
| (none) | anything | key-only, 0.1.x behaviour |

Three design decisions matter more than the API:

**The measurement is deliberately excluded from the signed message.** If it were
covered by `message_to_sign()`, an attacker holding the stolen key could simply
sign whatever measurement they wished, and the binding would be decorative. The
measurement must be the one field not under the signer's control: it is a claim
about the environment, checked against locally-registered expectation.

**The check runs outside the PQC branch.** A measurement registered for an actor
constrains every request path from that actor — including Ed25519-only and
unsigned requests. Enforcement that lives only inside one verification branch is
enforcement that can be routed around.

**Comparison is normalized.** `sha256:<hex>` and bare hex compare equal, because
a digest taken from a registry and one reported by a running workload are the same
value in different notations. Values that are not SHA-256 digests are rejected at
*registration* rather than compared as opaque strings, because a typo that never
matches produces a permanently denying policy that looks like a working one.

### 5.4 What this limit does not establish

- **Measurement quality.** NTI verifies that the presented value matches the
  registered one. Whether that value actually describes the running code depends
  on the measurement source — a TPM quote, a signed image digest from a registry,
  or a self-report. A workload that lies about its own hash defeats the binding,
  and only a hardware-rooted attestation closes that.
- **It is opt-in.** An actor with no registered measurement retains key-only
  authorization. Deployments must enable binding per actor; it is not on by
  default, because turning it on without provisioning measurements would deny all
  traffic from that actor.
- **Redeploy requires re-registration.** A new image has a new digest. The update
  path is `register_workload_measurement`, which is an administrative operation
  and must itself be access-controlled.

---

## 6. Summary of limits

| Limit | Established | Not established |
| --- | --- | --- |
| Thermodynamic | Forging a signature without the key is infeasible | Correctness of the verifier; side channels |
| Separation of context | The agent cannot read key material it never received | Host compromise of the sidecar; confused deputy within granted capability |
| Fail-closed | Absent positive verification, the action does not execute | That the action was intercepted at all |
| Audit trail | History cannot be edited undetectably | That the root is anchored where an attacker cannot also rewrite it |
| Workload binding | A stolen key alone cannot act | That the measurement describes the real running code |

---

## 7. What follows from this

The limits above are not a claim that a compromised agent is harmless. They are a
claim about **what a compromised agent can still not do**, and the list is short
and specific:

1. It cannot mint an authorization it was not granted.
2. It cannot read a credential it was never given.
3. It cannot execute an action that fails verification.
4. It cannot alter the record of what it attempted.
5. It cannot reuse a stolen key from an unmeasured host.

Everything outside that list is in scope for an attacker, including: persuading
the agent to *attempt* a harmful action that is within its legitimate capability;
compromising the sidecar's own host; exploiting a defect in the verifier; and
operating an action path that never reaches interception. Those are real, they are
the residual risk, and they are addressed by capability minimisation, host
hardening, the conformance suite, and coverage monitoring respectively. None of
them is addressed by cryptography, and this document does not claim otherwise.

The framing worth keeping: NTI converts a compromise into a **denied, attributable
event**. It does not prevent the compromise, and it does not make the agent
trustworthy. It makes the agent's authority bounded, which is a different and more
achievable property.

---

## References

- [`NTI-1.md`](NTI-1.md) — the specification these limits bound
- [`CONFORMANCE_TESTS.md`](CONFORMANCE_TESTS.md) — how the properties are tested
- [`AUDIT_REPORT.md`](AUDIT_REPORT.md) — independent review findings
- [`WHITE_PAPER_AGENTIC_ATTESTATION.md`](WHITE_PAPER_AGENTIC_ATTESTATION.md) — the
  same control class applied to a shipping platform
- NIST FIPS 204 — Module-Lattice-Based Digital Signature Standard
- RFC 6962 — Certificate Transparency
- Landauer, R. (1961), "Irreversibility and Heat Generation in the Computing Process"
