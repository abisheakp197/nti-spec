# Release Process

This document describes how the Neutral Trust Infrastructure (NTI)
specification repository is versioned and published. It follows the LF
Decentralized Trust
[Securing and Verifying Releases](https://lf-decentralized-trust.github.io/governance/governing-documents/release-signing/)
policy.

## Versioning

The specification version is recorded in the [`VERSION`](VERSION) file and
mirrored in the document header of [`NTI-1.md`](NTI-1.md). Versions use
`MAJOR.MINOR.PATCH` with a `-draft` suffix while the specification is under
public review (for example `1.0.0-draft`).

- **MAJOR** — normative change that breaks existing conformant implementations.
- **MINOR** — additive normative change (new requirement, new profile).
- **PATCH** — editorial or clarifying change with no normative effect.

## What This Repository Releases

This repository produces no compiled binaries. Its deliverables are:

- The specification text (`NTI-1.md`), RFC amendments (`rfcs/`), and conformance
  vectors (`conformance/`).
- The published documentation site, served from the `main` branch via GitHub
  Pages at <https://abisheakp197.github.io/nti-spec/>.

Compiled artifacts (platform wheels) are produced by the reference
implementation repository,
[`abisheakp197/Neutral-Trust-Infrastructure`](https://github.com/abisheakp197/Neutral-Trust-Infrastructure).
Its `RELEASE.md` ([implementation repository](https://github.com/abisheakp197/Neutral-Trust-Infrastructure))
documents the build, Sigstore keyless signing, SLSA build provenance, and
verification steps for those artifacts.

## Publication Process

1. **Conformance** — a pull request must pass `ASL Conformance Harness`,
   `Markdown Lint, Link Checker & Conformance Validation`, DCO, CodeQL, and
   `security-scan` before merge.
2. **Merge** — merging to `main` triggers the `pages` workflow, which builds and
   deploys the documentation site with
   [`actions/deploy-pages`](https://github.com/actions/deploy-pages).
3. **Tag (optional)** — specification revisions are tagged `vMAJOR.MINOR.PATCH`
   on `main`. Tags are created by a maintainer; the repository does not store a
   signing key.

## Verifying a Specification Revision

Specification content is verified by reproducing the conformance run:

```bash
python3 scripts/check_links.py
python3 conformance/validate.py
```

The first command checks documentation links; the second validates the
conformance vectors against the normative requirements. Both run in CI on every
pull request.

## Resources

- Pages workflow: [`.github/workflows/pages.yml`](.github/workflows/pages.yml)
- Conformance harness: [`conformance/`](conformance/)
- Security policy: [SECURITY.md](SECURITY.md)
- Reference implementation release process: the `RELEASE.md` in
  <https://github.com/abisheakp197/Neutral-Trust-Infrastructure>
