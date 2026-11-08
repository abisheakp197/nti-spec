# Project Proposal: Neutral Trust Infrastructure (NTI) to LF Decentralized Trust

## 1. Project Description

Neutral Trust Infrastructure (NTI) is a post-quantum (ML-DSA-87), custody-free, federated runtime enforcement sidecar for AI agents. NTI provides the missing Layer 1 trust mechanism for the machine economy. It mathematically verifies delegation chains at invocation time, ensuring that no captured or compromised system can define truth for the network.

The NTI sidecar sits between the agent and the network, intercepting outbound actions to generate cryptographic Merkle proofs and ML-DSA-87 signatures. The target resource's verifier then independently checks this cryptographic delegation chain at invocation time. The sidecar provides the math; the resource verifier enforces the access. The sidecar does not act as a proxy or replace the resource's native policy enforcement.

## 2. Motivation

Autonomous agents are increasingly granted the ability to act — to move value, call APIs, and change state — but the infrastructure that verifies *whether an agent was actually authorized to take a given action at the moment it took it* is thin. Existing projects solve adjacent problems well: identity issuance, credential formats, and evidence packaging. None provides a runtime enforcement point that cryptographically binds an agent's authorization to the specific action it is attempting, verifiable by the resource being acted upon.

NTI is proposed because this is a distinct layer, not a feature of an existing project, and because the maintainers of the adjacent projects have agreed the boundary should be a separate effort rather than a contribution into any one of them.

### 2.1 Distinct Advantage & Non-Overlap

NTI provides runtime enforcement for autonomous agents (Layer 1). It does not replace identity issuance (Identus/AnonCreds) or evidence packaging (ThunderID). It is designed to interoperate with them by verifying their cryptographic receipts at invocation time.

Concretely:

- **Identity issuance** (e.g. Identus, AnonCreds) answers *who is this agent and who vouches for it*. NTI consumes the resulting identifiers and keys; it does not issue them.
- **Evidence packaging and lifecycle governance** (e.g. ThunderID, UIBC) answers *what happened and how is it packaged for later review*. NTI produces the invocation-time cryptographic receipt that such packages can carry; it does not define the package format.
- **Runtime enforcement** — NTI's layer — answers *was this specific action, by this agent, authorized at this moment*, and gives the resource a proof it can check without trusting the agent.

This separation is deliberate. The NTI sidecar does not sit on the critical path as a proxy and does not become a single point of trust; the resource verifier performs its own check. Where an adjacent project already defines a format or identifier, NTI adopts it rather than inventing a competing one. Prior to submission, the maintainers contacted the relevant adjacent projects to confirm this boundary and that the work could not be contributed directly.

## 3. Solution

NTI consists of a reference implementation (Rust core with Python bindings, Apache-2.0) and a specification (CC BY 4.0), together with conformance vectors that any independent implementation can run against.

The sidecar constructs, for each outbound action:

1. A canonical serialization of the action and its authorizing delegation chain.
2. A Merkle tree over the delegation chain, producing an inclusion proof.
3. An ML-DSA-87 (FIPS 204) signature over a domain-separated, length-prefixed payload that binds the action digest, the delegation root, the signer's verification method, and the authoritative identifiers (receipt id, attempt id, idempotency key).

The resource-side verifier then independently recomputes the payload digest, the Merkle root, and the signature check. Verification is self-contained and requires no call back to the agent.

### 3.1 Verifiable Cryptographic Evidence

**We make no unverifiable claims.** Every cryptographic claim in this proposal is backed by an artifact a third party can independently reproduce:

- **Reproducible, not asserted.** The reference implementation ships a witness package — a signed manifest of conformance results — published at
  <https://abisheakp197.github.io/Neutral-Trust-Infrastructure/witness/>.
  It includes the public key, the manifest, the signature, and the scripts to
  re-run the checks, so anyone can confirm or refute the result. Our Merkle trees
  and ML-DSA-87 signatures are **reproducible**: the verification procedure is
  fully specified and open, and the published public key lets any party check the
  signature without trusting us.
- **Audit status stated plainly.** The project has completed an internal security
  review (documented in `AUDIT_REPORT.md`). An **independent third-party audit has
  not yet been completed**; commissioning one is an explicit roadmap item and a
  criterion the maintainers intend to meet on the path to Graduated status. We
  state this rather than overstate it.
- **Standards alignment.** Signatures use ML-DSA-87 (FIPS 204) and key
  encapsulation uses ML-KEM-1024 (FIPS 203), via widely used Rust crates
  (`pqcrypto-dilithium`, `pqcrypto-kyber`). We make no claim of formal
  certification.

## 4. Initial Proposed TSC

Per the principles of explicit consent and decentralized governance, the following individuals have explicitly accepted a seat on the initial proposed Technical Steering Committee. The TSC represents multiple independent organizations: NTI (Abisheak P.), UIBC (Steven Zhao), and VATE (Takao Sato).

- **Abisheak P.** (Lead Architect, NTI)
- **Steven Zhao (Xinghua)** (UIBC — evidence packaging & lifecycle governance; ORCID: 0009-0001-0512-1237)
- **Takao Sato (Poke-nushi)** (VATE — verifier-side receiving layer)

These three projects are independently governed, with separate repositories and release cadences. No single organization holds more than one seat. The maintainers are committed to growing the TSC further and increasing organizational diversity as the contributor base expands.

## 5. External Advisors

The following individual provides independent architectural review and guidance, ensuring the standard remains aligned with capability-based security principles:

- **Alan Karp** (Capability Security Expert)

## 6. Active Contributors (Non-TSC)

The following individuals have made significant technical contributions to the NTI-1 specification and reference implementation, but have not yet been formally confirmed for the TSC:

- **Larry Lewis** (Rust Core Contributor, W3C CG Chair)
- **Chris Hopley** (Cryptographic Conformance, AlgoVoi)

## 7. Vendor Neutrality & Governance

NTI is committed to absolute vendor neutrality. The specification is licensed under CC BY 4.0 and the reference implementation under Apache 2.0. The conformance lab remains strictly independent from the TSC to ensure separation of powers. Silence or past collaboration does not count as consent; any changes to the shared governance map require explicit confirmation from the project maintainer.

Project governance — including TSC composition and the rough-consensus decision process — is documented in the reference implementation repository (`GOVERNANCE.md`, `MAINTAINERS.md`).
