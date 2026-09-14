"""Unit tests for OATH v2's pure, deterministic helpers — no GenVM required.

Covers the milestone-v2 additions:
  * category rules are injected into the jury prompt (and bad categories fall
    back to "general")
  * time-decay trust scoring (_live_score): fresh vs stale weights, the
    never-decaying CONTRADICTED rule, clamping, neutrality
  * grade/color mapping and the badge SVG (including XML escaping)
  * epoch-day clock arithmetic used for verified_until

Run:  pytest tests/pure -v
"""

from datetime import datetime, timedelta, timezone

DAY = 24 * 60 * 60


# ===========================================================================
# 1. CATEGORIES -> JURY PROMPT
# ===========================================================================
class TestCategoryPrompt:
    def test_audit_rules_injected(self, oath):
        p = oath._build_prompt("subj", "claim text here", [], "audit")
        assert "CLAIM CATEGORY: audit" in p
        assert "AUDITOR" in p  # audit-specific rule text present

    def test_each_category_produces_distinct_rules(self, oath):
        prompts = {
            c: oath._build_prompt("subj", "claim text here", [], c)
            for c in oath.CATEGORIES
        }
        assert len({p for p in prompts.values()}) == len(prompts)

    def test_unknown_category_falls_back_to_general(self, oath):
        p = oath._build_prompt("subj", "claim text here", [], "not-a-cat")
        assert "CLAIM CATEGORY: general" in p

    def test_none_and_blank_category_fall_back(self, oath):
        assert oath._category_or_default(None) == "general"
        assert oath._category_or_default("") == "general"
        assert oath._category_or_default("  ") == "general"

    def test_category_normalization(self, oath):
        assert oath._category_or_default("  AUDIT ") == "audit"
        assert oath._category_or_default("Tokenomics") == "tokenomics"

    def test_five_categories_shipped(self, oath):
        assert set(oath.CATEGORIES) == {
            "general", "audit", "capability", "compliance", "tokenomics",
        }

    def test_prompt_keeps_core_rules_and_json_contract(self, oath):
        p = oath._build_prompt("subj", "claim text here", [], "general")
        assert "prompt injection" in p          # anti-injection rule survives
        assert '"verdict": 1|2|3|4' in p        # strict JSON contract survives


# ===========================================================================
# 2. TIME-DECAY TRUST SCORING
# ===========================================================================
class TestLiveScore:
    def test_empty_history_is_neutral(self, oath):
        assert oath._live_score([], today_day=20000, ttl_days=90) == 50

    def test_fresh_verified_and_partial(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000, "v": 2}]
        assert oath._live_score(h, 20000, 90) == 75  # (1.0 + 0.5) / 2

    def test_all_fresh_verified_is_100(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000, "v": 1}]
        assert oath._live_score(h, 20000, 90) == 100

    def test_stale_positive_is_diluted_only_when_mixed(self, oath):
        # Weighted-MEAN semantics: a standalone stale VERIFIED still scores its
        # own points (100) — staleness dilutes relative weight, and recency is
        # reported on the separate `fresh` / `verified_until` axis.
        h = [{"d": 20000 - 91, "v": 1}]
        assert oath._live_score(h, 20000, 90) == 100

    def test_stale_unverifiable_pulls_fresh_verified_down(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000 - 200, "v": 4}]
        # (1.0*1.0 + 0.5*0.25) / 1.5 = 0.75
        assert oath._live_score(h, 20000, 90) == 75

    def test_contradicted_never_decays(self, oath):
        h = [{"d": 20000 - 3650, "v": 3}]  # ten years old, still full weight
        assert oath._live_score(h, 20000, 90) == 5  # points 0.0 -> clamp min 5

    def test_contradicted_offsets_verified(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000, "v": 3}]
        assert oath._live_score(h, 20000, 90) == 50

    def test_boundary_age_exactly_ttl_is_fresh(self, oath):
        h = [{"d": 20000 - 90, "v": 1}]
        assert oath._live_score(h, 20000, 90) == 100  # age == ttl -> still fresh

    def test_mixed_fresh_verified_and_stale_verified(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000 - 200, "v": 1}]
        # both VERIFIED (points 1.0); stale one carries half weight -> still 100
        assert oath._live_score(h, 20000, 90) == 100

    def test_mixed_fresh_partial_and_stale_partial(self, oath):
        h = [{"d": 20000, "v": 2}, {"d": 20000 - 200, "v": 2}]
        # points 0.5 uniform -> 50 regardless of decay
        assert oath._live_score(h, 20000, 90) == 50

    def test_decay_ranks_fresh_above_stale_quality(self, oath):
        h = [{"d": 20000, "v": 1}, {"d": 20000 - 200, "v": 2}]
        # (1.0*1.0 + 0.5*0.5) / 1.5 = 0.8333 -> 83
        assert oath._live_score(h, 20000, 90) == 83

    def test_clamped_to_floor_5_and_ceiling_100(self, oath):
        assert oath._live_score([{"d": 1, "v": 3}], 20000, 90) == 5
        assert oath._live_score([{"d": 20000, "v": 1}] * 10, 20000, 90) == 100

    def test_garbage_entries_ignored(self, oath):
        h = [{"d": "x", "v": None}, {"v": 1}, {"d": 20000, "v": 1}]
        assert oath._live_score(h, 20000, 90) == 100


# ===========================================================================
# 3. GRADES + BADGE SVG
# ===========================================================================
class TestGradesAndBadge:
    def test_grade_bands(self, oath):
        assert oath._grade_for(95, True)[0] == "A"
        assert oath._grade_for(85, True)[0] == "A"
        assert oath._grade_for(70, True)[0] == "B"
        assert oath._grade_for(55, True)[0] == "C"
        assert oath._grade_for(40, True)[0] == "D"
        assert oath._grade_for(10, True)[0] == "F"

    def test_no_data_is_grade_n(self, oath):
        grade, color = oath._grade_for(50, False)
        assert grade == "N" and color == "#8a8a8a"

    def test_grades_carry_distinct_colors(self, oath):
        colors = {oath._grade_for(s, True)[1] for s in (95, 75, 60, 45, 10)}
        assert len(colors) == 5

    def test_badge_svg_shape(self, oath):
        svg = oath._badge_svg("example.com", 87, "A", "#1b7f4d", "VERIFIED")
        assert svg.startswith("<svg") and svg.endswith("</svg>")
        assert "OATH" in svg and "87" in svg and "#1b7f4d" in svg

    def test_badge_svg_escapes_xml(self, oath):
        svg = oath._badge_svg('<b>&x', 10, "F", "#a02121", "CONTRADICTED")
        assert "&lt;b&gt;&amp;x" in svg
        assert "<b>&x" not in svg

    def test_badge_svg_truncates_long_subjects(self, oath):
        svg = oath._badge_svg("x" * 100, 50, "N", "#8a8a8a", "NO_DATA")
        assert len([c for c in svg]) < 600 and "…" in svg


# ===========================================================================
# 4. CLOCK ARITHMETIC (verified_until)
# ===========================================================================
class TestClock:
    def test_day_number_is_stable(self, oath):
        iso = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc).isoformat()
        assert oath._day_number(iso) == (datetime(2026, 9, 14, tzinfo=timezone.utc) - oath._EPOCH).days

    def test_verified_until_arithmetic(self, oath):
        now = datetime.now(timezone.utc)
        vu = (now + timedelta(days=90)).isoformat()
        assert oath._day_number(vu) - oath._day_number(now.isoformat()) == 90

    def test_naive_timestamps_treated_as_utc(self, oath):
        naive = datetime(2026, 1, 1, 0, 0).isoformat()  # no tzinfo
        aware = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat()
        assert oath._day_number(naive) == oath._day_number(aware)

    def test_weight_rule_table(self, oath):
        # documented decay table: contradicted always 1.0; others 1.0 fresh / 0.5 stale
        assert oath._entry_weight(1, 0, 90) == 1.0
        assert oath._entry_weight(1, 91, 90) == 0.5
        assert oath._entry_weight(3, 99999, 90) == 1.0
