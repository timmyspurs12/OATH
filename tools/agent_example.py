#!/usr/bin/env python3
"""Trust-gated agent — the OATH protocol's intended consumer.

A marketplace agent is about to pay two vendors. Before sending anything, it
runs each vendor through the OATH trust gate: verified + fresh scores pass,
stale or contradicted subjects are rejected with reasons.

Two modes:

    python tools/agent_example.py --demo
        Runs against a built-in mock registry (no network, no keys) so anyone
        can see the flow immediately. Output is clearly labeled DEMO.

    OATH_ADDRESS=0x… OATH_CHAIN=studionet python tools/agent_example.py
        Live mode — reads the real deployed OathRegistry via genlayer-py
        (Python 3.12+, `pip install genlayer-py`). Read-only: needs no key.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sdk"))

from oath_client import OathClient  # noqa: E402

# vendors the agent intends to pay, with what it knows about them
VENDORS = {
    "audited-vendor.example": "would pay 400 GEN",
    "sketchy-vendor.example": "would pay 400 GEN",
}


def demo_registry() -> dict:
    """Mock get_trust_batch payload — clearly a DEMO fixture, nothing live."""
    return [
        {
            "subject": "audited-vendor.example",
            "total_verdicts": 3, "verified": 2, "partial": 1, "contradicted": 0,
            "score": 83, "fresh": True, "fresh_verdicts": 2, "stale_verdicts": 1,
            "last_verdict_label": "VERIFIED",
        },
        {
            "subject": "sketchy-vendor.example",
            "total_verdicts": 2, "verified": 0, "partial": 0, "contradicted": 2,
            "score": 5, "fresh": False, "fresh_verdicts": 0, "stale_verdicts": 2,
            "last_verdict_label": "CONTRADICTED",
        },
    ]


class DemoGate:
    """Offline stand-in for OathClient.trust_gate over demo_registry()."""

    def __init__(self, records):
        self.records = records

    def trust_gate(self, subjects, min_score=70, require_fresh=True):
        results, ok = {}, True
        for r in self.records:
            if r["subject"] not in subjects:
                continue
            reasons = []
            if r["score"] < min_score:
                reasons.append(f"score {r['score']} < required {min_score}")
            if require_fresh and not r["fresh"] and r["total_verdicts"] > 0:
                reasons.append("no verdict inside the freshness window — request reverification")
            if "contradicted" in r and r["contradicted"] and r["score"] < min_score:
                reasons.append("prior claim CONTRADICTED on chain")
            results[r["subject"]] = {
                "pass": not reasons, "score": r["score"], "fresh": r["fresh"],
                "grade": r["last_verdict_label"], "reasons": reasons,
            }
            ok = ok and not reasons
        return {"schema": "oath.trust_gate.v1", "decision": "TRUSTED" if ok else "UNTRUSTED",
                "min_score": min_score, "require_fresh": require_fresh, "subjects": results}


def print_gate(gate, vendors):
    print(json.dumps(gate, indent=2))
    print("\nAgent decisions:")
    for subject, note in vendors.items():
        r = gate["subjects"].get(subject)
        if r is None:
            print(f"  ✗ {subject:28s} — not on record; agent requests a claim be filed first")
        elif r["pass"]:
            print(f"  ✓ {subject:28s} — {note}  (score {r['score']}, {r['grade']})")
        else:
            print(f"  ✗ {subject:28s} — payment HELD: {'; '.join(r['reasons'])}")


def main():
    ap = argparse.ArgumentParser(description="OATH trust-gated agent demo")
    ap.add_argument("--demo", action="store_true", help="run against the built-in mock registry")
    ap.add_argument("--min-score", type=int, default=70)
    args = ap.parse_args()

    if args.demo or not os.environ.get("OATH_ADDRESS"):
        print("=== OATH trust-gated agent — DEMO MODE (mock registry, no network) ===\n")
        gate = DemoGate(demo_registry()).trust_gate(list(VENDORS), min_score=args.min_score)
        print_gate(gate, VENDORS)
        print("\nRun with OATH_ADDRESS=<deployed registry> for live reads.")
        return

    print(f"=== OATH trust-gated agent — LIVE ({os.environ.get('OATH_CHAIN', 'studionet')}) ===\n")
    oath = OathClient(address=os.environ["OATH_ADDRESS"],
                      chain=os.environ.get("OATH_CHAIN", "studionet"))
    gate = oath.trust_gate(list(VENDORS), min_score=args.min_score)
    print_gate(gate, VENDORS)


if __name__ == "__main__":
    main()
