# NTI and the Accountable Agents Framework

Ten-slide outline for the W3C Agent Trust Protocol Community Group discussion.
Each slide lists what is on screen, the spoken note, and the artifact to show.

The framing throughout: Fuqiao's question was how existing Web standards compose
to satisfy AAF's requirements. This is one answer, offered as a working
composition with named gaps, not as a competing framework.

---

## Slide 1 — Title

On screen:

> Composing the Web's existing trust primitives for accountable agents
> One worked composition: identity, authority, enforcement, evidence
> Abisheak P. — Neutral Trust Infrastructure

**Speaker note.** The temptation with a new framework is to propose new
primitives. This talk proposes none. It takes DIDs, Verifiable Credentials, HTTP
authorization and transparency-log receipts, and shows one way to compose them so
that an agent action can be authorised and then proved afterwards.

**Artifact.** Nothing. Keep the first slide empty.

---

## Slide 2 — The question, in four parts

On screen:

| Fuqiao's question | The Web primitive | The hard part |
| :--- | :--- | :--- |
| Who is acting? | DIDs | key binding, rotation, resolution |
| On whose authority? | Verifiable Credentials | delegation chains, scope narrowing, revocation |
| Is it allowed right now? | HTTP authentication and authorization | enforcement point, fail-closed behaviour |
| How is it proved later? | *(none agreed)* | evidence that survives an adversarial audit |

**Speaker note.** The first three have answers. The fourth does not, and it is the
one an auditor asks about. Everything else in this deck is about the fourth row.

---

## Slide 3 — Why the fourth row is empty

On screen:

- A log records what a system chose to write down.
- The system that wrote it also controls it, rotates it, and can rewrite it.
- An audit that accepts the operator's own log is not an audit; it is a
  statement by the operator.

**Speaker note.** This is not an argument against logging. It is an argument that
logging answers a different question. Logs answer "what did this system do?"
Evidence answers "can you show me that this is what happened, without my having
to trust you?"

---

## Slide 4 — Why logs are not enough

On screen:

> "Neutral evidence whose integrity and provenance can be verified independently
> of the system that produced it."
>
> "A system cannot rely on its own logs when it is being audited."
>
> — Tymofii Pidlisnyi, Agent Passport System

**Speaker note.** This is the requirement stated better than I can state it. Two
properties are being asked for, and they are separable: integrity (it was not
altered) and provenance (it came from where it claims to). A hash chain gives the
first. Independent verification gives the second. You need both, and neither is
free.

**Note before presenting.** This quotes a private message. Confirm with Tymofii
that he is content to be quoted verbatim and attributed in a public deck, or
paraphrase and attribute as a position rather than a quotation.

---

## Slide 5 — The composition

On screen:

```text
  DID            VC chain           enforcement point        receipt
  ---            --------           -----------------        -------
  who            on whose           is this allowed          prove it
  acts           authority          right now                later

  did:webvh  ->  delegation    ->   sidecar + policy    ->   Merkle + signature
                 chain root         fail-closed              independently verifiable
```

**Speaker note.** Read it left to right. Each layer consumes the output of the one
before it. The receipt is not a log of the other three; it is a signed statement
that binds the request, the verdict and the version of the engine that produced
the verdict.

---

## Slide 6 — DIDs: who is acting

On screen:

- `did:webvh` — the DID is the host, the key material is verifiable history.
- Key binding is the identity: the engine pins the public key at registration and
  will only accept a signature from that key.
- A DID string alone is not an identity. A signature over a request, verified
  against the pinned key, is.
- Rotation is a history problem, not a config problem.

**Speaker note.** The failure mode this closes: a request that names a DID but
carries a key of the caller's choosing. If the verifier trusts the DID string, any
key works. Pinning at registration makes the signature mean something.

---

## Slide 7 — VCs: on whose authority

On screen:

- Authority is carried by an explicit delegation record, not inferred from the
  actor's identity.
- A delegation must state: capability, caveats, validity window, and who issued it.
- The chain is committed to by a single root, so a verifier checks one value.
- Revocation is the unsolved part: revoking an ancestor requires the token to name
  its parent. Ours does not yet.

**Speaker note.** Be explicit about that last line. A delegation chain you cannot
revoke partway up is a chain you cannot fully trust. This is a known gap in our
implementation, not a design position, and it is the first thing I would fix.

---

## Slide 8 — Authorization: the enforcement point

On screen:

- Authorization is a runtime decision, not a document.
- The enforcement point sits between the agent and the action, not inside the
  agent.
- Fail-closed: an error in identity, delegation, policy or consensus resolves to
  Deny, never to Allow.
- The observation comes from the enforcement point, not from the request. A
  workload that reports its own measurement has not been measured.

**Speaker note.** The last bullet is the one that gets argued about. If the caller
supplies the measurement, the binding is decorative. The measurement must be read
by the party enforcing, from the runtime, at the moment of the decision.

---

## Slide 9 — Accountability: receipts, not logs

On screen:

- One operation returns the verdict **and** its receipt. There is no API that
  accepts a verdict chosen by the caller.
- `receipt_hash` covers the request, the decision, the reason, and the engine
  version. The signature is by the engine's issuer key, never the actor's.
- A verifier: recompute the hash, verify the signature, check the chain link,
  then **re-evaluate the request on the declared engine version** and confirm the
  decision matches.
- That last step is what separates a receipt from a signed log line.

**Speaker note.** Anyone can sign a log entry. The distinguishing property is that
the verdict and the record of the verdict are the same object, so it is impossible
to obtain a receipt for a decision the engine did not make. Without that, a
receipt proves only that a wrapper was willing to sign.

---

## Slide 10 — What this does not claim, and the ask

On screen:

Not claimed:

- That these are the right primitives for AAF. They are one composition.
- That our conformance tests are ratified. The containment tests rest on a
  transition-contract draft that neither party has agreed.
- That firmware or embedded deployment works today. It does not.
- That a receipt proves authorization. It proves what was decided and by which
  engine version — not that the engine's inputs were honest.

The ask:

- Review the composition, not the implementation.
- Bring a counter-example: an AAF requirement this composition cannot express.
- Conformance candidates are published for exactly this: to be challenged before
  they are relied on.

**Speaker note.** End on the invitation, not the claim. The useful outcome of this
session is a requirement we cannot meet, because that is the one that tells us
what to build next.
