"""
OATH v2 — direct-mode tests for the milestone additions.

Run (requires the GenLayer toolchain, as tests/direct/test_oath_registry.py):
    pytest tests/direct/test_milestone_v2.py -v

Pins the v2 behavior on top of the v1 invariants:

  * categories            — file_claim accepts an optional category; unknown
                            categories fall back to "general"; get_categories
                            exposes the rules; the category reaches the jury
  * freshness             — finalize stamps finalized_at + verified_until
                            (VERIFIED/PARTIAL only, finalized + TTL days);
                            get_claim.fresh / get_trust freshness fields
  * time-decay trust      — the trust score is recomputed from the capped
                            final-verdict ledger; CONTRADICTED never decays
  * reverify              — a FINAL claim can be reopened as a fresh claim
                            (new stake, same subject/claim/evidence/category,
                            linked via reverified_from)
  * badge                 — get_badge returns a machine-readable attestation
                            (schema, score, grade, color, svg)
  * backward compat       — the old 3-arg file_claim still works and files
                            as "general"; old constructor deployments still
                            pass all v1 regression tests
"""

import json
import pytest

CONTRACT = "contracts/oath_registry.py"

STAKE = 10 * 10**18          # 10 GEN in wei
TTL = 90                     # default freshness window (days)


# ---------------------------------------------------------------------------
# helpers (mirror tests/direct/test_oath_registry.py)
# ---------------------------------------------------------------------------
def _mock_evidence(direct_vm, body="Audit report confirms the claim is true."):
    direct_vm.mock_web(r".*", {"status": 200, "body": body})


def _mock_verdict(direct_vm, verdict):
    payload = json.dumps({
        "verdict": verdict,
        "confidence": 80,
        "rationale": "The evidence consistently supports this outcome and the primary source matches the claim.",
        "citations": ["https://evidence.example/report"],
    })
    direct_vm.mock_llm(r".*", payload)


def _deploy(direct_deploy, min_stake=STAKE, fee_bps=500, max_evidence=5,
            max_appeals=2, multiplier=2, window_days=0, ttl_days=TTL):
    return direct_deploy(
        CONTRACT, min_stake, fee_bps, max_evidence, max_appeals, multiplier,
        window_days, ttl_days,
    )


def _file(direct_vm, contract, subject="example.com", claim=None, value=STAKE,
          category=None):
    direct_vm.value = value
    claim = claim or "This subject holds the publicly documented audit certification."
    if category is None:
        cid = contract.file_claim(subject, claim, json.dumps(["https://evidence.example/report"]))
    else:
        cid = contract.file_claim(
            subject, claim, json.dumps(["https://evidence.example/report"]), category)
    direct_vm.value = 0
    return cid


def _adjudicate(direct_vm, contract, cid, verdict=1):
    _mock_verdict(direct_vm, verdict)
    label = contract.adjudicate(cid)
    direct_vm.clear_mocks()
    return label


def _finalize_verified(direct_vm, contract, subject="example.com", category="audit"):
    """file -> adjudicate VERIFIED -> finalize; returns (cid, claim)."""
    cid = _file(direct_vm, contract, subject=subject, category=category)
    _adjudicate(direct_vm, contract, cid, verdict=1)
    assert contract.finalize(cid) == "FINALIZED"
    return cid, contract.get_claim(cid)


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def oath(direct_vm, direct_deploy, direct_owner):
    """Fast-lane v2: 0-day appeal window, no appeals (finalize immediately)."""
    direct_vm.sender = direct_owner
    _mock_evidence(direct_vm)
    yield _deploy(direct_deploy)


@pytest.fixture
def oath_ttl0(direct_vm, direct_deploy, direct_owner):
    """Freshness disabled via constructor knob (verdict_ttl_days = 0)."""
    direct_vm.sender = direct_owner
    _mock_evidence(direct_vm)
    yield _deploy(direct_deploy, ttl_days=0)


# ===========================================================================
# 1. CATEGORIES
# ===========================================================================
class TestCategories:
    def test_get_categories_exposes_rules(self, oath):
        cats = oath.get_categories()
        assert set(cats.keys()) == {"general", "audit", "capability", "compliance", "tokenomics"}
        assert "AUDITOR" in cats["audit"]
        assert "ISSUER" in cats["compliance"]

    def test_valid_category_is_stored(self, direct_vm, oath):
        cid = _file(direct_vm, oath, category="audit")
        assert oath.get_claim(cid)["category"] == "audit"

    def test_backward_compat_three_arg_file_is_general(self, direct_vm, oath):
        cid = _file(direct_vm, oath)          # old 3-arg call shape
        assert oath.get_claim(cid)["category"] == "general"

    def test_unknown_category_falls_back_to_general(self, direct_vm, oath):
        cid = _file(direct_vm, oath, category="not-a-thing")
        assert oath.get_claim(cid)["category"] == "general"

    def test_category_normalized(self, direct_vm, oath):
        cid = _file(direct_vm, oath, category="  Tokenomics ")
        assert oath.get_claim(cid)["category"] == "tokenomics"

    def test_category_too_long_reverts(self, direct_vm, oath):
        with direct_vm.expect_revert("category too long"):
            _file(direct_vm, oath, category="x" * 64)

    def test_verdict_view_carries_category(self, direct_vm, oath):
        cid = _file(direct_vm, oath, category="compliance")
        _adjudicate(direct_vm, oath, cid, verdict=1)
        assert oath.get_verdict(cid)["category"] == "compliance"


# ===========================================================================
# 2. FRESHNESS (verified_until) AT FINALIZE
# ===========================================================================
class TestFreshness:
    def test_finalize_stamps_finalized_and_verified_until(self, direct_vm, oath):
        cid, claim = _finalize_verified(direct_vm, oath)
        assert claim["status"] == "FINAL"
        assert claim["finalized_at"] != ""
        assert claim["verified_until"] != ""
        assert claim["fresh"] is True

    def test_contradicted_has_no_freshness_window(self, direct_vm, oath):
        cid = _file(direct_vm, oath, subject="bad.example")
        _adjudicate(direct_vm, oath, cid, verdict=3)
        oath.finalize(cid)
        claim = oath.get_claim(cid)
        assert claim["verified_until"] == ""
        assert claim["fresh"] is False

    def test_ttl_zero_disables_freshness(self, direct_vm, oath_ttl0):
        cid, claim = _finalize_verified(direct_vm, oath_ttl0)
        assert claim["verified_until"] == ""
        assert claim["fresh"] is False

    def test_provisional_verdict_not_fresh(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)   # provisional only
        assert oath.get_claim(cid)["fresh"] is False
        assert oath.get_claim(cid)["finalized_at"] == ""

    def test_get_trust_reports_freshness(self, direct_vm, oath):
        _finalize_verified(direct_vm, oath, subject="fresh.example")
        t = oath.get_trust("fresh.example")
        assert t["fresh"] is True
        assert t["fresh_verdicts"] == 1
        assert t["stale_verdicts"] == 0
        assert t["verified_until"] != ""
        assert t["score"] == 100                       # one fresh VERIFIED

    def test_neutral_subject_reports_no_freshness(self, direct_vm, oath):
        t = oath.get_trust("never-seen.example")
        assert t["score"] == 50
        assert t["fresh"] is False
        assert t["fresh_verdicts"] == 0


# ===========================================================================
# 3. REVERIFY — the freshness loop
# ===========================================================================
class TestReverify:
    def test_reverify_reopens_final_claim(self, direct_vm, oath):
        old_cid, old = _finalize_verified(direct_vm, oath)
        direct_vm.value = STAKE
        new_cid = oath.reverify(old_cid)
        direct_vm.value = 0
        new = oath.get_claim(new_cid)
        assert new["status"] == "PENDING"
        assert new["reverified_from"] == old_cid
        assert new["subject"] == old["subject"]
        assert new["claim"] == old["claim"]
        assert new["category"] == old["category"]
        assert new["evidence"] == old["evidence"]
        assert new["stake_wei"] == STAKE
        assert old["status"] == "FINAL"                # source untouched

    def test_reverify_only_from_final(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        direct_vm.value = STAKE
        with direct_vm.expect_revert("only FINAL"):
            oath.reverify(cid)
        direct_vm.value = 0

    def test_reverify_requires_min_stake(self, direct_vm, oath):
        old_cid, _ = _finalize_verified(direct_vm, oath)
        direct_vm.value = STAKE - 1
        with direct_vm.expect_revert("stake too low"):
            oath.reverify(old_cid)
        direct_vm.value = 0

    def test_reverified_claim_runs_to_settlement(self, direct_vm, oath):
        old_cid, _ = _finalize_verified(direct_vm, oath, subject="loop.example")
        direct_vm.value = STAKE
        new_cid = oath.reverify(old_cid)
        direct_vm.value = 0
        _adjudicate(direct_vm, oath, new_cid, verdict=1)
        oath.finalize(new_cid)
        t = oath.get_trust("loop.example")
        assert t["total_verdicts"] == 2                # two FINAL verdicts now
        assert t["verified"] == 2
        stats = oath.get_stats()
        assert stats["claims_reverified"] == 1

    def test_contradicted_reverify_dents_trust(self, direct_vm, oath):
        old_cid, _ = _finalize_verified(direct_vm, oath, subject="flip.example")
        direct_vm.value = STAKE
        new_cid = oath.reverify(old_cid)
        direct_vm.value = 0
        _adjudicate(direct_vm, oath, new_cid, verdict=3)
        oath.finalize(new_cid)
        t = oath.get_trust("flip.example")
        assert t["total_verdicts"] == 2
        assert t["contradicted"] == 1
        assert t["score"] == 50                        # (1.0 + 0.0) / 2
        # the older VERIFIED verdict ages out but the CONTRADICTED never decays


# ===========================================================================
# 4. BADGE — machine-readable attestation
# ===========================================================================
class TestBadge:
    def test_badge_schema_and_grade_for_verified_subject(self, direct_vm, oath):
        _finalize_verified(direct_vm, oath, subject="grade.example")
        b = oath.get_badge("grade.example")
        assert b["schema"] == "oath.badge.v1"
        assert b["subject"] == "grade.example"
        assert b["score"] == 100
        assert b["grade"] == "A"
        assert b["verdict_label"] == "VERIFIED"
        assert b["fresh"] is True
        assert b["final_verdicts"] == 1

    def test_badge_no_data(self, oath):
        b = oath.get_badge("unknown.example")
        assert b["schema"] == "oath.badge.v1"
        assert b["grade"] == "N"
        assert b["fresh"] is False
        assert b["final_verdicts"] == 0

    def test_badge_svg_contains_score_and_escapes(self, direct_vm, oath):
        _finalize_verified(direct_vm, oath, subject="svg.example")
        b = oath.get_badge("svg.example")
        assert b["svg"].startswith("<svg")
        assert "100" in b["svg"]
        assert b["color"] in b["svg"]

    def test_badge_grade_f_for_contradicted(self, direct_vm, oath):
        cid = _file(direct_vm, oath, subject="f.example")
        _adjudicate(direct_vm, oath, cid, verdict=3)
        oath.finalize(cid)
        b = oath.get_badge("f.example")
        assert b["grade"] == "F"
        assert b["verdict_label"] == "CONTRADICTED"


# ===========================================================================
# 5. CONFIG SURFACING
# ===========================================================================
class TestConfig:
    def test_get_stats_exposes_v2_knobs(self, oath):
        s = oath.get_stats()
        assert s["verdict_ttl_days"] == TTL
        assert s["claims_reverified"] == 0
        assert s["max_evidence"] == 5
        assert s["appeal_window_days"] == 0

    def test_get_claim_v2_fields_default_clean(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        c = oath.get_claim(cid)
        assert c["finalized_at"] == ""
        assert c["verified_until"] == ""
        assert c["reverified_from"] == 0
        assert c["fresh"] is False
