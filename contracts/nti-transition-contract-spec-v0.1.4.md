# NTI × LGD transition-contract spec — v0.1.4

Prepared by Xinghua Zhao, 2026-10-30. This note locks the three transition contracts for the NTI runtime-halt integration discussed on the agent-protocol thread, and states the registry split as a working proposal. Nothing here commits either side to code; it is the base text for the conformance test family.

**Revision note (v0.1.4, 2026-10-30):** adds §2.4 — the `resume_basis` field (evidence | exemption) and its two exemption boundaries — proposed on the agent-protocol thread in reply to the VOC justification-receipt discussion. v0.1.3 remains frozen; this file is the v0.1.4 release and carries its own fingerprint.

---

## 0. Status, versioning, licensing

**0.1 Status.** Draft for comment. Not agreed: neither side has accepted this text. Written objections are accepted from the date of circulation; cite the section number and the sentence objected to.

**0.2 Versioning and freeze.** Every circulation of this document is a release and is frozen. The full-text SHA-256 and a UTC timestamp are registered in a release record kept outside this file, so that the fingerprint does not have to contain itself. Any character change to a released version raises the minor version and is recorded as a diff summary in the change log. A copy without a registered fingerprint is not a release and may be edited by anyone.

**0.3 Effect of silence.** A circulated draft is treated as accepted for the purpose of the conformance test family if no written objection is received within 14 days of circulation. This is a working rule proposed by the LGD side for the two sides named here. It is not a procedure of any standards body and carries no weight outside this thread.

**0.4 Forking.** If a disagreement is not resolved within 30 days of circulation, either side may derive a further draft from the last release. A derived draft must carry a different document name and must state which release and fingerprint it derives from. Neither side may circulate a derived draft under this document's name.

**0.5 Licensing and name status.** Three layers are licensed separately, and the boundary is stated here so that no later reader has to guess:
| Layer | Scope | Licence |
|---|---|---|
| Normative text | Sections 1 through 6 of this document only | CC BY 4.0 |
| Theory text and methodology | all LGD theory text, method descriptions and framework naming, whether or not referenced here | all rights reserved |
| Reference implementation | the code repository cited in Section 5 | Apache-2.0 as code |

CC BY 4.0 applies to the normative text only, and only so that others may implement it and write conformance tests against it; attribution must name this document and its release fingerprint. It does not extend to the theory text, to the methodology, or to the implementation's code. Where a sentence in this document paraphrases theory text, the paraphrase is licensed and the underlying theory text is not.

"NTI", "LGD" and "SynomosAI" appear as source identifiers only: none is a registered legal entity in any jurisdiction and none carries a registered trademark. Identifier status was not verified against a trademark register for this revision; the statement is a disclaimer of claim, not a claim of status.

**0.6 Author and correspondence.** Xinghua Zhao, independent researcher, ORCID 0009-0001-0512-1237, zhaoxinghua07@126.com. Written objections under §0.3 and any markup of this draft go to that address, with the release fingerprint in the subject line — an objection that cannot be tied to a fingerprint cannot be tied to a version. Revisions from v0.1 are listed in the change log at the end.

**0.7 Related artefacts, cited with the version they resolve to today.** Concept DOI 10.5281/zenodo.22821834 (uibc-core) currently resolves to version 0.3.0 of 2026-09-28; the ORCID record for the author lists version 0.2.1 of 2026-09-18, so the two sources disagree on version and the DOI is the authoritative one. First public anchor of the reference material: 2026-09-17 13:31:45 UTC, commit `cb6f11b` as recorded by the author. **No external transparency-log anchor is claimed in this document.** If such an anchor is relied on, it must be generated at the time of reliance and cited with its own log index and log identity; a transparency-log index is never carried over from a prior draft, because it cannot be verified without the log's inclusion proof. A citation that names the concept DOI without stating which version it resolved to on the date of citation is a stale citation, not a pinned one.

*Verification note.* The commit hash above is the author's record. It was not re-verified against the hosting service at the time of this revision, because the network path from the drafting host to that service did not resolve. Treat it as unverified until a third party confirms it.

## 1. Vocabulary (unchanged — do not drift)

REGISTERED → GATE_PASSED → ACTIVE → ANOMALY → PAUSE → ROLLBACK → REVERIFY → RESUMED

DENIED is not a state on this line. It is a boundary response value (Section 1.1) and must not be used as a state name.

### 1.1 Boundary values (the five-value set) — OPEN-1

A boundary value answers: may a new call proceed? This document does not yet enumerate the set. **Until the five values are listed here, this section is not testable and conformance tests must not be written against it.** Values appearing in the surrounding artifacts — DENIED in this document and in the demo, GATE_PASSED and APPROVED in the demo's gate record — are decision and state names, not a boundary set. The set must be drawn from the CoreSpec gate decision record, which is the normative source for gate decisions, and agreed by both sides (OPEN-1).

Two layers stay distinct:
- Boundary values answer: may a new call proceed? Post-revocation new call → DENIED.
- Halt transitions answer: what happens to a chain already in flight? Mid-execution chain → PAUSE → ROLLBACK → (REVERIFY → RESUMED only if the restore condition is met).

### 1.2 Undefined terms — OPEN-2

"NTI" and "LGD" name the two sides throughout this document. Neither is defined here, and no definition is imported by reference. A reader outside both sides cannot determine the scope of either party's obligations until OPEN-2 closes.

---

## 2. The three transition contracts

### 2.1 PAUSE
- **Trigger:** a registered trigger — expiry, revocation, or anomaly signal.
- **Where:** only at the sidecar boundary, between atomic tool calls, never mid-call. The current call finishes; the sidecar intercepts the next planned execution payload, checks the registry, blocks, and issues a signed PAUSE receipt.
- **Receipt fields, tier 1 (normative now):** transition, trigger, checkpoint id, timestamp, monotonic counter.
- **Receipt fields, tier 2 (pending Section 4):** signing key id, signature. These are required fields of the final receipt format. They cannot be implemented until Section 4 closes (OPEN-5). A receipt carrying tier 1 only is a valid evidence artifact for Section 3, but it establishes no authenticity.
- **Timestamp:** must be attributable to a source outside the signing party, or bound to the checkpoint sequence so that the issuer cannot rewrite the order. OPEN-3: the source (an RFC 3161 time-stamp authority, or the registry root anchor) is not yet chosen. Until it is, the replay claim below does not hold.
- **Pinned inputs:** for a third party to replay the receipt, all five of the following must be pinned and published with it — registry root bytes and the time at which that root was current; checkpoint bytes; the receipt bytes; the verification key reference; the clock source used. "Pinned inputs" without these five is not a replay contract.
- **Property:** a third party must be able to replay the receipt from pinned inputs. No interpreter opinion opens a transition.

### 2.2 ROLLBACK
- **Target:** the last checkpoint.
- **Receipt fields:** as for PAUSE — tier 1 now, tier 2 pending Section 4. The evidence snapshot reference replaces the checkpoint id where the rollback crosses a change gate.
- **Property:** deterministic and replayable by a third party.
- **Failure rule (normative):** if the target checkpoint is unavailable or fails its integrity check, the chain stays in ROLLBACK and must not reach RESUMED. A failed rollback is a halt that no restore condition can clear; clearing it requires an out-of-band decision by the declared verifier role. Failure of a rollback never resolves in favour of resumption.

### 2.3 REVERIFY → RESUMED — not automatic
- **Gate:** a registered restore condition must arrive and verify in full: (a) an evidence list (e.g. re-benchmark + release note), (b) a verifier role, (c) a validity window.
- **Missing any item:** the chain stays PAUSED and returns a structured receipt naming what is absent — a DENIED that names the gap, not a terminal state.
- **Window expiry:** if the validity window closes before (a) and (b) verify, the chain stays PAUSED. It does not degrade to RESUMED by default and does not become terminal; the receipt records window closure as the reason. OPEN-4: whether a closed window escalates to the next authority is not specified here.
- **Recurrence:** RESUMED is not a privileged end state. A second registered trigger at any later boundary sends the chain back to PAUSE, and the same three contracts apply again, without carrying credit from the earlier resume. A halt that can fire only once is not a halt.
- **One-way-gate exception:** where the governing regime makes revocation irreversible, REVERIFY → RESUMED does not apply; that case must be declared, not assumed. eIDAS Art. 28(4) is the instance in scope: a revocation takes effect from the moment of revocation and the status "shall not in any circumstances be reverted". The exception is a property of the regime, not of this specification — the same article, Art. 28(5), lets Member States provide for temporary suspension, under which validity is lost for the suspension period and returns when it ends. Where a suspension mechanism exists, PAUSE ↔ RESUMED maps onto suspension rather than revocation and the one-way gate does not apply. Declare which of the two the regime provides before relying on either.
- **Citation status:** Regulation (EU) No 910/2014, Art. 28(4)-(5), consolidated text in force 20 May 2024 following amendment by Regulation (EU) 2024/1183. Wording was taken from a consolidated-text mirror on 2026-10-30; a direct retrieval of the EUR-Lex consolidated page returned a consent interstitial rather than the text, so the verbatim is not yet confirmed from the primary source. Recheck against EUR-Lex CELEX 02014R0910-20240520, and for any later amendment, before any reliance. This limitation is recorded rather than papered over: an unconfirmed verbatim is not a citation.

### 2.4 RESUME receipt — the `resume_basis` field (proposed in v0.1.4)
- **Field:** `resume_basis = evidence | exemption`.
  - `evidence` — the registered restore condition was verified in full (evidence list, verifier role, validity window): the condition that caused the halt was confirmed restored.
  - `exemption` — an accountability layer accepted the risk; the reason is recorded, **not evaluated**. Both values permit RESUMED.
- **No state change.** The field is added to the RESUME receipt only. It does not add, remove, or rename a state; the transition line of §1 is unchanged.
- **Why a closed set, not free text.** A reason string is hash-chained (not altered) but not aggregable; an auditor cannot separate "restored on evidence" from "resumed on exemption" at the volume this is meant for. A closed-set value is countable, alertable, and recomputable by a third party who does not trust the filer.
- **Two boundaries (must be in the schema):**
  - `exemption_covers = policy_violation`
  - `exemption_does_not_cover = authority_revoked, authority_not_determined`
  - `authority_revoked` is the issuing authority's decision, not the executing side's; a signed justification cannot un-revoke it.
  - `authority_not_determined` is an absence of information (registry unreachable / stale root), not a judgment; a signature cannot convert "unknown" into "known". This is the fail-closed property asserted on 2026-10-29; an exemption must not buy it back.
- **Key sentence.** Because the protocol does not evaluate the opinion, it has to record that it did not — otherwise the absence of evaluation is invisible, and invisible is where an auditor's question goes to die.

---

## 3. Registry split (working proposal)
- **Merkle revocation registry (NTI side):** the trigger source — "why halt now".
- **Evidence registry (LGD side):** the restore source — "what must verify before resume".
- The gate predicate reads both, as separate inputs, and must not collapse them into one registry.
- **Precedence (normative):** at any boundary, a present trigger outranks a present restore. The gate halts, and the restore is not evaluated until the trigger is cleared. There is no state in which a restore condition overrides a live trigger.
- **Root versioning:** the Merkle root is an input, not a constant. A receipt must name the root it was decided against, and that root must be published with a time anchor. A halt decided against one root cannot be replayed against another.
- **Working proposal:** proceed on this split. The long-running call test of 29 October already runs on it, with the Merkle root as trigger. This section is the place to mark up a different reading of the split.

---

## 4. Signature layer (NTI side, to confirm — not claimed here)
- **Proposal.** The NTI-side signature layer, as proposed by the NTI side on the agent-protocol thread, wraps the receipts so that every PAUSE and ROLLBACK is independently auditable. This note records it as a proposal, not as a verified property.
- **Algorithm naming.** The thread refers to "Dilithium5". That name is pre-standardization. The standardized algorithm is ML-DSA, FIPS 204 (final, 2024-08-13), in three security levels; the highest level is ML-DSA-87. This document therefore writes ML-DSA-87 (FIPS 204) and records the historical name once. Naming verified 2026-10-30 against RFC 9881, which states that "prior to standardization, ML-DSA was known as Dilithium". The equivalence Dilithium5 = ML-DSA-87 is an inference from the round-3 submission's parameter sets, stated in implementation documentation and secondary sources; FIPS 204 itself does not use the Dilithium names, so the equivalence is recorded as an inference and not as a quotation.
- **Encoding, not name.** FIPS 204 changed things that reach the bytes: deterministic signing becomes the default, an optional context string is added to signing and verification, pre-hash mode is formalised, and serialisation is specified more precisely. Sources disagree on how far that breaks byte-level compatibility with the round-3 submission — some state that keys and signatures from one cannot be verified by the other, others state that the core signing bytes match where randomised signing and context strings are not used. Because the sources conflict (OPEN-7), this document asserts neither. It asserts the operative rule only: a receipt encoding must be fixed to FIPS 204 explicitly, and no receipt may be specified against a round-3 Dilithium byte layout.
- **Edition and errata.** The edition relied on here is FIPS 204 as published on 2024-08-13 (DOI 10.6028/NIST.FIPS.204). NIST carries a planning note dated 2026-07-31 listing minor issues to be corrected in a future update or revision of that publication. Any receipt format that fixes a byte-level encoding must therefore pin the FIPS 204 edition it was built against, and recheck that note before claiming long-term stability.
- **Identifiers.** If receipts are carried in X.509 or CMS: X.509 algorithm identifiers are specified in RFC 9881 (Proposed Standard, October 2025, DOI 10.17487/RFC9881), CMS in RFC 9882, JOSE and COSE in RFC 9964. A receipt must carry the standardized identifier, never a pre-standardization OID.
- **Claim boundary.** The properties asserted here are technical: independently verifiable, tamper-evident, third-party replayable. This document asserts no legal conclusion. Where a receipt is relied on as evidence, what it supports is the integrity and authenticity prerequisites of the applicable evidentiary rules of the forum in question; whether those prerequisites are sufficient is for that forum to decide. This document does not assert admissibility in any jurisdiction.
- **Open (OPEN-5).** Signature format, key management, which receipts carry which key, and rotation and revocation of the signing keys themselves are to be specified by the NTI side before any wrap is built.

---

## 5. Reference implementation (already runnable, unchanged)
LGD-MedAI Demo v0.1 — https://github.com/zhaoxinghua09-cell/lgd-medai-demo
- **Pinned revision (file-level, not repository-level):** the demonstration artefact is `lgd_medai_demo.py` as committed in `038a4eb` (2026-09-26, the v0.1 release commit). That file has not changed since. The repository itself has moved — HEAD at the time of writing is `6cdd0ab` (2026-10-05, CI only) — so pinning the repository would have made "unchanged" false within a week. "Unchanged" in this section means unchanged for that file.
- **Acceptance criterion source:** the README at `038a4eb` printed the pause tag as `PAUSED`; a later commit (`566c540`, 2026-09-27) corrected it to `PAUSE`, which is what the program actually emits. The criterion used here is the corrected one. Anyone reading the README at the pinned commit will see the stale tag, so the criterion is stated here rather than left to that file.
- **Run:** one command, zero dependencies, Python 3.10+ — `python lgd_medai_demo.py`. Acceptance: `final_state = RESUMED` and the log containing the tags DENIED / PAUSE / ROLLBACK / RESUMED.
- It demonstrates the full chain end to end, including the kill-and-recover path. No change to the demo is proposed in this note.
- **Scope.** The scenario is fictional, contains no patient data, and is not clinical or production evidence. It demonstrates the mechanism, not the safety of any deployed system.
- **Known divergence, already disclosed by the repository README.** In the demo, DENIED is implemented as a transient state reached by direct re-registration, bypassing the state machine. The normative semantics of DENIED are those of Sections 1 and 2 of this document. Where demo and document differ, this document governs and the demo is the simplification.
- **Vocabulary drift already present in the artefact.** `failure_rules.json` in the same repository composes gate actions as `PAUSE + REVERIFY + ROLLBACK`, `PAUSE + ESCALATE(manual review)` and `PAUSE + ROLLBACK(to last valid version)`. `ESCALATE` does not appear in the vocabulary of Section 1. The instruction "do not drift" therefore already fails against the reference material, and Section 1 cannot claim to be closed while a verb in active use is missing from it (OPEN-6).
- **Licensing.** The demo's code is Apache-2.0. The LGD theory text and methodology it embodies are not covered by that licence.

---

## 6. Open items
| ID | Unresolved | Closes on | Blocks |
|---|---|---|---|
| OPEN-1 | Enumeration of the five boundary values | LGD + NTI, joint table | Section 1.1 untestable |
| OPEN-2 | Definitions of "NTI" and "LGD" | Each side, own text | Outside reader cannot scope obligations |
| OPEN-3 | Timestamp source (RFC 3161 or root anchor) | NTI + LGD | The replay claim in Section 2.1 |
| OPEN-4 | Whether a closed validity window escalates | LGD | The REVERIFY test cases' terminal branch |
| OPEN-5 | Signature format, key management, rotation | NTI | Tier-2 receipt fields; authenticity claims |
| OPEN-6 | `ESCALATE` verb absent from Section 1 | LGD, then NTI | The "do not drift" claim; test family |
| OPEN-7 | FIPS 204 vs round-3 Dilithium byte-compatibility | NTI | Section 4 wording; migration statements |

No item on this list is closed by silence. Section 0.3 applies to objections to the text, not to these five.

---

## 7. References
| Cited in | Object | Link |
|---|---|---|
| §4 | FIPS 204, ML-DSA (final, 2024-08-13) | https://doi.org/10.6028/NIST.FIPS.204 |
| §4 | FIPS 204 planning note / errata list | https://csrc.nist.gov/pubs/fips/204/final |
| §4 | RFC 9881, X.509 identifiers for ML-DSA | https://www.rfc-editor.org/info/rfc9881 |
| §4 | RFC 9882, ML-DSA in CMS | https://www.rfc-editor.org/info/rfc9882 |
| §4 | RFC 9964, ML-DSA for JOSE and COSE | https://www.rfc-editor.org/info/rfc9964 |
| §2.3 | Regulation (EU) No 910/2014, Art. 28 | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02014R0910-20240520 |
| §5 | Reference implementation repository | https://github.com/zhaoxinghua09-cell/lgd-medai-demo |

---

## Change log

**v0.1 → v0.1.1** (2026-10-30)
1. Added Section 0 — status, freeze rule, effect of silence, forking, licensing and name status, author identity.
2. Section 1 — stated that DENIED is a boundary response value, not a state.
3. Section 1.1 — the five-value set is now declared OPEN-1 instead of being referenced as if enumerated.
4. Added Section 1.2 — NTI and LGD are undefined terms (OPEN-2).
5. Section 2.1 — receipt fields split into tier 1 (normative) and tier 2 (pending Section 4); added timestamp attribution requirement and the five-item definition of pinned inputs.
6. Section 2.2 — added the rollback failure rule (closed failure, never resumption) and the change-gate variant of the evidence reference.
7. Section 2.3 — added window-expiry behaviour and the recurrence rule (RESUMED is not privileged); added the Art. 28(5) counter-case and a version statement for the eIDAS citation.
8. Section 3 — added trigger-over-restore precedence and Merkle root versioning; removed second-person address; kept the working proposal unchanged in substance.
9. Section 4 — Dilithium5 replaced by ML-DSA-87 (FIPS 204) with the historical name recorded once; added identifier references; separated technical properties from legal conclusions.
10. Section 5 — pinned the revision to a commit; added the fictional-scope statement, the disclosed DENIED divergence, Python and dependency floor, and the licensing split.
11. Added Section 6 — open items with owners and blocked scope.

**v0.1.1 → v0.1.2** (2026-10-30, same day; driven by the pre-publish review)
12. Section 0.7 added — related artefacts with the versions they resolve to, including the discrepancy between the concept DOI (v0.3.0) and the ORCID listing (v0.2.1).
13. Section 2.3 — citation status downgraded from "verified" to "verbatim from a mirror, primary source not yet retrieved"; the limitation is stated in the text rather than only in the review file.
14. Section 4 — added the FIPS 204 edition and errata note (planning note dated 2026-07-31); byte-level encodings must pin the edition. Separated the Dilithium5 = ML-DSA-87 equivalence (an inference) from the quoted naming statement, and replaced the wire-compatibility assertion with the operative encoding rule, because the sources conflict (OPEN-7).
15. Section 5 — repository pin replaced by a file-level pin (`lgd_medai_demo.py` at `038a4eb`), because the repository moved to `6cdd0ab` within nine days and would have falsified "unchanged"; acceptance criterion now states its own source (`566c540`) because the README at the pinned commit still prints the stale `PAUSED` tag.
16. Section 5 — recorded the vocabulary drift already present in `failure_rules.json` (`ESCALATE`), which falsifies the "do not drift" instruction in Section 1 until OPEN-6 closes.
17. Section 6 — added OPEN-6 and OPEN-7.
18. Section 7 — added a references table so that every cited object has a credential-free link adjacent to it; this closes the "cited but not reachable" gap found by reading the text backwards rather than checking a list I had written myself.
19. v0.1.3 — removed a fabricated transparency-log anchor from §0.7. The earlier text carried a Sigstore Rekor log index that was never obtained by querying a log; a machine gate flagged it. It is replaced with an explicit statement that no log anchor is claimed, plus the rule that a log index is never carried over between drafts. Separately: the commit hash in §0.7 is marked unverified because the drafting host could not reach the hosting service.
20. v0.1.3 — §0.5 rewritten as a three-layer licence table with an explicit boundary, because the previous single paragraph left the split between normative text and theory text to inference. §0.6 now carries a correspondence address, without which the §0.3 objection procedure had no destination and was not operable.

**v0.1.3 → v0.1.4** (2026-10-30)
21. Added §2.4 — the `resume_basis` field (evidence | exemption) and the two exemption boundaries (`exemption_covers = policy_violation`; `exemption_does_not_cover = authority_revoked, authority_not_determined`), proposed on the agent-protocol thread in reply to the VOC justification-receipt discussion. Marked as proposed, not agreed; no fingerprint until circulated. No state is added, removed, or renamed; the §1 transition line is unchanged. This closes the version-drift gap between the email sent that day and the frozen v0.1.3 text.
