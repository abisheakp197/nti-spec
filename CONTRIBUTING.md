# Contributing to the NTI-1 Specification

We welcome community contributions to the NTI-1 specification, its conformance
vectors, and its RFC process. Please read this guide before getting started.

---

## 0. Developer Certificate of Origin (DCO) — Required

**All commits MUST be signed off using `git commit -s` to comply with the
Developer Certificate of Origin (DCO).**

Every commit in a pull request must contain a `Signed-off-by:` line with your real
name and email address, matching the commit author. The DCO is a lightweight
statement that you have the right to submit the contribution under the project's
open-source license. The full text is at <https://developercertificate.org/>.

Add the sign-off automatically:

```bash
git commit -s -m "your commit message"
```

This appends a line such as:

```text
Signed-off-by: Jane Doe <jane.doe@example.com>
```

If you forgot, amend the commit and force-push your branch:

```bash
git commit --amend -s
git push --force-with-lease
```

Pull requests whose commits lack a sign-off will fail the `DCO` check and cannot
be merged.

---

## 1. Licensing: DCO for Code, CSL for the Specification

**Code and tooling contributions use the Developer Certificate of Origin (DCO)
exclusively; no separate CLA is required for code. All commits must be signed off
using `git commit -s`.**

By signing off, you certify that you wrote the contribution or otherwise have the
right to submit it under the project's license (Community Specification License
1.0 for the specification text and conformance vectors, Apache-2.0 for tooling
code). You retain your copyright; there is no copyright-assignment or relicensing
agreement to sign for code contributions.

Specification contributions are made under the Community Specification License
1.0 (CSL) framework, which includes the Community Specification Contributor
License Agreement. See [LICENSE-SPEC](LICENSE-SPEC) for the full text.

There is no CLA bot and no CLA check to pass. The only contributor-agreement
requirement is the DCO sign-off described in section 0.

---

## 2. How to Submit a Contribution

1. **Find or Open an Issue:** Check existing issues before starting major work.
2. **Fork and Branch:** Create a feature branch off of `main`.
3. **Run the Checks Locally:** Ensure the markdown linter, the link checker, and
   the conformance validator all pass before submitting.
4. **Submit a Pull Request:** Open a PR targeting the `main` branch with a clear
   title and description of your changes.
5. **Sign Off Your Commits:** Use `git commit -s` so each commit carries a DCO
   `Signed-off-by:` line (see section 0).

---

## 3. Contribution Standards

* **Keep PRs Scoped:** Submit small, focused PRs that solve a single problem.
* **Preserve Normative Meaning:** A change to normative text (MUST / SHOULD) is a
  protocol change. State the rationale and, where behaviour changes, update the
  conformance vectors in the same pull request.
* **Do Not Weaken Disclosures:** The status notes at the top of `README.md` and
  `NTI-1.md` describe this document as a draft proposal. Do not remove or soften
  them.
* **Local Checks:** Before opening a PR, run:

  ```bash
  npx markdownlint-cli "*.md" "**/*.md"
  python3 scripts/check_links.py
  python3 conformance/validate.py
  ```

---

## 4. RFC Process

Substantive amendments to the specification are proposed as RFCs in the
[`rfcs/`](rfcs/) folder. Open an issue first to discuss scope, then submit the RFC
as a pull request.
