# Adopters

This file records organizations and projects that implement, deploy, or build on the Neutral Trust Infrastructure (NTI) specification.

It follows the LF Decentralized Trust [Defining Adopters](https://lf-decentralized-trust.github.io/governance/governing-documents/defining-adopters/) guidance: an entry must point at publicly verifiable usage. A name without a working link is not evidence, and will be removed.

## What counts as an adopter

Any one of these, with a public link:

1. **Scan badge.** The repository runs [`nti-scan-action`](https://github.com/abisheakp197/nti-scan-action) in CI.
2. **Dependency.** The repository depends on `ube-foundation`, `langchain-nti`, `crewai-nti` or `autogen-nti`, or imports the reference core directly.
3. **Conformance run.** The repository runs a conformance suite against the vectors in [`conformance/`](./conformance) and publishes the result.

## How to add yourself

1. Fork this repository.
2. Add one row to the correct table below, using the row template.
3. Open a pull request titled `adopters: <your project or organization>`.
4. A maintainer checks that the link resolves and shows one of the three forms of usage above, then merges.

Self-declaration is enough. You do not need permission, a review, or a commercial relationship, and an individual is as eligible as an organization.

### Row template

```markdown
| **your-org** | Runs `nti-scan-action` in CI | [your-org/your-repo](https://github.com/your-org/your-repo) |
```

## Implementations

| Implementer | Role | Repository |
| :--- | :--- | :--- |
| **NTI reference implementation** | Rust core with Python bindings; produces NTI receipts and conformance vectors | [abisheakp197/Neutral-Trust-Infrastructure](https://github.com/abisheakp197/Neutral-Trust-Infrastructure) |

## Adopting projects and organizations

Projects and organizations outside the reference implementation that build on or deploy NTI-1.

| Adopter | Usage | Link |
| :--- | :--- | :--- |
| _none recorded yet_ | — | — |

This table being empty is the honest current state, and it is the number that matters most for this project. It is also the easiest one to change: the first row takes one pull request and one working link.

## Independent review

Review of NTI-1 at defined boundaries. An entry requires a named reviewer or a public artifact; an unattributed claim cannot be verified and is not counted.

| Reviewer | Scope | Public artifact |
| :--- | :--- | :--- |
| _none recorded yet_ | — | — |

The previously listed, unattributed "independent individual researcher" entry was removed. It named no reviewer and cited no artifact, so under the rule at the top of this file it was not an adopter record. If that review happened, re-add it with the reviewer's name or a link to the report and it will be listed immediately.
