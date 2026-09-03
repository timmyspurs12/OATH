"""
OathRegistry — direct-mode regression tests (no Docker/Studio required).

Run:
    pytest tests/direct/test_oath_registry.py -v
    (or: gltest tests/direct/ -v)

These tests pin the invariants the review asked for:

  * appeal pricing            — first appeal = base stake x2, second = base x4,
                                priced off the ORIGINAL filing stake
  * fund conservation         — every staked GEN is treasury + pending refunds +
                                unsettled stake, and contract balance covers it
  * refund solvency           — refund_owed never exceeds contract balance,
                                and refund is only claimable once the claim FINAL
  * required re-adjudication  — an appealed (APPEALING) claim cannot be
                                finalized until it is re-adjudicated
  * provisional results       — trust score and stake settlement only happen at
                                finalize(), never on a provisional verdict, and
                                a re-adjudicated appeal REPLACES the old verdict
"""

import json
import pytest

CONTRACT = "contracts/oath_registry.py"

STAKE = 10 * 10**18          # 10 GEN in wei
STAKE_2 = 20 * 10**18        # first appeal extra (base x2)
STAKE_4 = 40 * 10**18        # second appeal extra (base x4)
FEE_BPS = 500                # 5%


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _mock_evidence(direct_vm, body="Audit report confirms the claim is true."):
    """Make the contract's own web fetch succeed with deterministic content."""
    direct_vm.mock_web(r".*", {"status": 200, "body": body})


def _mock_verdict(direct_vm, verdict):
    """Force the jury LLM to return a specific verdict JSON."""
    payload = json.dumps({
        "verdict": verdict,
        "confidence": 80,
        "rationale": "The evidence consistently supports this outcome and the primary source matches the claim.",
        "citations": ["https://evidence.example/report"],
    })
    direct_vm.mock_llm(r".*", payload)


def _deploy(direct_deploy, min_stake=STAKE, fee_bps=FEE_BPS, max_evidence=5,
            max_appeals=2, multiplier=2, window_days=7):
    return direct_deploy(
        CONTRACT, min_stake, fee_bps, max_evidence, max_appeals, multiplier, window_days
    )


def _file(direct_vm, contract, subject="example.com", claim=None, value=STAKE):
    direct_vm.value = value
    claim = claim or "This subject holds the publicly documented audit certification."
    cid = contract.file_claim(subject, claim, json.dumps(["https://evidence.example/report"]))
    direct_vm.value = 0
    return cid


def _adjudicate(direct_vm, contract, cid, verdict=1):
    _mock_verdict(direct_vm, verdict)
    label = contract.adjudicate(cid)
    direct_vm.clear_mocks()
    return label


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def oath(direct_vm, direct_deploy, direct_owner):
    """Production-like: 7-day window, 2 appeals, x2 multiplier, 10 GEN stake."""
    direct_vm.sender = direct_owner
    _mock_evidence(direct_vm)
    yield _deploy(direct_deploy, window_days=7, max_appeals=2, multiplier=2)


@pytest.fixture
def oath_final(direct_vm, direct_deploy, direct_owner):
    """Finalize-friendly: no appeals allowed and a 0-day window, so a verdict can
    be finalized immediately in tests (the 'appeals exhausted' path)."""
    direct_vm.sender = direct_owner
    _mock_evidence(direct_vm)
    yield _deploy(direct_deploy, window_days=0, max_appeals=0, multiplier=2)


# ===========================================================================
# 1. APPEAL PRICING
# ===========================================================================
class TestAppealPricing:
    def test_appeal_terms_match_config(self, oath):
        terms = oath.get_appeal_terms()
        assert terms["max_appeals"] == 2
        assert terms["appeal_multiplier"] == 2
        assert terms["appeal_window_days"] == 7
        assert terms["min_stake_wei"] == STAKE

    def test_first_appeal_costs_base_times_two(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        # underpay the appeal (only x1) -> revert
        direct_vm.value = STAKE
        with direct_vm.expect_revert("appeal stake required"):
            oath.appeal(cid)
        # exact x2 quote
        terms = oath.get_claim(cid)
        assert terms["next_appeal_stake_wei"] == STAKE_2
        direct_vm.value = STAKE_2
        assert oath.appeal(cid) == "APPEAL_OPEN"

    def test_second_appeal_costs_base_times_four(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        # first appeal x2 + re-adjudicate
        direct_vm.value = STAKE_2
        oath.appeal(cid)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        # second appeal must be x4 (NOT compounding off the already-paid stake)
        claim = oath.get_claim(cid)
        assert claim["next_appeal_stake_wei"] == STAKE_4
        direct_vm.value = STAKE_4
        assert oath.appeal(cid) == "APPEAL_OPEN"

    def test_priced_off_base_stake_not_running_total(self, direct_vm, oath):
        """After a x2 appeal the running total is 30 GEN, but the next appeal
        must still be priced on the 10 GEN base (x4 = 40), not 30x2 = 60."""
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        direct_vm.value = STAKE_2
        oath.appeal(cid)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        claim = oath.get_claim(cid)
        assert claim["stake_wei"] == STAKE + STAKE_2       # running total 30
        assert claim["next_appeal_stake_wei"] == STAKE_4   # but price = 40


# ===========================================================================
# 2. REQUIRED RE-ADJUDICATION AFTER APPEAL
# ===========================================================================
class TestReAdjudication:
    def test_cannot_finalize_while_appealing(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        direct_vm.value = STAKE_2
        oath.appeal(cid)
        assert oath.get_claim(cid)["status"] == "APPEALING"
        with direct_vm.expect_revert("re-adjudicate"):
            oath.finalize(cid)

    def test_must_adjudicate_before_any_finalize(self, direct_vm, oath_final):
        cid = _file(direct_vm, oath_final)
        # never adjudicated -> cannot finalize
        with direct_vm.expect_revert("nothing to finalize"):
            oath_final.finalize(cid)

    def test_finalize_blocked_while_window_open_with_appeals_left(self, direct_vm, oath):
        """On the production contract (7-day window, appeals left) a fresh
        verdict cannot be finalized early — this protects the appeal right."""
        cid = _file(direct_vm, oath)
        _adjudicate(direct_vm, oath, cid, verdict=1)
        with direct_vm.expect_revert("appeal window still open"):
            oath.finalize(cid)

    def test_re_adjudication_then_finalize_when_appeals_exhausted(self, direct_vm, direct_deploy, direct_owner):
        """With max_appeals spent, finalize is allowed after re-adjudication
        even before 7 days — the contract-configured rule."""
        direct_vm.sender = direct_owner
        _mock_evidence(direct_vm)
        # 7-day window but only ONE appeal allowed; exhaust it, then finalize.
        c = _deploy(direct_deploy, window_days=7, max_appeals=1, multiplier=2)
        cid = _file(direct_vm, c)
        _adjudicate(direct_vm, c, cid, verdict=1)
        direct_vm.value = STAKE_2
        c.appeal(cid)
        _adjudicate(direct_vm, c, cid, verdict=1)     # re-jury -> VERDICTED
        # appeals exhausted (1 of 1 used) -> finalizable now
        assert c.get_claim(cid)["status"] == "VERDICTED"
        assert c.finalize(cid) == "FINALIZED"
        assert c.get_claim(cid)["status"] == "FINAL"

    def test_appeal_only_when_verdicted(self, direct_vm, oath):
        cid = _file(direct_vm, oath)
        direct_vm.value = STAKE_2
        with direct_vm.expect_revert("only VERDICTED"):
            oath.appeal(cid)


# ===========================================================================
# 3. PROVISIONAL RESULTS — trust + stake only settle at finalize
# ===========================================================================
class TestProvisionalResults:
    def test_trust_neutral_before_finalize(self, direct_vm, oath_final):
        cid = _file(direct_vm, oath_final, subject="prov.example")
        # before any adjudication: neutral 50, zero verdicts
        t0 = oath_final.get_trust("prov.example")
        assert t0["score"] == 50 and t0["total_verdicts"] == 0
        _adjudicate(direct_vm, oath_final, cid, verdict=1)
        # verdict exists but is PROVISIONAL -> trust must STILL be neutral
        t1 = oath_final.get_trust("prov.example")
        assert t1["total_verdicts"] == 0
        assert t1["score"] == 50
        claim = oath_final.get_claim(cid)
        assert claim["verdict_final"] is False
        assert claim["settled"] is False

    def test_trust_updates_only_after_finalize(self, direct_vm, oath_final):
        cid = _file(direct_vm, oath_final, subject="fin.example")
        _adjudicate(direct_vm, oath_final, cid, verdict=1)   # VERIFIED provisional
        oath_final.finalize(cid)
        t = oath_final.get_trust("fin.example")
        assert t["total_verdicts"] == 1
        assert t["verified"] == 1
        assert t["score"] == 100                       # single VERIFIED -> 100
        assert oath_final.get_claim(cid)["verdict_final"] is True

    def test_appeal_outcome_replaces_provisional(self, direct_vm, direct_deploy, direct_owner):
        """An appealed verdict is overwritten, not double-counted."""
        direct_vm.sender = direct_owner
        _mock_evidence(direct_vm)
        # single allowed appeal: after appeal + re-jury, appeals are exhausted
        # so the claim can be finalized within the window.
        c = _deploy(direct_deploy, window_days=7, max_appeals=1, multiplier=2)
        cid = _file(direct_vm, c, subject="rep.example")
        _adjudicate(direct_vm, c, cid, verdict=1)      # provisional VERIFIED
        direct_vm.value = STAKE_2
        c.appeal(cid)
        _adjudicate(direct_vm, c, cid, verdict=3)      # re-jury CONTRADICTED
        c.finalize(cid)
        t = c.get_trust("rep.example")
        # exactly ONE verdict counted, and it is the FINAL (contradicted) one
        assert t["total_verdicts"] == 1
        assert t["contradicted"] == 1
        assert t["verified"] == 0
        stats = c.get_stats()
        assert stats["claims_contradicted"] == 1
        assert stats["claims_adjudicated"] == 1        # not double counted


# ===========================================================================
# 4. FUND CONSERVATION + REFUND SOLVENCY
# ===========================================================================
class TestFunds:
    def test_accounting_solvent_and_conserved_after_refund_path(self, direct_vm, oath_final):
        cid = _file(direct_vm, oath_final)
        _adjudicate(direct_vm, oath_final, cid, verdict=1)   # VERIFIED -> refund after fee
        oath_final.finalize(cid)
        acc = oath_final.get_accounting()
        assert acc["solvent"] is True
        assert acc["conserved"] is True
        # refund owed = stake - 5% fee
        claim = oath_final.get_claim(cid)
        assert claim["refund_owed_wei"] == STAKE - STAKE * FEE_BPS // 10000
        assert acc["pending_refunds_wei"] == claim["refund_owed_wei"]
        # treasury only holds the fee (nothing forfeited on VERIFIED)
        assert acc["treasury_wei"] == STAKE * FEE_BPS // 10000

    def test_contradicted_forfeits_stake_to_treasury(self, direct_vm, oath_final):
        cid = _file(direct_vm, oath_final)
        _adjudicate(direct_vm, oath_final, cid, verdict=3)   # CONTRADICTED
        oath_final.finalize(cid)
        acc = oath_final.get_accounting()
        assert acc["solvent"] is True
        assert acc["conserved"] is True
        claim = oath_final.get_claim(cid)
        assert claim["refund_owed_wei"] == 0           # forfeited
        assert acc["treasury_wei"] == STAKE            # entire stake to treasury

    def test_refund_only_claimable_when_final(self, direct_vm, oath_final, direct_bob):
        cid = _file(direct_vm, oath_final)
        _adjudicate(direct_vm, oath_final, cid, verdict=1)
        # still provisional -> no refund available yet
        with direct_vm.expect_revert("FINAL"):
            oath_final.claim_refund(cid)
        oath_final.finalize(cid)
        # a different account cannot claim someone else's refund
        direct_vm.sender = direct_bob
        with direct_vm.expect_revert("only the requester"):
            oath_final.claim_refund(cid)

    def test_conservation_holds_with_appeal_stakes(self, direct_vm, direct_deploy, direct_owner):
        direct_vm.sender = direct_owner
        _mock_evidence(direct_vm)
        c = _deploy(direct_deploy, window_days=7, max_appeals=1, multiplier=2)
        cid = _file(direct_vm, c)
        _adjudicate(direct_vm, c, cid, verdict=1)
        direct_vm.value = STAKE_2
        c.appeal(cid)
        _adjudicate(direct_vm, c, cid, verdict=1)
        # single appeal now exhausted -> finalizable; refund covers filing+appeal
        c.finalize(cid)
        acc = c.get_accounting()
        assert acc["solvent"] is True
        assert acc["conserved"] is True
        # total escrowed = 10 + 20 = 30 GEN; refund owed = 30 - 5% fee
        claim = c.get_claim(cid)
        assert claim["stake_wei"] == STAKE + STAKE_2
        assert claim["refund_owed_wei"] == (STAKE + STAKE_2) - (STAKE + STAKE_2) * FEE_BPS // 10000

    def test_conservation_holds_across_multiple_claims(self, direct_vm, oath_final):
        ids = []
        for s in ["a.example", "b.example", "c.example"]:
            ids.append((s, _file(direct_vm, oath_final, subject=s)))
        # verify one (refund) and contradict another (forfeit)
        _adjudicate(direct_vm, oath_final, ids[0][1], verdict=1)
        oath_final.finalize(ids[0][1])
        _adjudicate(direct_vm, oath_final, ids[1][1], verdict=3)
        oath_final.finalize(ids[1][1])
        # third left unsettled (still escrowed)
        acc = oath_final.get_accounting()
        assert acc["solvent"] is True
        assert acc["conserved"] is True
        # balance >= treasury + pending refunds + unsettled stake
        assert acc["contract_balance_wei"] >= (
            acc["treasury_wei"] + acc["pending_refunds_wei"] + acc["unsettled_stake_wei"]
        ) - 1
