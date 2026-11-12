# LFDT Readiness

This document tracks Neutral Trust Infrastructure (NTI) against the requirements
for submitting to **LF Decentralized Trust (LFDT) Labs** and for the subsequent
LFDT project lifecycle. It is written to be honest about what is done and what is
not, so a steward reviewing the proposal sees an accurate picture.

It is generated from live repository and OpenSSF Scorecard data. The values below
were captured on **2026-11-10**; re-check the Scorecard viewer links for current
scores, which move as checks re-run.

## 1. How submission works

LFDT Labs proposals are filed as a **GitHub issue** using the official Lab
Proposal form:

<https://github.com/LF-Decentralized-Trust/lab-proposals/issues/new?template=lab-proposal.yml>

Filing the form is the entire submission. A steward-review PR is opened
automatically. There is no TAC vote for a lab, but the proposal must be **cogent**
and **novel**, and there are hard licensing rules (Section 3 below).

The source text for every form field is in [`LFDT-PROPOSAL.md`](LFDT-PROPOSAL.md).

## 2. What a lab must satisfy at submission

Per the LFDT Lab Proposal guidance, the required items are:

| Requirement | Status |
| :--- | :--- |
| Code licensed **Apache 2.0** with DCO sign-off on all commits | See 2.1 |
| Specification licensed under **CSL 1.0** and the CSL framework | Met (see 3.2) |
| Every commit in a transferred repository carries a DCO `Signed-off-by:` | See 2.2 |
| A distinct lab name that is not a product/network/entity, cleared by trademark counsel | To confirm with LFDT |

### 2.1 Code licensing and DCO

The reference implementation (`Neutral-Trust-Infrastructure`) is Apache-2.0 and
enforces DCO via `.github/workflows/dco.yml`. This repository (`nti-spec`) is the
specification and is CSL-1.0.

### 2.2 DCO history (action required before repository transfer)

LFDT requires a DCO sign-off on every commit of a transferred repository, and
states that where existing history lacks it, the history must be **squashed into a
single signed-off commit** for the new lab repository.

- `Neutral-Trust-Infrastructure`: history is already squashed to a single signed-off
  initial commit. **Met.**
- `nti-spec`: history is **not** fully signed off. Before transfer, the history must
  be squashed into a single signed-off commit, as was done for the implementation
  repository. **Action required** (owner: maintainer).

This is a normal, expected step and does not block filing the proposal; it must be
completed during onboarding.

## 3. Licensing detail

### 3.1 Code — Apache 2.0

The reference implementation is Apache-2.0. GitHub license detection reports
`apache-2.0`. OpenSSF Scorecard `License` = **10/10**.

### 3.2 Specification — CSL 1.0

The specification is licensed under the Community Specification License 1.0, full
text in [`LICENSE-SPEC`](LICENSE-SPEC), with the required [`LICENSE`](LICENSE)
pointer at the repository root.

CSL 1.0 is not currently an SPDX-recognized license identifier, so GitHub license
detection reports this repository as "no license detected". OpenSSF Scorecard
`License` = **9/10** for that reason. This is an artifact of SPDX recognition, not
an absent license. CSL 1.0 is the license LFDT itself requires for specification
work, so this is expected and correct.

## 4. Security posture (live Scorecard)

OpenSSF Scorecard, captured 2026-11-10:

| Check | Implementation | Specification | Note |
| :--- | ---: | ---: | :--- |
| Dangerous-Workflow | 10 | 10 | Met |
| Token-Permissions | 10 | 10 | Met |
| Dependency-Update-Tool | 10 | 10 | Met (Dependabot) |
| SAST | 10 | 10 | Met (CodeQL) |
| Security-Policy | 10 | 10 | Met |
| Vulnerabilities | 10 | 10 | Met |
| CI-Tests | 10 | 10 | Met |
| Pinned-Dependencies | 7 | 8 | Pinned to SHAs; below 10 on residual items |
| **Branch-Protection** | **0** | **0** | **Action required — see 4.1** |
| **Signed-Releases** | **-1** | **-1** | No signed release published yet — see 4.2 |
| **Code-Review** | **0** | **0** | **Action required — see 4.1** |
| Fuzzing | 0 | 0 | Not yet started |
| CII-Best-Practices | 0 | 0 | Badge applied for; not yet registered |
| Overall | 6.4 | 6.4 | |

Viewer links:
<https://scorecard.dev/viewer/?uri=github.com/abisheakp197/Neutral-Trust-Infrastructure> ·
<https://scorecard.dev/viewer/?uri=github.com/abisheakp197/nti-spec>

### 4.1 Branch protection (action required — one manual step)

LFDT requires the Scorecard `Branch-Protection` check to reach **9 (Tier 4)**. Both
repositories currently score **0** because their rulesets are **defined but
disabled**.

A branch ruleset named **"NTI"** (implementation) and **"Spec"** (specification)
already exists on each repository and is currently `enabled: false`. Enabling it is
a one-click step in the GitHub UI:

`Settings → Rules → Rulesets → <NTI | Spec> → set Enforcement to "Active" → Save`.

The API token available to automation has **read-only** access to rulesets
(`403 Resource not accessible by integration`), so this step cannot be completed
programmatically and must be done by the repository owner.

**What to configure on the ruleset** (the existing ruleset already contains most of
this; confirm each item):

- Target: default branch (`main`).
- Rules: *Restrict deletions*, *Block force pushes*.
- *Require a pull request before merging*: 2 approvals, dismiss stale reviews,
  require review from Code Owners, require approval of the most recent review.
- *Require status checks to pass*: strict (branches up to date), with the required
  checks listed in 4.1.1.
- **Bypass list must be empty.** Scorecard treats any bypass actor as
  `EnforceAdmins = false`, which caps the score at 8. The existing ruleset has a
  `RepositoryRole: admin` bypass with `bypass_mode: always`; that entry must be
  removed (set bypass to *"None"*) to reach 9.

#### 4.1.1 Required status checks

Implementation (`Neutral-Trust-Infrastructure`):

```text
Developer Certificate of Origin
security-scan
CodeQL
Analyze (actions)
Analyze (python)
Analyze (rust)
```

Specification (`nti-spec`):

```text
Developer Certificate of Origin
security-scan
CodeQL
Analyze (actions)
Analyze (python)
Analyze (rust)
ASL Conformance Harness
Markdown Lint, Link Checker & Conformance Validation
```

> Note on two approvals: with a single maintainer, a 2-approval requirement means
> the maintainer cannot self-merge and must rely on a second reviewer or the
> bypass list. Removing the bypass list (required for score 9) and keeping two
> approvals will therefore require a second approver for every change. If that is
> not yet workable, a single approval is the practical interim setting; it still
> enables review and scores below 9 until a second reviewer exists.

### 4.2 Signed releases (action required — partially in place)

The reference implementation now has a Sigstore keyless signing job
(`release-signing` in `.github/workflows/release.yml`) that signs `SHA256SUMS.txt`
and attaches SLSA build provenance. `Signed-Releases` stays at **-1** until the
next release is published with those assets. The process and verification steps are
documented in the implementation's `RELEASE.md`.

The specification repository produces no binaries, so it does not sign releases.

### 4.3 Release documentation

Both repositories now have a `RELEASE.md` documenting the build, signing, and
verification process, as LFDT's release-signing policy requires.

## 5. Repository structure compliance

Per LFDT's Common Repository Structure:

| Required file | Implementation | Specification |
| :--- | :---: | :---: |
| `LICENSE` | Yes | Yes (pointer to `LICENSE-SPEC`) |
| `CODE_OF_CONDUCT.md` | Yes | Yes |
| `SECURITY.md` | Yes | Yes |
| `README` | Yes | Yes |
| `MAINTAINERS.md` | Yes | Yes |
| `CONTRIBUTING` | Yes | Yes |
| CI/CD configuration | Yes | Yes |
| `RELEASE.md` (release-signing policy) | Yes | Yes |
| `ADOPTERS.md` (recommended) | Yes | Yes |
| README badges (License, Best Practices, Scorecard) | Yes | Yes |
| `NOTICE` (recommended) | Yes | Yes |

## 6. Diversity

LFDT expects multiple maintainers and, for Incubation, maintainers from **two or
more organizations**. NTI has four maintainers: Abisheak P. (NTI), Tymofii
Pidlisnyi (APS), Steven Zhao (Independent), and Larry Lewis (personal capacity;
W3C ATP CG Chair as a separate affiliation). This satisfies the LFDT Incubation
requirement of ≥2 maintaining organizations. Growing the maintainer base further
is on the [roadmap](docs/ROADMAP.md). This does not block filing a lab proposal,
but it is a gate for Incubation, so it is stated plainly here.

## 7. Summary — what to do before submitting

1. **Submit the Lab Proposal issue** — copy the fields from
   [`LFDT-PROPOSAL.md`](LFDT-PROPOSAL.md) into the official form.
2. **Enable the branch-protection ruleset** on both repositories, with an empty
   bypass list (Section 4.1). This is the single largest score gap.
3. **Publish a signed release** of the reference implementation to turn on
   `Signed-Releases` (Section 4.2).
4. **Register the OpenSSF Best Practices badge** for both repositories.
5. **Squash the `nti-spec` history** into a single DCO-signed commit before
   repository transfer (Section 2.2).

Items 1 is the submission. Items 2–5 can proceed in parallel and are expected to be
completed during onboarding.
