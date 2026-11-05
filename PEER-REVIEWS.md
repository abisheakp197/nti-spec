# Peer Reviews

## 2026-11-05: Alan Karp Review

**Reviewer:** Alan Karp (Capability Security Expert)
**Date:** 2026-11-05
**Topic:** Architectural Boundary & Sidecar Verification Mechanics

### Review Summary & Correction

During architectural review of the NTI-1 specification, Alan Karp provided the following correction regarding sidecar placement and invocation-time verification:

> "The NTI sidecar is between the agent and the network. The resource's verifier acts on invocation, which doesn't involve a sidecar unless the resource is controlled by an agent, which is not common."

### Impact on Specification

The architectural clarification distinguishes between:

1. The client-side NTI sidecar running alongside the autonomous AI agent, which constructs delegation chains, Merkle proofs, and signatures.
2. The target resource verifier, which independently checks capability delegation proofs upon invocation without relying on a sidecar unless the target resource itself is agent-controlled.
