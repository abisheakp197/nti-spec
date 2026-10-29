# Neutral Trust Infrastructure (NTI): Bridging Audit and Execution for the Agentic Web

**Author:** Abisheak P.
**Date:** October 28, 2026
**Submission:** AIW #3 Book of Proceedings (Delegation and Authorization Cluster)
**License:** CC BY 4.0

## Abstract

As autonomous AI agents transition from experimental chat interfaces to operational infrastructure, the industry faces a critical gap in trust. Current frameworks like OAuth, ZCAP, and UCAN handle access control, while protocols like HDP provide post-incident audit trails. However, neither addresses the "runtime gap"—the ability to enforce cryptographic non-repudiation and halt an agent chain *mid-execution* when intent drifts.

This paper proposes Neutral Trust Infrastructure (NTI), a framework-agnostic, post-quantum sidecar architecture. NTI bridges the gap between audit (HDP) and execution by acting as a fail-closed cryptographic bouncer at the tool-call boundary, solving the "key leakage" problem and providing a continuous runtime revocation model.

## 1. The Problem: Audit vs. Enforcement

A key debate in the W3C AI Agent Protocol Community Group is how to secure delegation chains.

* **HDP** (Human Delegation Provenance) records the chain after the fact.
* **ZCAP/UCAN** handle pre-authorization at the boundary.
* **The Gap:** If an AI agent is compromised via indirect prompt injection, an audit log tells you what went wrong *after* the database was deleted. Pre-authorization fails because agents are notoriously bad at keeping secrets. If the agent holds the private key, the attacker holds the private key.

## 2. The NTI Architecture

NTI operates as a zero-trust sidecar (`NTIGuardrailMiddleware`). The agent never holds the private key.

1. **Isolated Crypto Engine:** Dilithium5 (ML-DSA) keys are managed in an isolated Rust core outside the LLM context window.
2. **Execution Interception:** When an agent requests a tool call, the sidecar intercepts the payload.
3. **Fail-Closed Verification:** The Rust core verifies the agent's capability bounds, signs the payload, and generates a Merkle-chained receipt. If the signature or policy check fails, execution is blocked (PermissionError).

## 3. Solving the Runtime Gap (Response to AIW Topic 2)

How do we pause, halt, or revoke a live agent chain? Based on discussions in the W3C AI Agent Protocol Community Group, the NTI runtime enforcement model is defined as follows:

* **The Safe Interruption Point:** You cannot safely interrupt an atomic tool execution mid-flight without corrupting external state. NTI enforces pauses strictly at the sub-call boundary. The agent finishes its current atomic tool call, and the sidecar intercepts the *next* planned execution payload.
* **Continuous State Heartbeat:** The NTI sidecar maintains a live connection to the Trust Engine. A policy layer (human or automated) can issue a "pause" or "halt" command to the Trust Engine. The sidecar intercepts the next internal agent loop and forces a suspension.
* **LGD Lifecycle State Machine (Contributed by Steven Zhao):** We adopt the LGD state transitions for runtime halts: `REGISTERED -> GATE_PASSED -> ACTIVE -> ANOMALY -> PAUSE -> ROLLBACK -> REVERIFY -> RESUMED`.
* **Enforcement over Policy (Response to Alan Karp):** While an LLM can evaluate policy and signal a `PAUSE`, it cannot be trusted to enforce it. The NTI sidecar is the deterministic enforcement layer. It intercepts the execution loop, blocks the socket connection, and signs the `PAUSE` or `ROLLBACK` receipt using Dilithium5.
* **Merkle-Chained Revocation Registry:** Capability tokens are bound to a root hash. If a human or policy layer issues a `PAUSE`, the root hash updates. The sidecar verifies the token's Merkle proof against the *latest* root hash in real-time. Even if the token was issued mid-chain, it is rejected at the boundary.

## 4. The Regulatory Necessity (EU AI Act & SOC2)

Under EU consumer law (Directive 2011/83/EU, Art. 8(2)), merchants must prove explicit acknowledgment of an order. If an agent places an order, the merchant must cryptographically prove *which human* delegated the authority. HDP records the intent, but NTI enforces the boundary. Together, they create a court-admissible SOC2 and EU AI Act compliance stack.

## 5. The NTI-1 Standard (5 Pillars)

To ensure enterprise compliance, the NTI-1 specification defines five core pillars:

1. **Identity:** CRYSTALS-Dilithium5 post-quantum signatures (NIST Level 5).
2. **Governance:** Zero-trust capability model with granular caveats.
3. **Consensus:** BFT threshold decision validation for multi-agent workflows.
4. **Audit:** SHA-256 Merkle-chained event logs.
5. **Persistence:** Self-verifying state integrity across restarts (HSM support).

## 6. Conclusion

NTI does not replace HDP, OAuth, or ZCAP. It is the neutral enforcement layer that makes them viable for enterprise deployment. By isolating keys, enforcing post-quantum signatures, and enabling continuous runtime revocation, NTI provides the missing infrastructure for the Agentic Web.

---
**The Standard (NTI-1 Spec):** <https://github.com/abisheakp197/nti-spec>
**Reference Implementation:** <https://github.com/abisheakp197/Neutral-Trust-Infrastructure>
**Compliance Leaderboard:** <https://nti-leaderboard.vercel.app>
