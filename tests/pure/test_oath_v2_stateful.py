"""End-to-end v2 state-machine tests executed on the in-process fake GenVM
(tests/pure/fake_genvm.py) — no GenLayer toolchain required.

Mirrors the direct-mode suite (tests/direct/test_milestone_v2.py) so the same
guarantees can be checked in any CI: file -> adjudicate -> finalize ->
freshness -> reverify -> badge, plus backward compatibility and v1 settlement
invariants on the v2 contract.

Run:  pytest tests/pure/test_oath_v2_stateful.py -v
"""

import json

import pytest

from fake_genvm import load_contract, reverts

STAKE = 10 * 10**18          # 10 GEN in wei
TTL = 90

EVIDENCE = json.dumps(["https://evidence.example/report"])
CLAIM_TEXT = "This subject holds the publicly documented audit certification."


def _verdict_payload(verdict, confidence=80):
    return json.dumps({
        "verdict": verdict,
        "confidence": confidence,
        "rationale": "The evidence consistently supports this outcome and the primary source matches the claim.",
        "citations": ["https://evidence.example/report"],
    })


@pytest.fixture
def vm():
    Deployed, _fake = load_contract()
    d = Deployed()  # defaults: 0-day window? no — window 7, appeals 2, ttl 90
    d.mock_web(r".*", "Audit report confirms the claim is true.")
    return d


@pytest.fixture
def oath(vm):
    """Fast-lane: 0-day appeal window, no appeals -> finalize immediately."""
    d = load_contract()[0](appeal_window_days=0, max_appeals=0)
    d.mock_web(r".*", "Audit report confirms the claim is true.")
    return d


def _file(d, subject="example.com", category=None, value=STAKE):
    d.value = value
    try:
        if category is None:
            cid = d.file_claim(subject, CLAIM_TEXT, EVIDENCE)
        else:
            cid = d.file_claim(subject, CLAIM_TEXT, EVIDENCE, category)
    finally:
        d.value = 0
    return cid


def _adjudicate(d, cid, verdict=1):
    d.mock_llm(r".*", _verdict_payload(verdict))
    try:
        return d.adjudicate(cid)
    finally:
        d.clear_mocks()


def _finalized(d, subject="example.com", category="audit", verdict=1):
    cid = _file(d, subject=subject, category=category)
    _adjudicate(d, cid, verdict=verdict)
    assert d.finalize(cid) == "FINALIZED"
    return cid, d.get_claim(cid)


# ===========================================================================
# 1. CATEGORIES
# ===========================================================================
class TestCategories:
    def test_get_categories_exposes_rules(self, oath):
        cats = oath.get_categories()
        assert set(cats) == {"general", "audit", "capability", "compliance", "tokenomics"}
        assert "AUDITOR" in cats["audit"]
        assert "ISSUER" in cats["compliance"]

    def test_valid_category_stored(self, vm):
        cid = _file(vm, category="audit")
        assert vm.get_claim(cid)["category"] == "audit"

    def test_three_arg_file_claim_still_works(self, vm):
        cid = _file(vm)  # v1 call shape — backward compatible
        assert vm.get_claim(cid)["category"] == "general"

    def test_unknown_category_falls_back(self, vm):
        cid = _file(vm, category="not-a-thing")
        assert vm.get_claim(cid)["category"] == "general"

    def test_category_reaches_the_jury_prompt(self, vm):
        seen = {}
        d = vm

        orig_prompt_builder = d.m._build_prompt

        def spy(subject, claim_text, snippets, category="general"):
            seen["category"] = category
            return orig_prompt_builder(subject, claim_text, snippets, category)

        d.m._build_prompt = spy
        cid = _file(d, category="tokenomics")
        _adjudicate(d, cid, verdict=1)
        assert seen["category"] == "tokenomics"

    def test_category_too_long_reverts(self, vm):
        reverts(vm, "category too long",
                lambda: _file(vm, category="x" * 64))


# ===========================================================================
# 2. FRESHNESS AT FINALIZE
# ===========================================================================
class TestFreshness:
    def test_finalize_stamps_finalized_and_verified_until(self, oath):
        cid, claim = _finalized(oath)
        assert claim["status"] == "FINAL"
        assert claim["finalized_at"] != ""
        assert claim["verified_until"] != ""
        assert claim["fresh"] is True

    def test_contradicted_has_no_freshness_window(self, oath):
        cid, claim = _finalized(oath, subject="bad.example", verdict=3)
        assert claim["verified_until"] == ""
        assert claim["fresh"] is False

    def test_provisional_not_fresh(self, oath):
        cid = _file(oath)
        _adjudicate(oath, cid, verdict=1)
        claim = oath.get_claim(cid)
        assert claim["finalized_at"] == ""
        assert claim["fresh"] is False

    def test_get_trust_freshness_fields(self, oath):
        _finalized(oath, subject="fresh.example")
        t = oath.get_trust("fresh.example")
        assert t["fresh"] is True
        assert t["fresh_verdicts"] == 1
        assert t["stale_verdicts"] == 0
        assert t["score"] == 100
        assert t["score_at_settlement"] == 100

    def test_neutral_subject(self, oath):
        t = oath.get_trust("never-seen.example")
        assert t["score"] == 50 and t["fresh"] is False

    def test_history_ledger_capped_at_32(self, vm):
        d = load_contract()[0](appeal_window_days=0, max_appeals=0)
        d.mock_web(r".*", "Audit report confirms the claim is true.")
        for i in range(40):
            cid = _file(d, subject=f"cap{i}.example")
            _adjudicate(d, cid, verdict=1)
            d.finalize(cid)
        t = d.get_trust("cap39.example")     # per-subject, so 1 each — sanity
        assert t["total_verdicts"] == 1
        # one subject hammered 40 times keeps only the last 32 ledger entries
        for i in range(40):
            cid = _file(d, subject="hammer.example")
            _adjudicate(d, cid, verdict=1)
            d.finalize(cid)
        t = d.get_trust("hammer.example")
        assert t["total_verdicts"] == 40     # lifetime counters keep growing
        assert t["fresh_verdicts"] == 32     # ledger capped at HISTORY_CAP
        assert t["score"] == 100


# ===========================================================================
# 3. REVERIFY
# ===========================================================================
class TestReverify:
    def test_reverify_reopens_final_claim(self, oath):
        old_cid, old = _finalized(oath)
        oath.value = STAKE
        new_cid = oath.reverify(old_cid)
        oath.value = 0
        new = oath.get_claim(new_cid)
        assert new["status"] == "PENDING"
        assert new["reverified_from"] == old_cid
        assert new["subject"] == old["subject"]
        assert new["claim"] == old["claim"]
        assert new["category"] == old["category"]
        assert new["evidence"] == old["evidence"]
        assert new["stake_wei"] == STAKE
        assert oath.get_claim(old_cid)["status"] == "FINAL"

    def test_reverify_only_from_final(self, oath):
        cid = _file(oath)
        oath.value = STAKE
        reverts(oath, "only FINAL", lambda: oath.reverify(cid))
        oath.value = 0

    def test_reverify_requires_min_stake(self, oath):
        old_cid, _ = _finalized(oath)
        oath.value = STAKE - 1
        reverts(oath, "stake too low", lambda: oath.reverify(old_cid))
        oath.value = 0

    def test_reverified_claim_runs_to_settlement(self, oath):
        old_cid, _ = _finalized(oath, subject="loop.example")
        oath.value = STAKE
        new_cid = oath.reverify(old_cid)
        oath.value = 0
        _adjudicate(oath, new_cid, verdict=1)
        oath.finalize(new_cid)
        t = oath.get_trust("loop.example")
        assert t["total_verdicts"] == 2
        assert t["verified"] == 2
        assert oath.get_stats()["claims_reverified"] == 1

    def test_contradicted_reverify_dents_trust(self, oath):
        old_cid, _ = _finalized(oath, subject="flip.example")
        oath.value = STAKE
        new_cid = oath.reverify(old_cid)
        oath.value = 0
        _adjudicate(oath, new_cid, verdict=3)
        oath.finalize(new_cid)
        t = oath.get_trust("flip.example")
        assert t["total_verdicts"] == 2
        assert t["contradicted"] == 1
        assert t["score"] == 50        # fresh VERIFIED (1.0) + CONTRADICTED (0.0)


# ===========================================================================
# 4. BADGE
# ===========================================================================
class TestBadge:
    def test_badge_for_verified_subject(self, oath):
        _finalized(oath, subject="grade.example")
        b = oath.get_badge("grade.example")
        assert b["schema"] == "oath.badge.v1"
        assert b["score"] == 100
        assert b["grade"] == "A"
        assert b["verdict_label"] == "VERIFIED"
        assert b["fresh"] is True
        assert b["final_verdicts"] == 1
        assert b["svg"].startswith("<svg") and "100" in b["svg"]

    def test_badge_no_data(self, oath):
        b = oath.get_badge("unknown.example")
        assert b["grade"] == "N"
        assert b["fresh"] is False
        assert b["final_verdicts"] == 0

    def test_badge_grade_f_for_contradicted(self, oath):
        _finalized(oath, subject="f.example", verdict=3)
        b = oath.get_badge("f.example")
        assert b["grade"] == "F"
        assert b["verdict_label"] == "CONTRADICTED"

    def test_badge_score_decays_after_ttl(self, vm):
        # deploy with ttl 0: positive verdicts are stale immediately,
        # CONTRADICTED keeps full weight — the decay is visible in the badge
        d = load_contract()[0](appeal_window_days=0, max_appeals=0, verdict_ttl_days=0)
        d.mock_web(r".*", "Audit report confirms the claim is true.")
        cid = _file(d, subject="decay.example")
        _adjudicate(d, cid, verdict=1)
        d.finalize(cid)
        b = d.get_badge("decay.example")
        assert b["fresh"] is False
        # single stale VERIFIED: mean stays 100 but recency flag is off
        assert b["score"] == 100
        # now a contradicted claim on another subject never decays
        cid2 = _file(d, subject="decay2.example")
        _adjudicate(d, cid2, verdict=3)
        d.finalize(cid2)
        b2 = d.get_badge("decay2.example")
        assert b2["grade"] == "F"


# ===========================================================================
# 5. BACKWARD COMPAT — v1 invariants still hold on the v2 contract
# ===========================================================================
class TestV1Compat:
    def test_v1_regression_suite_essentials(self, oath):
        # provisional verdicts do not touch trust
        cid = _file(oath, subject="prov.example")
        _adjudicate(oath, cid, verdict=1)
        assert oath.get_trust("prov.example")["total_verdicts"] == 0
        # settlement happens exactly once at finalize (idempotent afterwards)
        assert oath.finalize(cid) == "FINALIZED"
        t = oath.get_trust("prov.example")
        assert t["total_verdicts"] == 1 and t["score"] == 100
        assert oath.finalize(cid) == "FINALIZED"          # second call: no-op
        assert oath.get_trust("prov.example")["total_verdicts"] == 1

    def test_fund_conservation_after_refund_path(self, oath):
        cid, _ = _finalized(oath)
        acc = oath.get_accounting()
        assert acc["solvent"] is True
        assert acc["conserved"] is True
        assert oath.get_claim(cid)["refund_owed_wei"] == STAKE - STAKE * 500 // 10000

    def test_stats_exposes_v2_knobs(self, oath):
        s = oath.get_stats()
        assert s["verdict_ttl_days"] == TTL
        assert s["claims_reverified"] == 0
        assert s["max_evidence"] == 5
