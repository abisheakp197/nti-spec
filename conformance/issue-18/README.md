# Issue #18 conformance vectors

Shared test vectors contributed for #18:

- `preimage_reproducibility.json` — the RFC 8785 (JCS) canonical preimage and its
  SHA-256, with a worked example of how the current colon-joined preimage lets two
  different events collide (`colon_join_collides: true`, `jcs_collides: false`).
- `tamper_detection.json` — a valid chain and a mutated variant that MUST fail
  verification.
- `truncation.json` — a valid chain and a prefix that MUST NOT be accepted as
  complete (link-checking alone passes it; completeness needs the expected length).
- `duplicate_vote.json` — three votes from one `voter_id` at threshold 3, which
  MUST be denied.

These are generated, not hand-written. The deterministic generator and a test that
regenerates them byte-for-byte and checks each against a working harness are at
https://github.com/chopmob-cloud/algovoi-ube (`scripts/gen_issue18_vectors.py`,
`vectors/issue-18/`, `tests/test_issue18_vectors.py`).

**License:** these vectors are contributed under Apache-2.0
(SPDX-License-Identifier: Apache-2.0).
