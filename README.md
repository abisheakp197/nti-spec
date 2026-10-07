# NTI-1 Specification

**Neutral Trust Infrastructure — Standard 1**

The NTI-1 specification defines the requirements for post-quantum, zero-trust
governance of autonomous AI agents. It is the reference standard for
NTI-1 compliance.

## Read the Specification

→ [NTI-1.md](./NTI-1.md)

## What NTI-1 Defines

NTI-1 specifies the 5 pillars that any compliant AI agent system MUST implement:

1. **Identity** — Post-quantum cryptographic agent identity
2. **Governance** — Zero-trust capability enforcement
3. **Consensus** — BFT multi-agent decision validation
4. **Audit** — Merkle-chained tamper-proof logs
5. **Persistence** — Self-verifying agent state

## Compliance Levels

- **NTI-1 Level 1 (Basic)** — Pillars 1 and 4
- **NTI-1 Level 2 (Standard)** — All 5 pillars
- **NTI-1 Level 3 (Enterprise)** — All 5 pillars + HSM, SOC 2, ISO 27001

## Reference Implementation

The reference SDK is [`ube-foundation`](https://pypi.org/project/ube-foundation/),
available on PyPI and crates.io.

Framework integrations:
- [`langchain-nti`](https://pypi.org/project/langchain-nti/)
- [`crewai-nti`](https://pypi.org/project/crewai-nti/)
- [`autogen-nti`](https://pypi.org/project/autogen-nti/)

## Governance

The NTI-1 specification is maintained under the CC-BY-4.0 license.
Amendments are proposed via RFCs in the [rfcs/](./rfcs/) folder.

## License

Creative Commons Attribution 4.0 International (CC-BY-4.0).
