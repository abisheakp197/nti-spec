# NTI Compliance Crosswalk

> **Status: draft (v1.0.0-draft), for discussion.** NTI-1 is a draft proposal under
> public review, not a ratified standard (see [README.md](./README.md)). This
> crosswalk is an engineering mapping, not a legal opinion, not an audit, and not
> a certification. It describes which NTI-1 artefacts *can* produce evidence for
> the named controls, and where the implementer must supply evidence that NTI
> does not produce. Control text is summarised in paraphrase; consult the official
> source for the authoritative wording.

## 1. Purpose

Teams adopting NTI-1 need to answer one question from an auditor or a customer's
security questionnaire: *which control does this satisfy, and what is the
evidence artefact?* This document maps NTI-1 requirements to three regimes:

- **EU AI Act, Article 12** — record-keeping for high-risk AI systems
- **SOC 2, CC6.1** — logical access controls
- **ISO/IEC 42001** — AI management system

The mapping is deliberately narrow. It covers only the controls where NTI-1 has a
concrete, verifiable artefact, and it states plainly what NTI-1 does not do.

## 2. What NTI-1 produces

| Artefact | Defined in | Property |
| --- | --- | --- |
| Append-only audit chain | NTI-1 §3.4, Pillar 4 | Tamper-evident: each event commits to its parent; editing any past event breaks verification |
| Merkle accumulator root | NTI-1 §3.4, §6 | Commits to a set; used for revocation state and for anchoring log completeness |
| Capability delegation | NTI-1 §3.6.1 | Signed grant of authority from an issuer to an agent, with caveats and validity window |
| Invocation record | NTI-1 §3.6 | Signed record binding an agent, an action, and a decision |
| Decision record | NTI-1 §3.4 | Allow/deny outcome, with reason, per evaluated action |
| Revocation proof | NTI-1 §6 | Inclusion/non-inclusion proof against the revocation accumulator |
| Compliance level | NTI-1 §4 | Declared profile (Level 1 Audit-Only, 2 Standard, 3 Enterprise) |

Note on hashing: the audit trail is an **append-only SHA-256 hash chain**, not a
Merkle tree (§3.4). The Merkle accumulator is used for the revocation registry
and as the completeness anchor for the log. Crosswalk entries below respect that
distinction, because the two provide different evidence.

## 3. EU AI Act, Article 12 — Record-keeping

Article 12 requires high-risk AI systems to keep automatically generated logs
over the system's lifetime, sufficient to identify situations that may result in
the system presenting a risk, and to trace the operation of the system. Annex
requirements reference logging of events, the reference database, input data, and
the identification of persons involved in verification.

| Requirement (paraphrase) | NTI-1 artefact | Evidence | Gap / owner action |
| --- | --- | --- | --- |
| Automatic generation of logs per event | §3.4 audit chain; every evaluated action MUST be recorded | Audit chain export; `T-4.1` shows chain length equals action count | Retention period is deployer policy; NTI-1 does not enforce a retention schedule |
| Traceability of system operation | §3.4 parent-hash linkage; §3.6 invocation records | Chain verification output; tamper test (`conformance/issue-18/tamper_detection.json`) | Log content completeness is implementation-specific |
| Identification of the actors involved | §3.1 principal-bound identity; §3.6.1 delegation | Delegation chain: issuer → subject, with DID identifiers | Mapping DID to a natural or legal person is out of scope for NTI-1 |
| Detection of risk situations | §3.4 decision records (allow/deny + reason) | Deny events with reason codes | Risk classification logic belongs to the deployer's risk-management system (Art. 9), not NTI-1 |
| Integrity and non-repudiation of logs | §3.4 hash chain; §6 completeness anchoring | Verification of chain + anchoring of accumulator root | NTI-1 does not itself provide trusted timestamping; pair with an external time source |
| Post-market monitoring feeds | §3.4 exportable trail; §3.5 persistence | Exported, verified trail | Art. 72 reporting workflow is organisational |

What this means in practice: NTI-1 supplies a tamper-evident, exportable,
per-action log with actor attribution. It does **not** supply retention policy,
natural-person mapping, risk classification, or a monitoring process. Those are
deployer obligations and must be documented separately.

## 4. SOC 2, CC6.1 — Logical access controls

CC6.1 concerns logical access security software and infrastructure: identifying
and authenticating users, authorising access, and restricting access to
information assets to authorised parties.

| Requirement (paraphrase) | NTI-1 artefact | Evidence | Gap / owner action |
| --- | --- | --- | --- |
| Identify and authenticate access | §3.1 principal-bound identity; §3.6.1 signed delegation | Delegation records with issuer and subject identifiers | Identity proofing of the issuer is organisational; NTI-1 binds keys to principals but does not vet them |
| Authorise access to assets | §3.6.1 capability grants; §5 `T-6.3` | Deny on out-of-scope action; capability list per agent | Asset inventory and data classification remain the organisation's |
| Restrict access to authorised parties | §3.6.1 caveats and path restrictions; §5 `T-6.2` | Deny on expired or not-yet-valid capability | — |
| Remove access when appropriate | §6 revocation; §5 `T-6.1` | Deny on revoked token; revocation proof | Revocation propagation latency must be documented per deployment |
| Fail closed on missing checks | §6.1 `incomplete_check` | Deny when a check cannot complete | — |
| Evidence for the audit period | §3.4 exportable chain | Export covering the audit window | NTI-1 does not enforce retention; the export must be captured and stored by the organisation |

What this means in practice: this is NTI-1's strongest mapping. Capability
delegation with validity windows, revocation, and fail-closed semantics map
directly onto access-control testing. The auditor will still ask for the policy
document, the access review, and the provisioning process — NTI-1 evidences
enforcement, not governance.

## 5. ISO/IEC 42001 — AI management system

ISO/IEC 42001 is a management-system standard. NTI-1 is a technical control set.
It can supply evidence *into* an AIMS, but it cannot satisfy a management-system
clause on its own, because those clauses require organisational process.

| AIMS theme | NTI-1 contribution | Evidence | Gap / owner action |
| --- | --- | --- | --- |
| Operational control of AI systems (cf. Annex A operational controls) | §3.2 governance pillar; §6.1 fail-closed runtime | Runtime deny events; policy evaluation records | The AI policy itself, its approval, and its review cycle are organisational |
| Defined roles and responsibilities | §3.2 threshold-signature governance | Voter records, threshold decisions | RACI, competence, and training records are organisational |
| Monitoring and measurement | §3.4 decision records; §5 testable requirements | Conformance run output (T-1.1 … T-6.3) | Choice of metrics and targets belongs to the AIMS |
| Internal audit evidence | §3.4 exportable trail; §6.2 resume receipts | Verified export, including halt/resume transitions | Audit programme and auditor independence are organisational |
| Incident and nonconformity handling | §6 runtime halt; §6.2 `resume_basis` | Halt event plus documented basis for resume | Root-cause analysis and corrective-action workflow are organisational |
| Documented information control | §3.5 persistence and export/import | Reproducible state export | Document control system is organisational |

What this means in practice: present NTI-1 as *technical evidence for* operational
controls, and be explicit in the AIMS documentation that the management-system
clauses are met by process, not by the tool.

## 6. Where the cryptography fits, and what it does not prove

NTI-1 specifies ML-DSA-87 (Dilithium5) signatures over canonical JSON (RFC 8785)
and SHA-256 for the audit chain and accumulator.

- Signature verification proves a holder of a private key authorised an artefact.
  It does **not** prove the key belongs to the claimed organisation.
- That binding comes from a **trust registry** publishing authoritative root keys
  and issuer-to-legal-identity mappings (§6). Operating a trust registry is a
  governance function, not a library function.
- **No auditor should accept an NTI-1 receipt as proof of issuer identity unless
  the verifying party is pinned to a trust registry they have independently
  validated.** A receipt whose chain is self-issued verifies cryptographically and
  proves nothing about authorisation. This is the single most important caveat in
  this document.

Post-quantum algorithms protect the *longevity* of this evidence against future
key-recovery. They do not add authentication strength against a present-day
attacker who already controls the issuing key.

## 7. Conformance levels and control coverage

| Level (§4) | Pillars | Useful for |
| --- | --- | --- |
| Level 1 — Audit-Only | 1, 4 | Logging and access evidence; explicitly not governance |
| Level 2 — Standard | 1–5 | Regulated environments needing decision + governance evidence |
| Level 3 — Enterprise | 1–5 + HSM | Adds HSM key custody, SOC 2 Type II, ISO 27001, availability SLA |

Level 1 MUST be labelled Audit-Only wherever it is claimed, so that the absence of
governance is explicit rather than implied (§4).

## 8. Reference implementation status

The reference implementation is [`ube-foundation`](https://pypi.org/project/ube-foundation/).
Framework wrappers (`crewai-nti`, `langchain-nti`, `autogen-nti`, `openhands-nti`)
adapt it to specific agent frameworks.

Adopters should verify which pillars a given wrapper actually enforces before
citing it as control evidence. Wrapper coverage is not implied by this document,
and a wrapper that enforces only a subset should be cited only for that subset.

## 9. How to use this document

1. Pick the control you are evidencing.
2. Use the "Evidence" column to identify the artefact to collect.
3. Read the "Gap / owner action" column and assign that work to a named owner.
4. State the NTI-1 version and compliance level in the evidence record.
5. Do not cite NTI-1 for controls where this table shows no artefact.

## 10. References

- NTI-1 specification: [NTI-1.md](./NTI-1.md)
- Testable requirements: NTI-1 §5
- Revocation and halt semantics: NTI-1 §6
- Release and versioning: [RELEASE.md](./RELEASE.md)
- LFDT lab proposal: [LF-Decentralized-Trust/lab-proposals#36](https://github.com/LF-Decentralized-Trust/lab-proposals/issues/36)

Official control sources are the authoritative text: Regulation (EU) 2024/1689
Article 12; AICPA Trust Services Criteria CC6.1; ISO/IEC 42001:2023.
