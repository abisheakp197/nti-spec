# Security Policy

## Supported Versions

We actively maintain and patch the latest release of the NTI-1 Specification.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

This repository defines the formal NTI-1 protocol, threat model, and conformance examples for the AI agent trust ecosystem. Because downstream implementations depend on this specification, cryptographic ambiguities, logical flaws, or insecure conformance examples are treated as critical security issues.

Please report vulnerabilities directly to <abisheakp197@gmail.com>.

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

- Type of issue (e.g., protocol logic flaw, insecure conformance example, cryptographic ambiguity, missing threat boundary)
- The specific section or RFC number in the specification
- Any special configuration or implementation details required to exploit the ambiguity

We will investigate all legitimate reports and do our best to quickly update the specification and issue a security advisory.
