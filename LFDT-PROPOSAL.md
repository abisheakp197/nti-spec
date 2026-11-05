# Project Proposal: Neutral Trust Infrastructure (NTI) to LF Decentralized Trust

## 1. Project Description

Neutral Trust Infrastructure (NTI) is a post-quantum (ML-DSA-87), custody-free, federated runtime enforcement sidecar for AI agents. NTI provides the missing Layer 1 trust mechanism for the machine economy. It mathematically verifies delegation chains at invocation time, ensuring that no captured or compromised system can define truth for the network.

The NTI sidecar sits between the agent and the network, intercepting outbound actions to generate cryptographic Merkle proofs and ML-DSA-87 signatures. The target resource's verifier then independently checks this cryptographic delegation chain at invocation time. The sidecar provides the math; the resource verifier enforces the access. The sidecar does not act as a proxy or replace the resource's native policy enforcement.

## 2. Initial Proposed TSC

Per the principles of explicit consent and decentralized governance, the following individuals have explicitly accepted a seat on the initial proposed Technical Steering Committee:

* **Abisheak P.** (Lead Architect, NTI)
* **Steven Zhao (Xinghua)** (Independent Researcher, ORCID: 0009-0001-0512-1237)

## 3. External Advisors

The following individual provides independent architectural review and guidance, ensuring the standard remains aligned with capability-based security principles:

* **Alan Karp** (Capability Security Expert)

## 4. Active Contributors (Non-TSC)

The following individuals have made significant technical contributions to the NTI-1 specification and reference implementation, but have not yet been formally confirmed for the TSC:

* **Larry Lewis** (Rust Core Contributor, W3C CG Chair)
* **Chris Hopley** (Cryptographic Conformance, AlgoVoi)

## 5. Vendor Neutrality & Governance

NTI is committed to absolute vendor neutrality. The specification is licensed under CC BY 4.0 and the reference implementation under Apache 2.0. The conformance lab remains strictly independent from the TSC to ensure separation of powers. Silence or past collaboration does not count as consent; any changes to the shared governance map require explicit confirmation from the project maintainer.
