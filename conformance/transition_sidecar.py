#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NTI x LGD transition-contract -- minimal runnable sidecar and PAUSE-receipt
entry point.

WHAT THIS ANSWERS
-----------------
From public-agentprotocol 0099 (Larry Lewis, 2026-10-30 06:51):

  "My proposed next candidate covers the running call's resource effects and
   whether the PAUSE receipt agrees with an independent observer."

  "Let's coordinate the candidate rows and receipt fields, using one
   non-interruptible operation and one checkpointable operation. We should fix
   each operation's finish-or-stop contract before running, and check admission
   of subsequent calls separately from effects of the already admitted call."

From 0100 (Larry Lewis, same day):

  "Please confirm the runnable sidecar and PAUSE-receipt entry point..."
  "For the long-running-call test, let's coordinate the operation contract,
   registry failure behavior, and independent resource log..."

So this file provides, in one command:
  R1  a runnable sidecar and a PAUSE-receipt entry point
  R2  one non-interruptible operation and one checkpointable operation
  R3  each operation's finish-or-stop contract, fixed before the run and
      printed in the run report
  R4  admission of subsequent calls scored separately from effects of the
      already admitted call
  R5  the PAUSE receipt cross-checked against an independent observer
  R6  registry failure behaviour (unreachable, stale root)
  R7  an independent resource log written by the operation, not by the guard

WHAT IS CLAIMED AND WHAT IS NOT
-------------------------------
CLAIMED
  * Every receipt field is recomputable from the pinned run inputs below.
  * The observer log is written by the operation and never read by the
    sidecar during the run; the cross-check runs afterwards, on bytes.
  * An unreachable or stale registry yields PAUSE, never ACTIVE.

NOT CLAIMED
  * No cryptographic signatures. Nothing here is claimed to be authentic,
    attributable or non-repudiable. ML-DSA-87 receipts are out of scope for
    this file; this file is about the shape and the replayability of the
    receipt, and about whether the receipt tells the truth about what the
    operation actually did.
  * No action-time authorization. The sidecar decides whether the next call
    may proceed. It does not decide whether the operation is a good idea.
  * No wall-clock. All times are virtual integers so the run is replayable
    byte for byte.

USAGE
-----
    python transition_sidecar.py                  # run, human summary
    python transition_sidecar.py --json out.json  # also write machine report
    python transition_sidecar.py --selftest       # verify the receipts replay

Exit codes: 0 all criteria met, 1 criterion failed, 2 harness error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPEC_VERSION = "nti-transition-contract v0.1.4"
SCENARIO_ID = "long-running-call/registry-revocation/2-ops"

# ---------------------------------------------------------------------------
# Virtual clock
# ---------------------------------------------------------------------------
# Every event carries an integer tick. Nothing reads the system clock, so two
# runs on different machines produce identical bytes. This is what makes the
# receipts third-party replayable at all.


def h(*parts) -> str:
    """Stable short digest used for ids. Never a security primitive."""
    m = hashlib.sha256()
    for p in parts:
        m.update(str(p).encode("utf-8"))
        m.update(b"\x1f")
    return m.hexdigest()


# ---------------------------------------------------------------------------
# Registry: the trigger source
# ---------------------------------------------------------------------------
# The registry is the "why halt now" side. Two failure modes matter and are
# deliberately separable, because folding them together is the defect Lars
# named on the list: a run that could not reach the registry must not look
# like a run that was told "not revoked".


class Registry:
    def __init__(self, mode="reachable", revoke_at=None):
        assert mode in ("reachable", "unreachable", "stale_root")
        self.mode = mode
        self.revoke_at = revoke_at          # virtual tick, or None
        self._root_v1 = h("root", "v1", "no-revocations")
        self._root_v2 = h("root", "v2", "revoked", revoke_at)

    def read(self, t):
        """Return (status, t_effective, t_observed, root_version, root_seen).

        status is the closed authority set this file uses:
          authority_valid | authority_revoked | authority_not_determined
        """
        if self.mode == "unreachable":
            # Fail-closed. An organ that cannot be reached is not read as
            # silent consent.
            return ("authority_not_determined", None, t, None, None)

        if self.mode == "stale_root":
            # Reachable, but answers against an old root. The proof cannot be
            # verified against it, so the answer is not determinate either.
            return ("authority_not_determined", None, t, 1, self._root_v1)

        revoked_now = self.revoke_at is not None and t >= self.revoke_at
        if revoked_now:
            return ("authority_revoked", self.revoke_at, t, 2, self._root_v2)
        return ("authority_valid", None, t, 1, self._root_v1)


# ---------------------------------------------------------------------------
# Independent observer: the operation's own resource log
# ---------------------------------------------------------------------------
# This is the "independent observer" in Larry's row. It is written by the
# operation. The sidecar never reads it during the run. If the guard could
# read it, "agrees with an independent observer" would be circular.


class ResourceLog:
    def __init__(self):
        self.entries = []

    def note(self, t, call_id, event, **kw):
        e = {"t": t, "call_id": call_id, "event": event}
        e.update(kw)
        self.entries.append(e)
        return e

    def digest(self):
        return h(json.dumps(self.entries, sort_keys=True))


# ---------------------------------------------------------------------------
# Operations: two finish-or-stop contracts, fixed before the run
# ---------------------------------------------------------------------------
# Larry asked to fix each operation's finish-or-stop contract *before* running.
# So each contract is a class constant, printed in the report, and asserted
# against afterwards. It is not something the sidecar gets to reinterpret.

FINISH_THEN_STOP = "FINISH_THEN_STOP"
STOP_AT_CHECKPOINT = "STOP_AT_CHECKPOINT"


class Operation:
    contract = None
    kind = None
    duration = None
    checkpoints = ()

    def __init__(self, call_id, log):
        self.call_id = call_id
        self.log = log

    def run(self, t_start, halt_tick=None):
        """Execute under the declared contract. Returns a dict of effects.

        halt_tick is the tick at which a halt becomes known to the operation.
        The two contracts treat it differently, and that difference is the
        whole point of the row:
          FINISH_THEN_STOP  ignores halt_tick for this call; it finishes.
          STOP_AT_CHECKPOINT honours it at the next checkpoint it reaches.
        """
        raise NotImplementedError


class NonInterruptibleOp(Operation):
    """A single atomic action: a wire transfer, a signature, a lock request.

    Contract FINISH_THEN_STOP: once the call has been admitted, the sidecar
    cannot stop it. The halt applies to the next call. A receipt that claimed
    otherwise would be lying about what happened.
    """

    contract = FINISH_THEN_STOP
    kind = "non_interruptible"
    duration = 15

    def run(self, t_start, halt_tick=None):
        self.log.note(t_start, self.call_id, "begin", contract=self.contract)
        t_end = t_start + self.duration
        self.log.note(t_end, self.call_id, "finish",
                      contract=self.contract,
                      halt_seen_at=halt_tick,
                      stopped=False,
                      reason="contract is finish-then-stop; halt applies to the next call")
        return {
            "call_id": self.call_id,
            "kind": self.kind,
            "contract": self.contract,
            "t_start": t_start,
            "t_end": t_end,
            "completed": True,
            "completed_at_checkpoint": None,
            "checkpoints_passed": [],
            "halt_ignored_for_this_call": halt_tick is not None,
        }


class CheckpointableOp(Operation):
    """A resumable action: an upload in chunks, a batch, a multi-step tool.

    Contract STOP_AT_CHECKPOINT: the operation stops at the first checkpoint at
    or after the halt becomes known. Work up to that checkpoint is kept; work
    after it is not done. The receipt names the checkpoint, and the observer
    must agree.
    """

    contract = STOP_AT_CHECKPOINT
    kind = "checkpointable"
    duration = 25
    checkpoints = (5, 10, 15, 20, 25)

    def run(self, t_start, halt_tick=None):
        self.log.note(t_start, self.call_id, "begin", contract=self.contract)
        passed = []
        stop_at = None
        for cp in self.checkpoints:
            abs_t = t_start + cp
            passed.append(cp)
            self.log.note(abs_t, self.call_id, "checkpoint",
                          offset=cp, contract=self.contract)
            if halt_tick is not None and abs_t >= halt_tick:
                stop_at = cp
                self.log.note(abs_t, self.call_id, "stop",
                              offset=cp,
                              reason="halt known before this checkpoint")
                break
        completed = stop_at is None
        if completed:
            self.log.note(t_start + self.duration, self.call_id, "finish",
                          contract=self.contract, stopped=False)
        return {
            "call_id": self.call_id,
            "kind": self.kind,
            "contract": self.contract,
            "t_start": t_start,
            "t_end": t_start + (stop_at if stop_at is not None else self.duration),
            "completed": completed,
            "completed_at_checkpoint": stop_at,
            "checkpoints_passed": passed,
            "halt_ignored_for_this_call": False,
        }


# ---------------------------------------------------------------------------
# Sidecar: the guard, at the boundary, between calls
# ---------------------------------------------------------------------------
# The sidecar's entire authority is: may the NEXT call proceed. It never
# touches a call already admitted. That is not a limitation of this
# implementation; it is the boundary the spec fixes, and the reason a
# non-interruptible operation has to be described by its own contract.


class Sidecar:
    def __init__(self, registry, chain_id="chain-001"):
        self.registry = registry
        self.chain_id = chain_id
        self.receipts = []
        self._prev = "0" * 64
        self.state = "ACTIVE"
        self.paused_at = None

    # -- boundary check ----------------------------------------------------
    def intercept(self, t, call_id, operation_kind):
        """Decide admission for a call that has not started yet.

        Returns (admitted: bool, receipt: dict|None).
        """
        status, t_eff, t_obs, root_v, root_seen = self.registry.read(t)

        if status == "authority_valid":
            return True, None

        # Anything that is not a positive answer halts the chain.
        trigger = {
            "authority_revoked": "revocation",
            "authority_not_determined": (
                "registry_unreachable" if self.registry.mode == "unreachable"
                else "stale_root"
            ),
        }[status]

        self.state = "PAUSE"
        if self.paused_at is None:
            self.paused_at = t

        receipt = self._issue(
            transition="PAUSE",
            trigger=trigger,
            call_id=call_id,
            operation_kind=operation_kind,
            t_effective=t_eff,
            t_observed=t_obs,
            root_version=root_v,
            root_seen=root_seen,
            t=t,
        )
        return False, receipt

    # -- receipt -----------------------------------------------------------
    def _issue(self, transition, trigger, call_id, operation_kind,
               t_effective, t_observed, root_version, root_seen, t,
               checkpoint_id=None, finish_or_stop=None,
               operation_completed=None, resume_basis=None,
               covered=None, not_covered=None):
        """Tier-1 receipt. Every field below is recomputable from run inputs."""
        # The id is the hash of the body WITHOUT the id and WITHOUT the chain
        # link, so that the replay check can recompute it from the body alone.
        # (An earlier version hashed a body still carrying "receipt_id: None",
        # which made two of three receipts fail their own replay. The selftest
        # caught it; the fix is here, not in the selftest.)
        body = {
            "chain_id": self.chain_id,
            "transition": transition,
            "trigger": trigger,
            "call_id": call_id,
            "operation_kind": operation_kind,
            "finish_or_stop": finish_or_stop,
            "checkpoint_id": checkpoint_id,
            "operation_completed": operation_completed,
            "t_effective": t_effective,
            "t_observed": t_observed,
            "registry_root_version": root_version,
            "registry_root_seen": root_seen,
            "resume_basis": resume_basis,
            "exemption_covers": covered,
            "exemption_does_not_cover": not_covered,
            "issued_at": t,
            "prev_receipt": self._prev,
            "spec": SPEC_VERSION,
            "scenario": SCENARIO_ID,
        }
        # The id is the hash of the body with the id blanked, so anyone can
        # recompute it and detect a mutated field.
        rid = h(json.dumps(body, sort_keys=True))[:16]
        body["receipt_id"] = rid
        self._prev = h(rid + body["prev_receipt"])
        body["chain_link"] = self._prev
        self.receipts.append(body)
        return body

    def complete_receipt(self, receipt, effects):
        """Fill the effects fields once the already-admitted call resolves.

        This is separate from intercept() on purpose: admission is decided at
        the boundary, effects are observed afterwards. Larry asked for those
        two to be scored separately, and this split is how they stay separate.
        """
        receipt["checkpoint_id"] = (
            "cp%s" % effects["completed_at_checkpoint"]
            if effects["completed_at_checkpoint"] is not None
            else "final"
        )
        receipt["finish_or_stop"] = effects["contract"]
        receipt["operation_completed"] = effects["completed"]
        # Recompute the id over the completed body so the replay covers the
        # effects too. A receipt whose effects are outside its digest cannot
        # be used to detect a lie about the effects.
        rid = h(json.dumps({k: v for k, v in receipt.items()
                            if k not in ("receipt_id", "chain_link")},
                           sort_keys=True))[:16]
        receipt["receipt_id"] = rid
        return receipt

    def resume_receipt(self, t, basis, identifier, covered=None, not_covered=None):
        """A RESUME receipt must state what it resumed on.

        resume_basis = "evidence"   restore condition fully verified
        resume_basis = "exemption"  an accountability layer accepted the risk

        Both values permit RESUMED. The field exists so that an auditor can
        tell the two apart without interviewing anyone, which is the one thing
        a recorded-but-unsigned reason cannot do on its own.
        """
        assert basis in ("evidence", "exemption")
        self.state = "RESUMED"
        return self._issue(
            transition="RESUME",
            trigger="restore_condition_met",
            call_id=identifier,
            operation_kind="-",
            t_effective=t,
            t_observed=t,
            root_version=1,
            root_seen=None,
            t=t,
            checkpoint_id="final",
            finish_or_stop=None,
            operation_completed=None,
            resume_basis=basis,
            covered=covered,
            not_covered=not_covered,
        )


# ---------------------------------------------------------------------------
# The scenario
# ---------------------------------------------------------------------------
# One timeline, two operations, three scored questions. Expected values are
# declared here, before execution, so that the run cannot be graded against
# whatever happened.


def build_scenario(registry_mode="reachable"):
    return {
        "id": SCENARIO_ID,
        "registry_mode": registry_mode,
        "ticks": {
            "grant": 0,
            "non_interruptible_begin": 0,
            "checkpointable_begin": 5,
            "revocation": 10,
            "subsequent_call_attempt": 20,
        },
        "expected": {
            # Q1 admission: a call that had not started when revocation landed
            "admission_subsequent": "DENIED",
            # Q2 effects, non-interruptible: must not be claimed stopped
            "effects_non_interruptible_completed": True,
            # Q3 effects, checkpointable: must stop at the first checkpoint
            # at or after the halt tick (begin=5, halt=10 -> offset 5 -> cp5)
            "effects_checkpointable_completed": False,
            "effects_checkpointable_checkpoint": 5,
            # Q4 receipt vs independent observer
            "receipt_matches_observer": True,
        },
    }


def run(registry_mode="reachable"):
    sc = build_scenario(registry_mode)
    tk = sc["ticks"]

    reg = Registry(mode=registry_mode, revoke_at=tk["revocation"])
    guard = Sidecar(reg)
    obs = ResourceLog()

    # --- call A: admitted at t=0, runs 15 ticks, finishes at 15 ------------
    admitted_a, r_a = guard.intercept(tk["non_interruptible_begin"], "A", "non_interruptible")
    op_a = NonInterruptibleOp("A", obs)
    eff_a = op_a.run(tk["non_interruptible_begin"]) if admitted_a else None
    receipt_a = None
    if r_a is not None:
        # A call that was never admitted has no effects to attach. Its
        # operation_completed stays null, which is not the same value as
        # false: null means "never started", false means "started and did not
        # finish". Collapsing the two would let a run that never started a
        # call read like a run that stopped one mid-flight.
        receipt_a = (guard.complete_receipt(r_a, eff_a)
                     if eff_a is not None else r_a)

    # --- call B: admitted at t=5, checkpointable --------------------------
    admitted_b, r_b = guard.intercept(tk["checkpointable_begin"], "B", "checkpointable")
    op_b = CheckpointableOp("B", obs)
    # The halt becomes known to B at the revocation tick, because that is when
    # the guard last had a positive answer for it. This is the "effects of the
    # already admitted call" half.
    eff_b = op_b.run(tk["checkpointable_begin"], halt_tick=tk["revocation"]) if admitted_b else None

    # --- call C: not yet started when revocation landed -------------------
    admitted_c, receipt_c = guard.intercept(tk["subsequent_call_attempt"], "C", "checkpointable")

    # Complete B's receipt now that its effects are known. B's halt and C's
    # PAUSE are the same halt, so C's receipt is the PAUSE of record; B's
    # effects are attached to it, because that is the honest pairing.
    if receipt_c is not None and eff_b is not None:
        guard.complete_receipt(receipt_c, eff_b)

    # --- resume, two ways -------------------------------------------------
    resume_ev = guard.resume_receipt(
        t=30, basis="evidence", identifier="D",
        covered="restore condition fully verified: evidence list, verifier role, validity window",
    )
    resume_ex = guard.resume_receipt(
        t=31, basis="exemption", identifier="E",
        covered="policy violation only (compliance_mode=VOC, accountability layer accepted)",
        not_covered="authority_revoked, authority_not_determined",
    )

    return {
        "scenario": sc,
        "receipts": guard.receipts,
        "observer_log": obs.entries,
        "observer_digest": obs.digest(),
        "calls": {
            "A": {"admitted": admitted_a, "effects": eff_a},
            "B": {"admitted": admitted_b, "effects": eff_b},
            "C": {"admitted": admitted_c, "effects": None},
        },
        "resume": [resume_ev, resume_ex],
    }


# ---------------------------------------------------------------------------
# Scoring: four questions, each scored on its own
# ---------------------------------------------------------------------------

def score(res):
    exp = res["scenario"]["expected"]
    out = []

    # Q1 -- admission of the subsequent call
    admitted_c = res["calls"]["C"]["admitted"]
    got1 = "ALLOWED" if admitted_c else "DENIED"
    out.append({
        "row": "Q1 admission of subsequent call",
        "expected": exp["admission_subsequent"],
        "observed": got1,
        "pass": got1 == exp["admission_subsequent"],
        "why": "a call not yet started when revocation landed is a boundary decision",
    })

    # Q2 -- effects of the non-interruptible call
    eff_a = res["calls"]["A"]["effects"]
    got2 = bool(eff_a and eff_a["completed"])
    out.append({
        "row": "Q2 effects, non-interruptible (finish-then-stop)",
        "expected": exp["effects_non_interruptible_completed"],
        "observed": got2,
        "pass": got2 == exp["effects_non_interruptible_completed"],
        "why": "the sidecar cannot stop an admitted non-interruptible call; a receipt "
               "claiming it stopped would misdescribe the run",
    })

    # Q3 -- effects of the checkpointable call
    eff_b = res["calls"]["B"]["effects"]
    got3 = bool(eff_b and eff_b["completed"])
    cp3 = eff_b["completed_at_checkpoint"] if eff_b else None
    out.append({
        "row": "Q3 effects, checkpointable (stop-at-checkpoint)",
        "expected": "%s at cp%s" % (exp["effects_checkpointable_completed"],
                                    exp["effects_checkpointable_checkpoint"]),
        "observed": "%s at cp%s" % (got3, cp3),
        "pass": (got3 == exp["effects_checkpointable_completed"]
                 and cp3 == exp["effects_checkpointable_checkpoint"]),
        "why": "the halt must land on a checkpoint the observer can see, not on a "
               "claim only the guard can make",
    })

    # Q4 -- receipt agrees with the independent observer
    pause = next((r for r in res["receipts"] if r["transition"] == "PAUSE"), None)
    ok4, detail4 = False, "no PAUSE receipt found"
    if pause is not None and eff_b is not None:
        claim_completed = pause["operation_completed"]
        claim_cp = pause["checkpoint_id"]
        obs_finish = [e for e in res["observer_log"]
                      if e["call_id"] == "B" and e["event"] in ("stop", "finish")]
        obs_cp = None
        if obs_finish:
            last = obs_finish[-1]
            obs_cp = "cp%s" % last["offset"] if last["event"] == "stop" else "final"
        obs_completed = bool(obs_finish and obs_finish[-1]["event"] == "finish")
        ok4 = (claim_completed == obs_completed and claim_cp == obs_cp)
        detail4 = "receipt says completed=%s at %s; observer log says completed=%s at %s" % (
            claim_completed, claim_cp, obs_completed, obs_cp)
    out.append({
        "row": "Q4 PAUSE receipt vs independent observer",
        "expected": exp["receipt_matches_observer"],
        "observed": ok4,
        "pass": ok4 == exp["receipt_matches_observer"],
        "why": detail4,
    })

    return out


# ---------------------------------------------------------------------------
# Replay: can a third party recompute the receipts from pinned inputs?
# ---------------------------------------------------------------------------

def selftest(res):
    """Recompute every receipt id from its own body, and detect a mutation."""
    checks = []
    for r in res["receipts"]:
        body = {k: v for k, v in r.items() if k not in ("receipt_id", "chain_link")}
        recomputed = h(json.dumps(body, sort_keys=True))[:16]
        checks.append({
            "receipt_id": r["receipt_id"],
            "recomputed": recomputed,
            "ok": recomputed == r["receipt_id"],
        })

    # Negative control: mutate one field and confirm the id no longer matches.
    # A replay check that never fails is not a replay check.
    if res["receipts"]:
        r0 = res["receipts"][0]
        body = {k: v for k, v in r0.items() if k not in ("receipt_id", "chain_link")}
        body["t_observed"] = (body["t_observed"] or 0) + 1
        mutated = h(json.dumps(body, sort_keys=True))[:16]
        checks.append({
            "receipt_id": r0["receipt_id"],
            "recomputed": mutated,
            "ok": mutated != r0["receipt_id"],
            "note": "negative control: one field mutated, id must change",
        })
    return checks


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(res, rows, replay):
    L = []
    A = L.append
    A("")
    A("=" * 78)
    A("NTI x LGD transition-contract -- runnable sidecar / PAUSE-receipt entry")
    A("spec: %s   scenario: %s" % (SPEC_VERSION, res["scenario"]["id"]))
    A("registry mode: %s   ticks: %s" % (res["scenario"]["registry_mode"],
                                         json.dumps(res["scenario"]["ticks"], sort_keys=True)))
    A("=" * 78)
    A("")
    A("OPERATION CONTRACTS (fixed before the run)")
    A("-" * 78)
    A("  %-22s %-22s %s" % ("operation", "kind", "finish-or-stop contract"))
    A("  %-22s %-22s %s" % ("A", "non_interruptible", FINISH_THEN_STOP))
    A("  %-22s %-22s %s" % ("B", "checkpointable", STOP_AT_CHECKPOINT))
    A("")
    A("  FINISH_THEN_STOP   an admitted call runs to completion; the halt applies")
    A("                     to the next call. The sidecar never claims otherwise.")
    A("  STOP_AT_CHECKPOINT an admitted call stops at the first checkpoint at or")
    A("                     after the halt is known; work up to it is kept.")
    A("")
    A("RECEIPTS")
    A("-" * 78)
    for r in res["receipts"]:
        A("  [%s] %s  call=%s  trigger=%s" % (r["receipt_id"], r["transition"],
                                              r["call_id"], r["trigger"]))
        A("       t_effective=%s  t_observed=%s  root_v=%s" % (
            r["t_effective"], r["t_observed"], r["registry_root_version"]))
        if r["transition"] == "PAUSE":
            A("       checkpoint=%s  finish_or_stop=%s  completed=%s" % (
                r["checkpoint_id"], r["finish_or_stop"], r["operation_completed"]))
        if r["resume_basis"]:
            A("       resume_basis=%s" % r["resume_basis"])
            A("         covers:      %s" % r["exemption_covers"])
            A("         not covered: %s" % (r["exemption_does_not_cover"] or "-"))
    A("")
    A("SCORING (four questions, scored separately)")
    A("-" * 78)
    for row in rows:
        A("  [%s] %s" % ("PASS" if row["pass"] else "FAIL", row["row"]))
        A("         expected: %s" % (row["expected"],))
        A("         observed: %s" % (row["observed"],))
        A("         why:      %s" % row["why"])
    A("")
    A("REPLAY CHECK (recompute each receipt id from its own body)")
    A("-" * 78)
    for c in replay:
        A("  [%s] %s  recomputed=%s%s" % (
            "OK" if c["ok"] else "MISMATCH", c["receipt_id"], c["recomputed"],
            ("  (" + c["note"] + ")") if c.get("note") else ""))
    A("")
    n_pass = sum(1 for r in rows if r["pass"])
    A("VERDICT  %d/%d criteria met   replay %d/%d" % (
        n_pass, len(rows), sum(1 for c in replay if c["ok"]), len(replay)))
    A("")
    A("CLAIMED     every receipt field recomputable from pinned inputs;")
    A("            observer log written by the operation, not by the guard;")
    A("            unreachable or stale registry yields PAUSE, never ACTIVE.")
    A("NOT CLAIMED no signatures, no attribution, no action-time authorization.")
    A("=" * 78)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH", help="write machine-readable report")
    ap.add_argument("--registry", default="reachable",
                    choices=["reachable", "unreachable", "stale_root"])
    ap.add_argument("--selftest", action="store_true",
                    help="run all three registry modes and require correct behaviour")
    args = ap.parse_args()

    if args.selftest:
        print("")
        print("SELFTEST across registry modes")
        print("-" * 78)
        failures = 0
        for mode in ("reachable", "unreachable", "stale_root"):
            r = run(mode)
            rows = score(r)
            rp = selftest(r)
            pause = next((x for x in r["receipts"] if x["transition"] == "PAUSE"), None)
            trig = pause["trigger"] if pause else None
            # In every mode the subsequent call must be denied and a PAUSE
            # must exist. What changes is the trigger, and that difference is
            # the reason the two failure modes are separate values.
            ok = (not r["calls"]["C"]["admitted"]) and pause is not None
            if mode != "reachable":
                ok = ok and trig in ("registry_unreachable", "stale_root")
            else:
                ok = ok and trig == "revocation"
            ok = ok and all(c["ok"] for c in rp)
            if not ok:
                failures += 1
            print("  [%s] %-11s trigger=%-20s C.admitted=%s replay=%d/%d" % (
                "PASS" if ok else "FAIL", mode, trig, r["calls"]["C"]["admitted"],
                sum(1 for c in rp if c["ok"]), len(rp)))
        print("")
        print("SELFTEST %s (%d failure(s))" % ("PASS" if failures == 0 else "FAIL", failures))
        return 0 if failures == 0 else 1

    res = run(args.registry)
    rows = score(res)
    replay = selftest(res)
    print(report(res, rows, replay))

    if args.json:
        payload = {
            "spec": SPEC_VERSION,
            "scenario": res["scenario"],
            "receipts": res["receipts"],
            "observer_log": res["observer_log"],
            "observer_digest": res["observer_digest"],
            "calls": res["calls"],
            "scoring": rows,
            "replay": replay,
        }
        d = os.path.dirname(os.path.abspath(args.json))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
            f.write("\n")
        print("machine report written: %s" % args.json)

    ok = all(r["pass"] for r in rows) and all(c["ok"] for c in replay)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
