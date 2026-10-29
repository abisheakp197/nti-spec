# Neutral Trust Infrastructure (NTI): Bridging Audit and Execution for the Agentic Web

**Author:** Abisheak P.
**Date:** October 28, 2026
**Submission:** AIW #3 Book of Proceedings (Delegation and Authorization Cluster)
**License:** CC BY 4.0

## Abstract

As autonomous AI agents transition from experimental chat interfaces to operational infrastructure, the industry faces a critical gap in trust. Current frameworks like OAuth, ZCAP, and UCAN handle access control, while protocols like HDP provide post-incident audit trails. However, neither addresses the "runtime gap"—the ability to enforce cryptographic non-repudiation and halt an agent chain *mid-execution* when intent drifts.

This paper proposes Neutral Trust Infrastructure (NTI), a framework-agnostic, post-quantum sidecar architecture. NTI bridges the gap between audit (HDP) and execution by acting as a fail-closed cryptographic bouncer at the tool-call boundary, solving the "key leakage" problem and providing a continuous runtime revocation model anchored in principal-bound legal identity.

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

## 3. Solving the Runtime Gap (LGD State Machine)

How do we pause, halt, or revoke a live agent chain? Based on discussions in the W3C AI Agent Protocol Community Group, the NTI runtime enforcement model integrates the Lifecycle Governance Domain (LGD) state machine to enforce deterministic mid-flight halts.

### Safe Interruption Point & Enforcement

* **Safe Interruption Boundary:** Atomic tool execution cannot be interrupted mid-flight without risking external state corruption. NTI enforces execution halts strictly at the sub-call boundary: the current atomic tool call completes, and the sidecar intercepts the subsequent planned payload.
* **Continuous Heartbeat & Control:** The NTI sidecar maintains a real-time connection to the Trust Engine. A policy layer or human operator can broadcast a halt or pause directive, which the sidecar captures before the next agent loop iteration.
* **Enforcement over Policy (Response to Alan Karp):** While an LLM or policy evaluator can signal a `PAUSE`, it cannot be relied upon to enforce its own suspension. The NTI sidecar serves as the deterministic enforcement layer, severing socket connections and producing signed Dilithium5 revocation receipts.

### LGD State Machine Sequence

To standardize runtime revocation and execution halts, NTI adopts the LGD state transitions:

`REGISTERED -> GATE_PASSED -> ACTIVE -> ANOMALY -> PAUSE -> ROLLBACK -> REVERIFY -> RESUMED`

1. **REGISTERED:** Agent identity and principal delegation proofs are registered with the trust authority.
2. **GATE_PASSED:** Initial capability policy and cryptographic signatures pass boundary checks.
3. **ACTIVE:** The agent executes authorized tool sub-calls.
4. **ANOMALY:** Intent drift, prompt injection, or policy violation is detected.
5. **PAUSE:** The sidecar immediately halts execution at the next tool sub-call boundary.
6. **ROLLBACK:** Unverified or uncommitted operations are reverted to a verified checkpoint.
7. **REVERIFY:** Delegation chains and capability tokens are re-checked against authority records.
8. **RESUMED:** Normal execution resumes following successful re-verification.

### Fail-Closed Semantics (`incomplete_check`)

When a revocation registry or authority endpoint is unreachable or returns an indeterminate status, the runtime MUST NOT fall back to permissive execution. Instead, the sidecar enforces fail-closed semantics by emitting an `incomplete_check` block and forcing an immediate transition to `PAUSE`:

```json
{
  "incomplete_check": {
    "reason": "tryLater"
  }
}
```

The `reason` field categorizes the nature of the unreachable status:

* `tryLater`: Transient network failure or remote service unavailability.
* `not_authoritative`: The queried endpoint is not recognized as an authoritative registry for the agent principal.
* `internal_error`: Execution error during revocation evaluation.

Requiring an immediate `PAUSE` on `incomplete_check` prevents silent execution under stale or unverified authority.

## 4. The Regulatory Necessity (EU AI Act & SOC2)

Under EU consumer law (Directive 2011/83/EU, Art. 8(2)), merchants must prove explicit acknowledgment of an order. If an agent places an order, the merchant must cryptographically prove *which human* delegated the authority.

HDP records the intent, but NTI enforces the boundary. Together, they create a court-admissible SOC2 and EU AI Act compliance stack by establishing non-repudiable audit records tied directly to legal entities with real-time fail-closed execution controls.

## 5. The NTI-1 Standard (5 Pillars)

To ensure enterprise compliance, the NTI-1 specification defines five core pillars:

1. **Principal-Bound Identity:** Non-repudiable identifiers tied to the responsible legal party (human or enterprise), delegated to the agent via post-quantum signatures (CRYSTALS-Dilithium5).
2. **Governance:** Zero-trust capability model with granular caveats.
3. **Consensus:** BFT threshold decision validation for multi-agent workflows.
4. **Audit:** SHA-256 Merkle-chained event logs.
5. **Persistence:** Self-verifying state integrity across restarts (HSM support).

## 6. Ecosystem Interoperability (ASL Conformance Kit)

To demonstrate multi-environment interoperability and rigorous safety bounds, NTI has successfully integrated the ASL (Agent Security Lab) Conformance Kit into its automated CI/CD pipeline.

### Test Lab vs. Cross-Enterprise Engine

The integration establishes a clear architectural distinction between local containment and cross-enterprise trust:

* **ASL (Local Containment / The Test Lab):** Integrates Raja's static test vectors, kernel-level egress confinement, OS-level sandbox isolation, and simulated 700-agent swarm stress testing to ensure local agent bounds are enforced.
* **NTI (Cross-Enterprise Trust / The Engine):** Provides the distributed cryptographic runtime engine, maintaining principal-bound post-quantum identity, BFT multi-agent consensus, and cross-organization Merkle audit logs.

### Interoperability via AF_UNIX Sockets

ASL local sandboxes interoperate with the NTI runtime engine via high-throughput **AF_UNIX sockets** within the CI/CD pipeline. This local IPC interface connects kernel-confined agent execution environments directly with the out-of-process NTI sidecar, ensuring low-latency cryptographic verification without exposing keying material or control channels to network attack vectors.

## 7. Conclusion

NTI does not replace HDP, OAuth, or ZCAP. It is the neutral enforcement layer that makes them viable for enterprise deployment. By isolating keys, enforcing principal-bound post-quantum signatures, and enabling continuous runtime revocation, NTI provides the missing infrastructure for the Agentic Web.

## References

1. Karp, A. (2026). *Policy Evaluation vs. Execution Enforcement in Autonomous Agent Workflows*. W3C AI Agent Protocol CG / LinkedIn Post.
2. W3C AI Agent Protocol Community Group. (2026). *Human Delegation Provenance (HDP) & Zero-Trust Capability Standards*.
3. NTI Specification Repository: <https://github.com/abisheakp197/nti-spec>
4. NTI Reference Implementation: <https://github.com/abisheakp197/Neutral-Trust-Infrastructure>
5. NTI Compliance Leaderboard: <https://nti-leaderboard.vercel.app>
