# LFDT Lab Proposal: Neutral Trust Infrastructure (NTI)

**Status:** Proposal to establish NTI as a Linux Foundation Decentralized Trust (LFDT) Lab.
**Requested action:** None from the TAC. A Lab requires no endorsements and no TAC vote; it is established by two Lab Stewards.

## Summary

Neutral Trust Infrastructure (NTI) is applying to become an LFDT Lab. The Lab builds on the existing **Agent Authority Conformance** lab, extending its authority-conformance work into runtime enforcement: verifying, at invocation time, that a specific action by a specific agent was authorized.

A Lab is the right vehicle for this work. It is a lightweight, low-ceremony home for a focused effort that already has a running reference implementation, a specification, and conformance vectors. It requires no endorsements and no TAC vote, which keeps the effort neutral and free of the endorsement politics that have surrounded adjacent proposals.

## Scope

The Lab will host and steward:

- The NTI specification (`NTI-1.md`) and its RFC process.
- The reference implementation and its conformance vectors.
- Cross-project conformance work with the Agent Authority Conformance lab, including shared test vectors for the authority-delegation boundary.

The Lab does not issue certifications and does not speak for any other project. Where an adjacent project already defines a format or identifier, the Lab adopts it rather than inventing a competing one.

## Relationship to the Agent Authority Conformance Lab

NTI builds on the Agent Authority Conformance lab rather than competing with it. Agent Authority Conformance defines and tests what a valid authority delegation is; NTI provides the runtime enforcement point that checks such a delegation when an agent acts. The two layers compose: conformance defines the contract, NTI enforces it at the moment of action.

## Lab Stewards

| Steward | Affiliation |
| :--- | :--- |
| Abisheak P. | Neutral Trust Infrastructure (NTI) |
| Tymofii Pidlisnyi | Agent Authority Conformance |

The two stewards are drawn from two independent projects, each with its own repository and release cadence. Stewards act in their own capacity; no single organization holds more than one steward seat. The Lab is committed to adding stewards as the contributor base grows.

## Governance and Neutrality

- The specification is licensed under CC BY 4.0 and the reference implementation under Apache-2.0.
- Contributions use the Developer Certificate of Origin (DCO) exclusively; no CLA is required.
- The Lab does not require or record endorsements. Endorsement is opt-in and individually given, and no reviewer's participation, silence, or past collaboration is represented as endorsement.

## What Is Requested

Establish NTI as an LFDT Lab, co-stewarded by the two stewards named above. No TAC vote and no endorsements are required for a Lab. We ask only for the Lab to be recognized so the work has a neutral, durable home under LFDT.

## Next Steps

1. Confirm the two Lab Stewards.
2. Recognize the Lab under LFDT.
3. Publish the Lab's charter, repository, and conformance process.

---

*See `LFDT-PROPOSAL.md` for the full project proposal.*
