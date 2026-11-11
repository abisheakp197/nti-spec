# LFDT Lab Proposal: Neutral Trust Infrastructure (NTI)

**Status:** Draft Lab Proposal, prepared for submission to LF Decentralized Trust (LFDT) Labs.

**How to submit:** LFDT Labs accepts proposals as a GitHub issue using the official
**Lab Proposal** form, at
<https://github.com/LF-Decentralized-Trust/lab-proposals/issues/new?template=lab-proposal.yml>.
Filing that form is the entire submission. This document is the source text for each
field of that form, so the submission can be produced by copy-and-paste. There is no
TAC vote and no endorsement requirement for a lab; proposals are reviewed by the LFDT
lab stewards for whether the work is **cogent** and **novel**.

**Corrected in this revision.** An earlier version of this file described a "Lab"
track that "requires no endorsements and no TAC vote" and that entered directly as a
lab without passing through the LFDT project lifecycle. That framing was wrong on one
point: LFDT's own lifecycle document states that *every* project accepted by LFDT —
explicitly including **LFDT Labs projects** — enters the lifecycle through the
**Incubation** state and is subject to the TAC's entry criteria. A lab is the
on-ramp; it is not a bypass around those criteria. This revision states the correct
relationship and records the gaps that remain (see [LFDT-READINESS.md](LFDT-READINESS.md)).

---

## Section 1: Mission and Scope

### Lab Name

Proposed name: **Neutral Trust Infrastructure**.

> Per the LFDT Naming Guidelines, a lab cannot be named after a product, a network,
> or an existing entity, and needs its own distinct identity. "Neutral Trust
> Infrastructure" is a descriptive name, not a product or vendor name. It should be
> checked against the LFDT trademark-counsel review; alternate candidate names are
> listed under *Additional Information* in case counsel requires a change.

### Short Description

A post-quantum, custody-free runtime enforcement layer that verifies, at invocation
time, that a specific action by a specific AI agent was authorized.

### Scope of Lab

NTI provides the runtime enforcement point for autonomous agents. Existing work
answers adjacent questions well — identity issuance, credential formats, and evidence
packaging — but none provides a runtime check that cryptographically binds an agent's
authorization to the *specific action* it is attempting, in a form the resource being
acted upon can verify without trusting the agent.

The lab will host and steward:

- the **NTI-1 specification** and its RFC amendment process;
- a **reference implementation** (Rust core with Python bindings) that produces NTI
  receipts and conformance vectors;
- **conformance vectors** that any independent implementation can run against.

The lab does not issue certifications, does not speak for any other project, and
does not define a competing format where an adjacent project already defines one. It
adopts existing identifiers and formats and composes with them.

**Origin and history.** NTI grew out of published authority-conformance work. The
authority-conformance layer defines and tests what a valid delegation is; NTI is the
runtime enforcement point that checks such a delegation when an agent acts. NTI
references that work and claims no formal relationship with it.

### Alignment with LFDT Mission

LFDT's mission is to build a neutral, vendor-neutral home for decentralized trust
technology. NTI is squarely in that space: it is about verifiable authorization for
autonomous actors, using open, standardized cryptography (ML-DSA-87 per FIPS 204,
ML-KEM-1024 per FIPS 203). It is vendor-neutral by construction — the specification is
implementation-independent and the conformance vectors are public — and it is at the
early, pre-maturity stage that LFDT Labs exists to serve. LFDT is the right home
because the work needs a neutral steward so that no single vendor's implementation
defines the trust boundary.

### Relation to Existing LFDT Labs and Projects

NTI occupies a distinct layer and is designed to compose with adjacent work rather
than duplicate it:

- **Identity issuance** (for example, Hyperledger Identus, Hyperledger AnonCreds)
  answers *who is this agent and who vouches for it*. NTI consumes the resulting
  identifiers and keys; it does not issue them.
- **Evidence packaging and lifecycle governance** (a separate, adjacent layer) answers
  *what happened and how is it packaged for later review*. NTI produces the
  invocation-time receipt that such packages can carry; it does not define the
  package format.
- **Runtime enforcement** — NTI's layer — answers *was this specific action, by this
  agent, authorized at this moment*, and gives the resource a proof it can check.

NTI also interoperates with the **Agent-DID** approach: an NTI receipt binds an
ML-DSA-87 verification method that must be resolvable and authorized through the
agent's DID document (see `docs/NTI-Agent-DID-INTEROP.md`). NTI does not define its
own DID method.

---

## Section 2: Lab Details

### Technical Activity Type

- **Does this lab produce code?** Yes.
- **Does this lab produce a specification?** Yes.

The lab does both and keeps them separate: the reference implementation is licensed
under Apache 2.0 with DCO sign-off on all commits; the specification is licensed under
the Community Specification License 1.0 (CSL) and its framework.

### Pre-existing Repositories

```text
- https://github.com/abisheakp197/nti-spec
- https://github.com/abisheakp197/Neutral-Trust-Infrastructure
```

> **DCO note for repository transfer.** LFDT requires every commit in a transferred
> repository to carry a DCO `Signed-off-by:` line, and states that where existing
> history does not have it, the history must be squashed into a single signed-off
> commit for the new lab repository. The reference-implementation repository has
> already been squashed to a single signed-off initial commit for this reason. The
> specification repository's history is **not** fully signed off and would need the
> same treatment before transfer; this is tracked in [LFDT-READINESS.md](LFDT-READINESS.md).

### Initial Committers

```text
- https://github.com/abisheakp197
- https://github.com/aeoess
- https://github.com/zhaoxinghua09-cell
```

The initial committers are the project's three maintainers, listed in
[`MAINTAINERS.md`](MAINTAINERS.md): Abisheak P. (NTI), Tymofii Pidlisnyi
(Independent Researcher — Agent Passport System (APS)), and Steven Zhao,
Independent Researcher, who serves as an Initial TSC Member (Standards Capacity),
providing standards and specification governance rather than day-to-day code
maintenance. Committers act in their own capacity. No organization is
represented, and no single organization holds more than one seat.

### Sponsor

```text
Tymofii Pidlisnyi (tima@aeoess.com) - Agent Passport System (APS)
```

### Licensing

- [x] I understand that all code hosted in LFDT Labs must be made available under an
  Apache 2.0 license with DCO sign-off.
- [x] I understand that all specification and standards work in LFDT Labs is done
  under the Community Specification License 1.0 and the rest of the CSL framework.

Code contributions use the DCO exclusively; no separate CLA is required for code.
Specification contributions are made under the CSL framework, which includes the
Community Specification Contributor License Agreement. DCO enforcement is active via
GitHub Actions in both repositories.

### Governance Model or Practice

Governance is documented in [`GOVERNANCE.md`](GOVERNANCE.md) (decision making),
[`MAINTAINERS.md`](MAINTAINERS.md) (maintainers and scopes), and
[`CONTRIBUTING.md`](CONTRIBUTING.md) (contribution process and DCO). Decisions are
made by rough consensus of the maintainers, in public.

### Security

- Vulnerability disclosure policy: [`SECURITY.md`](SECURITY.md) in both repositories.
- Dependency scanning: Dependabot is enabled in both repositories.
- Release signing: the reference implementation signs release artifacts with Sigstore
  (keyless) and attaches SLSA build provenance; the process is documented in its
  [`RELEASE.md`](https://github.com/abisheakp197/Neutral-Trust-Infrastructure) (in the implementation repository).
- Static analysis: CodeQL runs on every pull request in both repositories.
- OpenSSF Scorecard is published for both repositories (badge on each README).
- OpenSSF Best Practices badge: applied for; see [LFDT-READINESS.md](LFDT-READINESS.md)
  for current status.

### Infrastructure and Tooling

GitHub Actions for CI (build, test, lint, link-check, conformance, CodeQL, Scorecard),
GitHub Pages for the documentation site, and PyPI Trusted Publishing for the reference
implementation's wheels. No anticipated needs beyond what is already in use.

### Evidence of Adoption and Use Cases

- The reference implementation publishes a signed **witness package** — a manifest of
  conformance results with the public key, the manifest, the signature, and the
  scripts to re-run the checks — at
  <https://abisheakp197.github.io/Neutral-Trust-Infrastructure/witness/>.
- The specification is an input contribution / Discussion Draft to the W3C Agent
  Protocol Community Group (public-agentprotocol). It is not a W3C deliverable and no
  organizational W3C endorsement is claimed.
- Independent researchers are conducting review and interoperability testing at
  defined boundaries. See [`ADOPTERS.md`](ADOPTERS.md).
- A public security assessment of NTI was published using the AACP (REMORA) framework
  by an independent assessor. It is referenced as presented by its maintainer,
  including its stated limitations, and is not claimed as formal independent
  validation.

### Roadmap

The 12-month roadmap (toward Graduated-status criteria) is in
[`docs/ROADMAP.md`](docs/ROADMAP.md). Near-term items include commissioning a formal
independent security audit, growing maintainer diversity to three or more
organizations, and completing the OpenSSF Best Practices badge application.

---

## Section 3: Existing Assets

### Existing Name and Logo

The name "Neutral Trust Infrastructure" is used for this work. No trademark is
registered on the name at this time. Any logo will be provided to LFDT on request.

### Website URL

Documentation sites: <https://abisheakp197.github.io/nti-spec/> and
<https://abisheakp197.github.io/Neutral-Trust-Infrastructure/>. No independent domain
is owned; no domain has been purchased (per the LFDT guidance against purchasing
domains before acceptance).

### Social Media Accounts

None at this time.

### Trademark and Accounts Signoff

- [x] If the lab is accepted, I agree to donate all related trademarks and accounts to
  the LFDT.

---

## Section 4: Contact Information

### Contact name(s) and email(s)

```text
Abisheak P. - abisheakp197@gmail.com
```

### Contributing or sponsoring entity signatory information

Provided at the time of asset transfer if the lab is accepted. There are no
organization-held assets to contribute at this stage.

### Additional Information

- **Name alternates.** If trademark counsel requires a different name, candidate
  alternates will be supplied at that time.
- **Incubating-project ambition.** NTI's intent is to mature toward an LFDT Incubation
  project; this lab proposal is the first step. LFDT staff guidance on the lab-to-project
  path is welcome.
- **Lifecycle acknowledgement.** We understand and accept that a lab enters the LFDT
  project lifecycle through Incubation and is subject to the TAC's entry criteria
  (Legal, Diversity, Security). [LFDT-READINESS.md](LFDT-READINESS.md) records our
  current status against those criteria.
- **Licensing.** Code is Apache 2.0 with DCO; specification is CSL 1.0. No alternative
  licenses are in use.
