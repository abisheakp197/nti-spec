# LF Pre-Flight Audit — nti-spec

**Role:** LFDT TAC Auditor & Principal Security Engineer
**Scope:** Pre-submission hardening of `abisheakp197/nti-spec` and
`abisheakp197/Neutral-Trust-Infrastructure` for the Linux Foundation Decentralized
Trust (LFDT) Lab application.
**Date:** 2026-11-10
**Status:** Remediated on branch `fix/pre-flight-audit-final`

---

## 1. Summary

This audit covers licensing, governance, DCO, link integrity, README completeness,
internal contradictions, security posture, branch protection, and OpenSSF Scorecard
gaps across both repositories. Every actionable finding has been remediated on the
`fix/pre-flight-audit-final` branch in each repository. Items that require
repository-owner action (branch protection, Scorecard maintenance) are listed in
Section 6.

## 2. Supply-chain hardening

### 2.1 GitHub Actions pinned to commit SHAs

Every third-party action in this repository is now pinned to a full 40-character
commit SHA with a trailing `# <version>` comment. Floating tags (`@v4`, `@v5`,
`@v3`) were replaced. This satisfies the OpenSSF Scorecard `Pinned-Dependencies`
check and the LFDT supply-chain expectations.

All pinned SHAs were verified to resolve to a real commit on their upstream
repository, and each trailing version comment was checked against the upstream tag
at that SHA.

| Action | Pinned ref |
| :--- | :--- |
| `actions/checkout` | `11d5960a…` (v4) |
| `actions/setup-python` | `a26af69b…` (v5) |
| `actions/setup-node` | `49933ea5…` (v4) |
| `actions/upload-artifact` | `ea165f8d…` (v4) |
| `actions/configure-pages` | `1f0c5cde…` (v4) |
| `actions/jekyll-build-pages` | `44a6e6be…` (v1) |
| `actions/upload-pages-artifact` | `56afc609…` (v3) |
| `actions/deploy-pages` | `d6db9016…` (v4) |
| `Swatinem/rust-cache` | `d1527c8f…` (v2) |
| `tim-actions/get-pr-commits` | `198af035…` (v1.3.1) |
| `tim-actions/dco` | `f2279e6e…` (v1.1.0) |
| `abisheakp197/nti-scan-action` | `6591bbe4…` (v1.0.0) |
| `ossf/scorecard-action` | `fa7117db…` (v2.5.0) |
| `actions/checkout` (scorecard) | `3d3c42e5…` (v7.0.1) |
| `actions/upload-artifact` (scorecard) | `cf430e03…` (v7.0.2) |
| `github/codeql-action/upload-sarif` | `24c54180…` (v4.38.3) |

### 2.2 Tool installs pinned

CI installs that previously used floating versions now pin exact versions:
`markdownlint-cli@0.50.0` and `requests==2.32.3`.

### 2.3 Dependabot

`.github/dependabot.yml` was added. This repository has no runtime dependency
manifests (only CI tooling), so Dependabot is scoped to the `github-actions`
ecosystem to keep the pinned SHAs current. This addresses the Scorecard
`Dependency-Update-Tool` check.

## 3. Governance and licensing

This repository previously lacked several governance files that its own
`CONTRIBUTING.md` referenced. They were added:

| Item | Status |
| :--- | :--- |
| `LICENSE-SPEC` (Community Specification License 1.0) | Present |
| `NOTICE` | Added; records CSL for the spec and Apache-2.0 for the reference implementation |
| `CODE_OF_CONDUCT.md` | Added; byte-identical to the core repository copy |
| `CONTRIBUTING.md` | Added; DCO-based, no CLA, CSL for specification text |
| `GOVERNANCE.md` | Added; TSC + rough-consensus model, kept in sync with core |
| `MAINTAINERS.md` | Added; maintainer list and LFDT diversity commitment |
| `SECURITY.md` | Present |
| DCO workflow (`.github/workflows/dco.yml`) | **Added — see Section 5** |

**Licensing:** `LICENSE-SPEC` is the Community Specification License 1.0. GitHub
reports its SPDX as `NOASSERTION`, which is expected: CSL is not an SPDX-recognized
identifier. The CSL text itself is licensed CC BY 4.0 by the Joint Development
Foundation; that attribution is required and is recorded in `NOTICE`. This is an
attribution requirement on the license text, not a re-licensing of the NTI-1
specification, which remains under CSL 1.0.

## 4. Documentation and link integrity

* The link checker (`scripts/check_links.py`) was strengthened to validate
  **relative** links against the local tree, not just external URLs. A renamed or
  deleted file can no longer silently break a document. The check now covers 31
  links (previously 10 external-only).
* `README.md` now links `CONTRIBUTING.md`, `MAINTAINERS.md`, `GOVERNANCE.md`,
  `RELEASE.md`, `ADOPTERS.md`, and `LFDT-PROPOSAL.md`.
* The conformance validator and the Markdown linter both pass locally.

## 5. Internal contradictions resolved

* **Missing DCO enforcement (contradiction).** `CONTRIBUTING.md` states that "Pull
  requests whose commits lack a sign-off will fail the `DCO` check and cannot be
  merged," but this repository had **no DCO workflow**. A `.github/workflows/dco.yml`
  was added (identical to the core repository's, using the same pinned SHAs), so the
  documented behaviour now matches the enforced behaviour.
* **Stale audit claim.** `AUDIT_REPORT.md` described a crates.io link as "pending
  removal/replacement" although the link had already been removed. The report now
  states the accurate, completed status.
* `.github/workflows/pages.yml` was missing a trailing newline; corrected.

## 6. Findings requiring repository-owner action

These cannot be changed through a pull request; they are repository settings.

1. **Branch protection (Scorecard `Branch-Protection`, currently 0/10).** Enable
   branch protection on `main`: require a pull request, require at least one
   approving review, require status checks to pass (the DCO check and CI), and
   disallow force-pushes and deletions.
2. **Scorecard `Code-Review`, `Maintained`, `CII-Best-Practices`, `Fuzzing`,
   `Contributors` (all 0).** These are process checks that improve over time as the
   project gains reviewers, releases, and a fuzzing harness; they are not blockers
   for the Lab application but should be tracked.
3. **Scorecard publication.** The Scorecard workflow was added; its first run on
   `main` after merge will publish the repository's score and populate the README
   badge.
4. **Repository topic / description.** Consider adding a description and topics to
   improve discoverability; not a Lab blocker.

## 7. Verification performed

* YAML parse of every workflow and `dependabot.yml` — pass.
* All pinned action SHAs resolve to real upstream commits — pass.
* Version comments checked against upstream tags — pass.
* Markdown linter (`markdownlint-cli@0.50.0`) — pass.
* Link checker (external + relative) — 31 links, all pass or time out gracefully.
* Conformance validator — pass.
* DCO trailer check across non-merge commits — pass.
