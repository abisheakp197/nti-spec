# LFDT Lab Proposal: Neutral Trust Infrastructure (NTI)

**Status:** Proposal to establish NTI as a Linux Foundation Decentralized Trust (LFDT) Lab.
**Requested action:** None from the TAC. A Lab requires no endorsements and no TAC vote; it is governed by the LFDT Lab Stewards.

## Summary

Neutral Trust Infrastructure (NTI) is applying to become an LFDT Lab. The Lab extends published authority-conformance work into runtime enforcement: verifying, at invocation time, that a specific action by a specific agent was authorized. It references the published work of the **Agent Authority Conformance** project; it claims no formal relationship with that project.

A Lab is the right vehicle for this work. It is a lightweight, low-ceremony home for a focused effort that already has a running reference implementation, a specification, and conformance vectors. It requires no endorsements and no TAC vote, which keeps the effort neutral and free of the endorsement politics that have surrounded adjacent proposals.

## Scope

The Lab will host and steward:

- The NTI specification (`NTI-1.md`) and its RFC process.
- The reference implementation and its conformance vectors.
- Conformance work that aligns with published authority-conformance work, including test vectors for the authority-delegation boundary.

The Lab does not issue certifications and does not speak for any other project. Where an adjacent project already defines a format or identifier, the Lab adopts it rather than inventing a competing one.

## Reference to Published Authority-Conformance Work

NTI references the published work of the Agent Authority Conformance project rather than competing with it. Published authority-conformance work defines and tests what a valid authority delegation is; NTI provides the runtime enforcement point that checks such a delegation when an agent acts. The two layers compose: conformance defines the contract, NTI enforces it at the moment of action.

No formal relationship between the two projects is claimed. The Agent Authority Conformance project does not participate in, sponsor, or endorse NTI; its published work is referenced for technical context only.

## Maintainers

This Lab will be governed by the LFDT Lab Stewards.

| Maintainer | Affiliation |
| :--- | :--- |
| Abisheak P. | Neutral Trust Infrastructure (NTI) |

Maintainers act in their own capacity; no single organization holds more than one maintainer seat. The Lab is committed to adding maintainers as the contributor base grows.

## Governance and Neutrality

- The specification is licensed under the Community Specification License 1.0 (CSL) and the reference implementation under Apache-2.0.
- Code contributions use the Developer Certificate of Origin (DCO); no separate CLA is required for code. Specification contributions are made under the Community Specification License 1.0 (CSL) framework, which includes the Community Specification Contributor License Agreement.
- The Lab does not require or record endorsements. Endorsement is opt-in and individually given, and no reviewer's participation, silence, or past collaboration is represented as endorsement.

## What Is Requested

Establish NTI as an LFDT Lab, governed by the LFDT Lab Stewards. No TAC vote and no endorsements are required for a Lab. We ask only for the Lab to be recognized so the work has a neutral, durable home under LFDT.

## Next Steps

1. Complete steward review of this proposal.
2. Recognize the Lab under LFDT.
3. Publish the Lab's charter, repository, and conformance process.

---

*See `LFDT-PROPOSAL.md` for the full project proposal.*
