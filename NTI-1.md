# NTI-1: Neutral Trust Infrastructure — Standard 1

**Version:** 1.0.0-draft
**Status:** Draft for public comment
**Published:** 2026

---

## Abstract

This document specifies NTI-1 (Neutral Trust Infrastructure — Standard 1), a post-quantum, zero-trust governance standard for autonomous AI agents. NTI-1 defines formal requirements across five core pillars: Principal-Bound Identity, Governance, Consensus, Audit, and Persistence. It establishes standardized compliance levels, testable requirements, and verification protocols necessary for auditability and interoperability across enterprise multi-agent deployment environments.

---

## Table of Contents

1. [Abstract](#abstract)
2. [Introduction](#1-introduction)
3. [Terminology](#2-terminology)
4. [The 5 Pillars](#3-the-5-pillars)
5. [Compliance Levels](#4-compliance-levels)
6. [Testable Requirements](#5-testable-requirements)
7. [Runtime Halt & Revocation (LGD State Machine)](#6-runtime-halt--revocation-lgd-state-machine)
8. [Ecosystem Interoperability: ASL Conformance Kit](#7-ecosystem-interoperability-asl-conformance-kit)
9. [Reference Implementation](#8-reference-implementation)
10. [Certification Process](#9-certification-process)
11. [Governance](#10-governance)
12. [Security Considerations](#11-security-considerations)
13. [Appendix](#12-appendix)

---

## 1. Introduction

### 1.1 Purpose

This specification defines the requirements for **Neutral Trust Infrastructure (NTI-1)**, a standard for cryptographically verifiable governance of autonomous AI agents.

As AI agents transition from passive assistants to active executors of real-world actions — transferring funds, modifying infrastructure, accessing sensitive data — the need for a formal, auditable trust standard becomes critical. NTI-1 defines what such a standard requires.

### 1.2 Scope

NTI-1 applies to any system in which an autonomous AI agent:

- Executes actions with real-world consequences
- Accesses data classified as sensitive
- Operates on behalf of a human or organizational principal
- Interacts with other agents in multi-agent workflows

### 1.3 Motivation

Three converging forces make NTI-1 necessary:

1. **Regulatory pressure.** NIST, the EU AI Act, and India DPDP Act are increasingly mandating verifiable AI governance.
2. **Post-quantum urgency.** NIST has mandated migration to post-quantum cryptography (PQC). Principal-bound identity must be PQC-compliant from day one.
3. **Threat landscape.** Prompt injection, hallucinated actions, and rogue agents are now the primary vectors of AI-driven harm.

### 1.4 Design Principles

NTI-1 is designed around four principles:

- **Neutrality.** The standard must be implementable by any party without allegiance to a specific vendor.
- **Verifiability.** All claims of compliance must be testable by a third party.
- **Minimalism.** The standard specifies only what is necessary. Implementations may extend, but MUST NOT contradict.
- **Federation.** Multiple parties must be able to participate in a trust network without central control.

---

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/html/rfc2119).

- **Agent** — An autonomous software system that perceives, decides, and acts.
- **Action** — A discrete operation executed by an agent with external effect.
- **Capability** — An explicit permission granted to an agent to perform a specific class of actions.
- **Caveat** — A condition attached to a capability (e.g., Expires, ValueLimit).
- **Trust Engine** — The component that evaluates an action against policy.
- **Verifier** — A participant in an NTI-1 federation that validates actions.
- **Merkle Chain** — A cryptographic hash chain over a sequence of events.
- **BFT Consensus** — Byzantine Fault Tolerant agreement among multiple parties.
- **PQC** — Post-Quantum Cryptography.
- **Dilithium5** — CRYSTALS-Dilithium5, a NIST Level 5 post-quantum signature algorithm.
- **Kyber1024** — CRYSTALS-Kyber1024, a NIST Level 4 post-quantum key encapsulation mechanism.

---

## 3. The 5 Pillars

### 3.1 Pillar 1: Principal-Bound Identity

**Requirement:** Every agent MUST possess a principal-bound identity that cryptographically ties its actions to a responsible legal party (human or enterprise).

**Specification:**

- Non-repudiable identifiers MUST be tied to the responsible legal party (human or enterprise), delegated to the agent via post-quantum signatures (CRYSTALS-Dilithium5).
- Every action request MUST be signed by the agent's private key delegated by or bound to the principal.
- The principal's and agent's public keys MUST be resolvable by verifiers.
- Identity claims MUST NOT be revocable without an auditable record.

**Rationale:** An AI agent is code and lacks legal standing. Cryptographic identity must bind agent actions to a responsible legal principal (human or enterprise) so accountability is non-repudiable. Post-quantum schemes are mandatory because classical schemes (RSA, ECDSA) will be broken by quantum computers.

---

### 3.2 Pillar 2: Governance

**Requirement:** Every agent action MUST be evaluated against a capability policy before execution.

**Specification:**

- Agents possess zero inherent permissions. All capabilities MUST be granted.
- Capability grants MUST support at least these caveats:
  - **Expires** — Time after which the capability is invalid.
  - **MaxExecutions** — Maximum number of times the capability may be used.
  - **ValueLimit** — Maximum value the capability may affect.
  - **PathRestricted** — Restriction to specific resources.
- Policy evaluation MUST return a decision (Allow or Deny) with a reason.
- Denied actions MUST NOT be executed under any circumstances.
- The policy engine MUST log all evaluations to the audit trail (Pillar 4).

**Reference Logic (Capability Evaluation):**

```python
def evaluate_capability(capability: dict, action_value: float, current_time: float) -> tuple:
    """Evaluate whether an action request satisfies capability caveats."""
    if "expires" in capability and current_time > capability["expires"]:
        return False, "Capability expired"
    if "value_limit" in capability and action_value > capability["value_limit"]:
        return False, "Value limit exceeded"
    return True, "Allowed"
```

**Rationale:** Zero-trust means no implicit trust. Every action must be explicitly authorized.

---

### 3.3 Pillar 3: Consensus

**Requirement:** In multi-agent systems, decisions affecting high-value actions MUST require Byzantine Fault Tolerant consensus.

**Specification:**

- Multi-agent decisions MUST support threshold signature collection.
- Each vote MUST contain: `(voter_id, request_id, decision, outcome_hash, signature)`.
- The system MUST verify:
  - Each vote signature against the voter's registered public key.
  - No duplicate votes from the same voter.
  - Threshold agreement across distinct voters.
  - Matching outcome hashes among agreeing votes.
- The threshold MUST be configurable (RECOMMENDED: 2/3 majority).

**Rationale:** In multi-agent systems, one rogue agent must not be able to trigger high-value actions alone.

---

### 3.4 Pillar 4: Audit

**Requirement:** Every evaluated action MUST be recorded in a tamper-evident audit trail.

**Specification:**

- Audit records MUST be chained via SHA-256 Merkle chain.
- Each audit event MUST include:
  - Event ID (UUID)
  - Agent ID
  - Action request hash
  - Decision (Allow/Deny)
  - Reason
  - Timestamp
  - Parent hash (previous event)
  - Event hash
- The audit trail MUST be verifiable by a third party via `verify_history()`.
- Tampering with any past event MUST cause verification to fail.
- Audit trails MUST be exportable in a standard format (JSON Lines RECOMMENDED).

**Reference Logic (Audit Hash Calculation):**

```python
import hashlib


def calculate_event_hash(event_id: str, agent_id: str, request_hash: str, decision: str, reason: str, timestamp: str, parent_hash: str) -> str:
    """Calculate canonical SHA-256 event hash for audit log chain verification."""
    payload = f"{event_id}:{agent_id}:{request_hash}:{decision}:{reason}:{timestamp}:{parent_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

**Rationale:** Regulators and auditors require proof of what happened, in what order, and that nothing has been altered.

---

### 3.5 Pillar 5: Persistence

**Requirement:** Agent state and audit trails MUST persist across restarts with self-verifying integrity.

**Specification:**

- On reload, the system MUST verify the integrity of the audit chain.
- Any gap or alteration MUST be detected and reported.
- Agent identity keys MUST be persisted securely (HSM RECOMMENDED for Level 3).
- Persistent state MUST be exportable and importable across implementations.

**Rationale:** Without persistence, audit trails can be reset by simply restarting the system, defeating the purpose of Pillar 4.

---

## 4. Compliance Levels

### 4.1 Level 1: Basic

- Pillars 1 (Principal-Bound Identity) and 4 (Audit) are REQUIRED.
- Suitable for non-critical agents and internal tooling.

### 4.2 Level 2: Standard

- All 5 pillars are REQUIRED.
- Suitable for regulated industries and enterprise deployments.

### 4.3 Level 3: Enterprise

- All 5 pillars are REQUIRED.
- Additional requirements:
  - Hardware Security Module (HSM) for key storage.
  - SOC 2 Type II audit completion.
  - ISO 27001 certification.
  - 99.99% availability SLA.
- Suitable for banks, healthcare systems, and government deployments.

---

## 5. Testable Requirements

Each requirement below is testable by a third party.

### 5.1 Principal-Bound Identity Tests

- **T-1.1:** Submit an action with no signature. Result: MUST be Deny.
- **T-1.2:** Submit an action with an invalid signature. Result: MUST be Deny.
- **T-1.3:** Submit an action with a valid Dilithium5 signature. Result: MAY be Allow (if capability granted).

### 5.2 Governance Tests

- **T-2.1:** Submit an action without a granted capability. Result: MUST be Deny.
- **T-2.2:** Submit an action with an expired capability. Result: MUST be Deny.
- **T-2.3:** Submit an action exceeding ValueLimit. Result: MUST be Deny.
- **T-2.4:** Submit an action within granted bounds. Result: MUST be Allow.

### 5.3 Consensus Tests

- **T-3.1:** Multi-agent action without threshold consensus. Result: MUST be Deny.
- **T-3.2:** Multi-agent action with duplicate votes. Result: MUST be Deny.
- **T-3.3:** Multi-agent action with valid threshold. Result: MUST be Allow.

### 5.4 Audit Tests

- **T-4.1:** Execute 100 actions. Result: Chain length MUST equal 100.
- **T-4.2:** Modify event #50 in the chain. Result: `verify_history()` MUST return False.
- **T-4.3:** All events MUST be exportable in JSON Lines format.

### 5.5 Persistence Tests

- **T-5.1:** Restart the system. Result: Audit chain MUST be preserved and verifiable.
- **T-5.2:** Delete one event from disk. Result: `verify_history()` MUST return False.

---

## 6. Runtime Halt & Revocation (LGD State Machine)

### 6.1 Lifecycle State Machine

To enforce continuous runtime revocation without corrupting atomic execution, NTI-1 standardizes the LGD (Lifecycle Governance Domain) state machine sequence:

`REGISTERED -> GATE_PASSED -> ACTIVE -> ANOMALY -> PAUSE -> ROLLBACK -> REVERIFY -> RESUMED`

- **REGISTERED**: The agent identity is bound to a principal and registered with the trust authority.
- **GATE_PASSED**: Pre-execution capability policy and signature checks have succeeded.
- **ACTIVE**: The agent is actively executing authorized tool sub-calls.
- **ANOMALY**: Runtime anomaly or policy drift is detected by the sidecar or verification engine.
- **PAUSE**: Execution is immediately halted at the next tool sub-call boundary.
- **ROLLBACK**: Unverified or uncommitted actions are reverted to a safe state checkpoint.
- **REVERIFY**: Capabilities, signatures, and delegation proofs are re-evaluated.
- **RESUMED**: Following successful re-verification, the agent transitions back to active operation.

### 6.2 Fail-Closed Semantics for Unreachable Registries

When a revocation registry or trust authority is unreachable during runtime verification, the system MUST enforce fail-closed semantics to prevent silent execution under stale authority.

If a status check cannot be completed, the runtime MUST emit an `incomplete_check` block and transition immediately to `PAUSE`:

```json
{
  "incomplete_check": {
    "reason": "tryLater"
  }
}
```

The `reason` field MUST be set to one of the following canonical error values:

- `tryLater`: Temporary network or service unavailability; retry recommended after backoff.
- `not_authoritative`: The queried registry endpoint cannot provide authoritative status for the identity.
- `internal_error`: Unhandled internal exception or processing error during status resolution.

When an `incomplete_check` is encountered, the runtime sidecar MUST NOT allow the action request to proceed under assumed validity.

---

## 7. Ecosystem Interoperability: ASL Conformance Kit

### 7.1 CI/CD Pipeline Integration

NTI has integrated the ASL (Agent Security Lab) Conformance Kit into its CI/CD verification pipeline. This integration validates runtime containment across kernel-level egress confinement and 700-agent swarm stress tests.

### 7.2 Architectural Distinction

NTI and ASL serve complementary roles in the agentic trust stack:

- **ASL (Agent Security Lab)**: Provides local containment, operating as the isolated sandbox environment ("the test lab") that enforces OS-level egress filters, memory isolation, and swarm load boundaries.
- **NTI (Neutral Trust Infrastructure)**: Provides the cross-enterprise runtime trust layer ("the engine") that enforces principal-bound cryptographic identity, zero-trust policy evaluation, BFT consensus, and tamper-evident audit trails.

### 7.3 Interoperability Transport

ASL local containment and the NTI cross-enterprise trust engine interoperate via **AF_UNIX sockets**. This local IPC transport provides high-throughput, low-latency communication between the local kernel sandbox and the NTI cryptographic sidecar while preventing external socket interception.

---

## 8. Reference Implementation

The reference implementation is `ube-foundation`, available at:

- **PyPI:** <https://pypi.org/project/ube-foundation/>
- **crates.io:** <https://crates.io/crates/ube-foundation>
- **Repository:** <https://github.com/abisheakp197/Neutral-Trust-Infrastructure>

Framework integrations:

- `langchain-nti` — <https://pypi.org/project/langchain-nti/>
- `crewai-nti` — <https://pypi.org/project/crewai-nti/>
- `autogen-nti` — <https://pypi.org/project/autogen-nti/>

Alternative implementations are permitted and encouraged under the CC-BY-4.0 license terms.

---

## 9. Certification Process

### 9.1 Self-Assessment

Implementers MAY self-assess against this specification.

### 9.2 Third-Party Certification

For formal NTI-1 certification:

1. Implement all applicable pillar requirements.
2. Pass all testable requirements in Section 5.
3. Submit a certification request to the NTI Foundation.
4. Complete a third-party audit.
5. Receive certification valid for 12 months, renewable.

### 9.3 Public Registry

Certified implementations will be listed in the NTI Registry (forthcoming).

---

## 10. Governance

### 10.1 Steward

The NTI-1 specification is stewarded by the NTI Foundation.

### 10.2 Amendments

Proposed changes are submitted as RFCs in the `rfcs/` folder. Amendments require public comment and a 30-day review period.

### 10.3 Versioning

Specification versions use semantic versioning:

- **Major** — Incompatible changes
- **Minor** — Backwards-compatible additions
- **Patch** — Clarifications and errata

### 10.4 Neutrality

The NTI-1 standard MUST remain neutral. It MUST NOT favor any single vendor, platform, or jurisdiction.

---

## 11. Security Considerations

### 11.1 Quantum Threat

Classical signature schemes will be broken by sufficiently large quantum computers. NTI-1 mandates PQC from day one to avoid a costly migration later.

### 11.2 Side-Channel Attacks

Implementations SHOULD protect private keys against side-channel attacks via constant-time operations and, at Level 3, HSM storage.

### 11.3 Replay Attacks

Action requests MUST include a unique identifier (UUID) and timestamp to prevent replay.

### 11.4 Denial of Service

Verifiers MUST rate-limit request processing and MUST NOT block the audit chain under load.

### 11.5 Multi-Agent Collusion

BFT consensus (Pillar 3) is designed to resist up to $f < n/3$ malicious agents.

---

## 12. Appendix

### 12.1 Acknowledgements

This specification builds on decades of work in cryptography, distributed systems, and AI safety. It is offered as a neutral foundation for a global trust layer.

### 12.2 Feedback

Feedback is welcome at: <https://github.com/abisheakp197/nti-spec/issues>

---

## Document Status

End of Specification — Version 1.0.0-draft
