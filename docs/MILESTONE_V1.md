# OATH — Milestone v1 delta document

**Project:** OATH — Claim Verification Protocol
**Repository:** https://github.com/timmyspurs12/OATH
**Baseline (accepted project):** commit `5520855` — *"Deferred settlement:
provisional verdicts, finalize-only trust/stake settlement, appeal pricing,
refunds; 17 regression tests; app reads appeal terms + refunds"*

This milestone ships **two new layers of substantial work** on top of the
accepted version — a contract upgrade (new on-chain functionality) and an
agent integration stack — plus frontend support, and everything is
repo-verifiable: every feature below points at code, tests and runnable tools
in this repository.

---

## 1. Contract v2 — new functionality (`contracts/oath_registry.py`)

| # | Feature | Where to look | Why it matters |
|---|---------|---------------|----------------|
| 1.1 | **Claim categories.** `file_claim(subject, claim_text, evidence_json, category="general")` accepts `audit / capability / compliance / tokenomics / general`. Each category injects type-specific judging rules into the jury prompt — an audit claim is checked against the auditor's own registry, a compliance claim against the issuer's official register, etc. Unknown values fall back to `general`; the old 3-arg call still works. | `CATEGORIES`, `_category_or_default()`, `_build_prompt(..., category)`, `file_claim` | Verdict quality: an audit claim is no longer judged like a marketing claim. `get_categories()` exposes the exact rules on-chain. |
| 1.2 | **Verdict freshness.** At `finalize`, positive verdicts (VERIFIED / PARTIAL) are stamped with `verified_until = finalized + verdict_ttl_days` (new constructor knob, default 90). `get_claim` returns `finalized_at`, `verified_until`, `fresh`. | `finalize()`, `Claim` fields, `_claim_fresh()` | Verifications expire. A "verified in 2024" badge is not a current verification. |
| 1.3 | **Time-decay trust scoring.** Subjects keep a capped (32-entry) ledger of final verdicts (`SubjectScore.history_json`). `get_trust` / `get_trust_batch` recompute the score against *today*: fresh positive verdicts count 1.0, stale positives count 0.5, and CONTRADICTED verdicts keep full weight forever (trust is hard to build, easy to lose). Stored score preserved as `score_at_settlement`. | `_live_score()`, `_entry_fresh()`, `_entry_weight()`, `_update_trust()`, `_live_trust()` | The trust score now *moves with time* — decay is deterministic and readable, not bolted on in clients. |
| 1.4 | **`reverify(claim_id)`** (payable). Reopens a FINAL claim as a fresh PENDING claim with a new min-stake: same subject/claim/evidence/category, linked via `reverified_from`. Counted in `get_stats().claims_reverified`. | `reverify()` | The freshness loop: stale verifications get re-run by anyone, at stake. |
| 1.5 | **`get_badge(subject)`** — machine-readable attestation card: schema `oath.badge.v1`, live score, grade A–F, color, freshness, final-verdict count and a ready-to-embed **SVG badge** for READMEs/UIs. | `get_badge()`, `_grade_for()`, `_badge_svg()` | The adoption hook: any project can show an "OATH A · 87" badge backed by on-chain verdicts. |
| 1.6 | **Config surfacing.** `get_stats()` now returns `verdict_ttl_days`, `max_evidence`, `max_appeals`, `appeal_multiplier`, `appeal_window_days`, `claims_reverified`. | `get_stats()` | Apps/agents read configuration; nothing is hard-coded. |

**Backward compatibility:** the v1 `file_claim` 3-argument call shape still
works (files as `general`); the new constructor parameter is appended last with
a default; all v1 views keep their original keys (v2 fields are additive).
The v1 regression suite (`tests/direct/test_oath_registry.py`, 17 tests) is
unchanged and must still pass.

## 2. Agent stack — new integration

| # | Artifact | What it does |
|---|----------|--------------|
| 2.1 | **`sdk/oath_client.py`** (+ `sdk/README.md`) | The OATH SDK: read client (`get_trust`, `get_badge`, `badge_svg`, `get_categories`, …) and write client (`file_claim`, `adjudicate`, `appeal`, `finalize`, `reverify`, `claim_refund`) over `genlayer-py`, plus **`trust_gate(subjects, min_score, require_fresh)`** — the one-call TRUSTED/UNTRUSTED decision any agent makes before transacting. |
| 2.2 | **`tools/mcp_server.py`** | An MCP server (Model Context Protocol) exposing **11 OATH tools** — `oath_get_trust`, `oath_get_badge`, `oath_trust_gate`, `oath_file_claim`, `oath_adjudicate`, … — so Claude Desktop / Cursor / any MCP agent can query and use OATH live. Runs on stdio; env-configured (`OATH_ADDRESS`, `OATH_CHAIN`); write tools activate only with `OATH_KEY`. |
| 2.3 | **`tools/agent_example.py`** | Runnable trust-gated agent demo: before "paying" vendors, it gates each through OATH and holds payments to stale/contradicted subjects. `--demo` mode runs offline against a labeled fixture; live mode reads the deployed registry. |

This is the README's promise made real: *"Any wallet, agent, marketplace or
x402 payer can call `get_trust(subject)` before transacting."*

## 3. Frontend (`app/index.html` + root `index.html` copy)

- **Category picker** on the filing form (drives the on-chain category).
- **Category + REVERIFIED chips** in the docket; category in the case meta strip.
- **Freshness on the case page:** `FRESH / STALE · verified until YYYY-MM-DD`
  for finalized positive verdicts, plus a **REVERIFY** button (one click, new
  stake, fresh jury).
- **Trust ledger** shows the fresh/stale split and decay note; protocol page
  documents the new API + FAQ entries.
- Still a single self-contained file; root `index.html` kept byte-identical
  for GitHub Pages.

## 4. Tests — the delta is pinned

| Suite | Count | Runs where |
|-------|-------|-----------|
| `tests/direct/test_oath_registry.py` (v1 invariants) | 17 | GenLayer toolchain (`pytest tests/direct -v`) |
| `tests/direct/test_milestone_v2.py` (v2 state machine, direct-mode) | 24 | GenLayer toolchain |
| `tests/pure/test_oath_v2_helpers.py` (pure logic: categories→prompt, decay math, grades, SVG, clock) | 30 | anywhere: `pytest tests/pure -v` |
| `tests/pure/test_oath_v2_stateful.py` (full lifecycle on the in-process fake GenVM: file→adjudicate→finalize→freshness→reverify→badge + v1 compat) | 24 | anywhere: `pytest tests/pure -v` |

**78 new tests; 95 total.**

`tests/pure/fake_genvm.py` is a documented test harness (collapsed consensus,
zero-init storage, mocked web/LLM) — it lets CI verify the contract state
machine without the GenVM toolchain; the authoritative direct-mode suites
remain `tests/direct/`.

## 5. Live deployment evidence

Filled in during the deployment walkthrough
(`docs/DEPLOY_V2_WALKTHROUGH.md`):

- v2 contract address: `0x________________________________`
- Network: ____________  ·  Explorer link: ____________
- Live case demonstrating the full loop (file → adjudicate → finalize →
  reverify): claim ids `____`, `____`
- App pointed at the v2 deployment: https://timmyspurs12.github.io/OATH/

## 6. Suggested portal submission text

**Title:** `OATH v2 — categories, freshness & the agent stack`

**Changes & Improvements (≤1000 chars):**

> OATH v2 ships two new layers, pinned by 78 new tests (95 total).
>
> CONTRACT — new functionality: file_claim takes a claim category
> (audit/capability/compliance/tokenomics) that injects type-specific judging
> rules into the jury prompt; positive verdicts now carry a 90-day freshness
> window with time-decay trust scoring (stale positives count half,
> CONTRADICTED never decays); new reverify() reopens stale claims at fresh
> stake; new get_badge(subject) returns a machine-readable attestation card
> (score, grade A–F, embeddable SVG). v1 call shapes stay compatible.
>
> AGENTS — new integration: an SDK (sdk/oath_client.py) with a one-call
> trust_gate TRUSTED/UNTRUSTED primitive, an MCP server (tools/mcp_server.py)
> exposing 11 OATH tools to Claude/Cursor/any agent, and a runnable
> trust-gated payment demo.
>
> FRONTEND: category picker, FRESH/STALE case states, one-click reverify.
>
> LIVE: deployed at 0x… on …; cases #n (file→jury→finalize→reverify) on the
> explorer; app re-pointed at the v2 registry.

*(Replace the `0x…`/`#n` placeholders with the deployment evidence from §5
before submitting.)*

**Evidence & supporting information:**

- Delta document: this file (`docs/MILESTONE_V1.md`)
- Pure test run (no toolchain needed): `pytest tests/pure -v` — 54 passed
- Agent demo: `python tools/agent_example.py --demo`
- MCP server: `OATH_ADDRESS=0x… python tools/mcp_server.py`
- Deployment walkthrough: `docs/DEPLOY_V2_WALKTHROUGH.md`
