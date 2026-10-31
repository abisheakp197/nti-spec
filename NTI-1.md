# NTI-1 Specification: Neutral Trust Infrastructure - Standard 1

**License:** CC BY 4.0 | **Version:** 1.0.0-draft

## Table of Contents

1. [Introduction](#1-introduction)
2. [Terminology](#2-terminology)
3. [The 5 Pillars](#3-the-5-pillars)
4. [Compliance Levels](#4-compliance-levels)
5. [Testable Requirements](#5-testable-requirements)
6. [Runtime Halt & Revocation (LGD State Machine)](#6-runtime-halt--revocation-lgd-state-machine)
7. [Ecosystem Interoperability (ASL Conformance Kit)](#7-ecosystem-interoperability-asl-conformance-kit)
8. [Reference Implementation](#8-reference-implementation)
9. [Certification Process](#9-certification-process)
10. [Governance](#10-governance)
11. [Security Considerations](#11-security-considerations)
12. [Appendix](#12-appendix)

---

## 1. Introduction

This document specifies NTI-1, the foundational open standard for post-quantum, zero-trust governance of autonomous AI agents. NTI-1 defines formal technical requirements across five core pillars, establishing verifiable trust, non-repudiation, and BFT multi-agent consensus for enterprise deployment environments.

## 2. Terminology

* **Agent:** An autonomous software system that perceives, decides, and acts.
* **Action:** A discrete operation executed by an agent with external effect.
* **Capability:** An explicit permission granted to an agent to perform a specific class of actions.
* **Caveat:** A condition attached to a capability (e.g., Expires, ValueLimit).
* **Trust Engine:** The component that evaluates an action against policy.
* **Merkle Chain:** A cryptographic hash chain over a sequence of events.
* **PQC:** Post-Quantum Cryptography.
* **Dilithium5:** CRYSTALS-Dilithium5, a NIST Level 5 post-quantum signature algorithm.

## 3. The 5 Pillars

### 3.1 Pillar 1: Principal-Bound Identity

**Requirement:** Every agent MUST possess a principal-bound identity that cryptographically ties its actions to a responsible legal party (human or enterprise).

**Specification:**

* Non-repudiable identifiers MUST be tied to the responsible legal party, delegated to the agent via CRYSTALS-Dilithium5.
* Every action request MUST be signed by the agent's private key delegated by or bound to the principal.
* Identity claims MUST NOT be revocable without an auditable record.

**Rationale:** An AI agent is code and lacks legal standing. Cryptographic identity must bind agent actions to a responsible legal principal.

### 3.2 Pillar 2: Governance

**Requirement:** Every agent action MUST be evaluated against a policy before execution.

**Specification:**

* Agents possess zero inherent permissions. All capabilities MUST be granted.
* Capability grants MUST support at least these caveats: `Expires`, `MaxExecutions`, `ValueLimit`, `PathRestricted`.
* Policy evaluation MUST return a decision (Allow or Deny) with a reason.
* Denied actions MUST NOT be executed under any circumstances.

### 3.3 Pillar 3: Consensus

**Requirement:** In multi-agent systems, decisions affecting high-value actions MUST require Byzantine Fault Tolerant consensus.

**Specification:**

* Multi-agent decisions MUST support threshold signature collection.
* Each vote MUST contain: `(voter_id, request_id, decision, outcome_hash, signature)`.
* The system MUST verify: no duplicate votes, threshold agreement, and matching outcome hashes.
* The threshold MUST be configurable (RECOMMENDED: 2/3 majority).

### 3.4 Pillar 4: Audit

**Requirement:** Every evaluated action MUST be recorded in a tamper-evident audit trail.

**Specification:**

* Audit records MUST be chained via SHA-256 Merkle chain.
* Each audit event MUST include: Event ID, Agent ID, Action hash, Decision, Reason, Timestamp, Parent hash, Event hash.
* Tampering with any past event MUST cause verification to fail.

### 3.5 Pillar 5: Persistence

**Requirement:** Agent state and audit trails MUST persist across restarts with self-verifying integrity.

**Specification:**

* On reload, the system MUST verify the integrity of the audit chain.
* Agent identity keys MUST be persisted securely (HSM support at Level 3).
* Persistent state MUST be exportable and importable.

## 4. Compliance Levels

* **Level 1 (Basic):** Pillars 1 and 4 REQUIRED. Suitable for internal tooling.
* **Level 2 (Standard):** All 5 Pillars REQUIRED. Suitable for regulated industries.
* **Level 3 (Enterprise):** All 5 Pillars + HSM key storage, SOC 2 Type II, ISO 27001, and 99.99% availability SLA.

## 5. Testable Requirements

(Implementation MUST pass these tests to claim compliance)

* **T-1.1 (Identity):** Submit action with no signature. Result: MUST be Deny.
* **T-2.1 (Governance):** Submit action with expired capability. Result: MUST be Deny.
* **T-3.1 (Consensus):** Multi-agent action without threshold. Result: MUST be Deny.
* **T-4.1 (Audit):** Execute 100 actions. Result: Chain length MUST equal 100.
* **T-5.1 (Persistence):** Restart system. Result: Audit chain MUST be preserved.

## 6. Runtime Halt & Revocation (LGD State Machine)

To enforce continuous runtime revocation without corrupting atomic execution, NTI-1 standardizes the LGD (Lifecycle Governance Domain) state machine sequence:

`REGISTERED -> GATE_PASSED -> ACTIVE -> ANOMALY -> PAUSE -> ROLLBACK -> REVERIFY -> RESUMED`

> **Reference (draft for comment).** The state-machine logic and the `resume_basis` field below are drawn from the *NTI x LGD transition-contract spec - v0.1.4*, prepared by Xinghua Zhao (2026-10-30). That document is **draft for comment and explicitly "not agreed" by either side** (see its sec.0.1 / sec.0.3); it carries no standards-body weight outside its originating thread. It is linked here as a working reference for implementers, not as a ratified normative annex. Canonical, byte-for-byte copy: <https://github.com/zhaoxinghua09-cell/nti-lgd-transition-contract/blob/679b6e4445fb84e26cc051cda3b0ebed3d5526c3/nti-transition-contract-spec-v0.1.4.md>

### 6.1 Fail-Closed Semantics (`incomplete_check`)

When a revocation registry or trust authority is unreachable, the system MUST enforce fail-closed execution. If a status check cannot be completed, the runtime MUST emit an `incomplete_check` and halt. The `reason` field MUST be set to one of the following:

* `tryLater`: Temporary network unavailability.
* `not_authoritative`: Queried registry cannot provide authoritative status.
* `internal_error`: Unhandled exception during status resolution.

When `incomplete_check` is encountered, the runtime sidecar MUST NOT allow the action to proceed.

### 6.2 Resume Receipt - the `resume_basis` field

When the `REVERIFY -> RESUMED` edge is taken, the RESUME receipt MUST carry a `resume_basis` value from the closed set:

* `evidence` - the registered restore condition was verified in full (evidence list, verifier role, validity window): the condition that caused the halt was confirmed restored.
* `exemption` - an accountability layer accepted the risk; the reason is recorded, **not evaluated**. Both values permit `RESUMED`.

The field adds to the RESUME receipt only; it does not add, remove, or rename a state, and the sec.6 transition line is unchanged.

**Exemption boundaries (MUST be in the schema):**

* `exemption_covers = policy_violation`
* `exemption_does_not_cover = authority_revoked, authority_not_determined`

`authority_revoked` is the issuing authority's decision, not the executing side's; a signed justification cannot un-revoke it. `authority_not_determined` is an absence of information (registry unreachable / stale root), not a judgment; a signature cannot convert "unknown" into "known". An exemption MUST NOT buy back the fail-closed property: `authority_revoked` and `authority_not_determined` MUST NOT be resumed on `exemption`.

## 7. Ecosystem Interoperability (ASL Conformance Kit)

NTI-1 standardizes interoperability with the ASL Conformance Kit. The NTI CI/CD pipeline executes ASL static test vectors to verify agent sandbox behavior and dynamic runtime drift.

* **ASL (Local Containment / Test Lab):** Provides OS-level and kernel-level egress sandbox isolation.
* **NTI (Cross-Enterprise Trust Engine):** Enforces principal-bound post-quantum identity and BFT consensus.
* **Transport:** ASL sandboxes interface with the NTI sidecar via local IPC using **AF_UNIX sockets**, guaranteeing high throughput and protection against wire interception.

## 8. Reference Implementation

The reference implementation is `ube-foundation`.

* **PyPI:** <https://pypi.org/project/ube-foundation/>
* **crates.io:** <https://crates.io/crates/ube-foundation>
* **Repository:** <https://github.com/abisheakp197/Neutral-Trust-Infrastructure>

Framework Integrations: `langchain-nti`, `crewai-nti`, `autogen-nti`.

## 9. Certification Process

1. Implement all applicable pillar requirements.
2. Pass all testable requirements in Section 5.
3. Submit a certification request to the NTI Foundation.
4. Complete a third-party audit.
5. Receive certification valid for 12 months.

## 10. Governance

The NTI-1 specification is stewarded by the NTI Foundation. Proposed changes are submitted as RFCs. Amendments require public comment and a 30-day review period. The standard MUST remain neutral and MUST NOT favor any single vendor or jurisdiction.

## 11. Security Considerations

* **Quantum Threat:** Classical schemes will be broken by quantum computers. NTI-1 mandates PQC from day one.
* **Side-Channel Attacks:** Implementations SHOULD protect private keys via constant-time operations.
* **Replay Attacks:** Action requests MUST include a unique identifier and timestamp.

## 12. Appendix

**Acknowledgements:** This specification builds on decades of work in cryptography, distributed systems, and AI safety, specifically incorporating W3C CG feedback on Principal-Bound Identity and the LGD state machine.

**Feedback:** Welcome at <https://github.com/abisheakp197/nti-spec/issues>
