# OATH — Architecture

## The one-liner

OATH is a claim-verification protocol: an Intelligent Contract that fetches your
evidence itself, adjudicates it with a decentralized LLM jury, and writes a
citable, appealable verdict plus a machine-queryable trust score — so agents,
wallets and marketplaces can answer *"should I trust this?"* with one call.

## System diagram

```
                        ┌──────────────────────────────────────────────┐
   claimant (EOA/agent) │         OATH REGISTRY (Intelligent Contract) │
   ────────────────────▶│                                              │
   file_claim(subject,  │  1. file_claim  [payable]  ── stake 10 GEN ──▶  storage:
    claim, evidence[],  │     validate · store · status=PENDING          TreeMap claims
    stake)              │                                              ◆  TreeMap subjects
                        │  2. adjudicate(id)                            ◆  counters
                        │     ┌─────────────────────────────────────┐  │
   ┌──────────────┐     │     │  NON-DETERMINISTIC BLOCK           │  │
   │  EVIDENCE    │◀────┼─────│  leader_fn:                        │  │
   │  (web)       │  ───│────▶│   gl.nondet.web.request(url)  ×N    │  │
   │  registry/   │     │     │   gl.nondet.exec_prompt(prompt,    │  │   after consensus:
   │  explorer/   │     │     │       response_format='json')      │  │   • verdict/conf/rationale
   │  docs/audit  │     │     │                                   │  │   • citations written
   └──────────────┘     │     │  validator_fn: (runs again,        │  │   • trust score updated
                        │     │   compares STRUCTURE + verdict)    │  │   • stake settled / refund
                        │     └──────────────────────────────────┘  │   • treasury += fees
                        │  3. appeal(id) [payable]  ── stake ×2/×4 ─▶│
                        │  4. finalize(id)  ── locks verdict forever │
                        └──────────────────────────────────────────┘
                                       │
                                       ▼  get_trust(subject) / get_trust_batch()
                        ┌───────────────────────────────┐
                        │  CONSUMERS (any dApp/agent)    │
                        │  wallets · marketplaces ·      │
                        │  x402 payers · agent frameworks│
                        └───────────────────────────────┘
```

## Why this shape

| Concern | Solution |
|---|---|
| Evidence can't be forged | The contract fetches every URL itself (`gl.nondet.web.request`); claimants only state *where* to look |
| Judgments, not keywords | `gl.nondet.exec_prompt` jury verdict with the canonical prompt (`prompts/jury_prompt.md`) |
| Consensus on non-determinism | `gl.vm.run_nondet_unsafe(leader, validator)` — validators check structure + categorical agreement, never exact strings |
| Spam / false claims | Stake `min_stake` (10 GEN); **CONTRADICTED → stake forfeited**, VERIFIED/PARTIAL → refund minus 5% fee |
| Wrong verdicts | 7-day deterministic appeal window, stake ×2 then ×4, then `finalize()` locks it |
| Cost control | Evidence truncated (6,000 chars/URL), max 5 URLs, fee caps in constructor |
| Prompt injection from evidence | Jury rules state evidence text is never instructions; leader/validators re-read the same prompt |
| Machine consumption | `get_trust` / `get_trust_batch` views → 0–100 score, counters, latest verdict label |

## Trust score model

```
score = 100 × (Σ weights) / total_verdicts        (clamped 5..100)
  VERIFIED        → 1.0
  PARTIALLY_VERIFIED → 0.5
  UNVERIFIABLE    → 0.25
  CONTRADICTED    → 0.0
neutral start: 50 ("no data" — never trust a subject with zero verdicts)
```

## Storage & types

`Claim` and `SubjectScore` are `@allow_storage @dataclass`es; maps are
`TreeMap[u256, Claim]` and `TreeMap[str, SubjectScore]` (no `dict`/`list` in
persistent state — GenVM requirement). All `gl.nondet.*` calls live inside the
non-deterministic block; **all** storage writes, transfers and status changes
happen after consensus returns (GenVM linter enforces this: `genvm-lint check`).

## Files

```
oath/
├── contracts/oath_registry.py   # THE contract (single file → Studio-ready)
├── prompts/jury_prompt.md       # canonical jury prompt spec (+ tuning knobs)
├── app/index.html               # single-file SPA: Pre-Flight · docket · case file · trust ledger · protocol
├── tools/offline_demo.py        # run the jury prompt locally w/ stdlib only
├── docs/SUBMISSION.md          # portal type 41 submission walkthrough
└── README.md
```

## Roadmap (beyond MVP)

1. **Level-2 committee:** rotate jury at appeal depth; weight verdicts by
   appeal count in the trust score.
2. **Rebuttals:** subjects can reply with counter-evidence before finalize.
3. **Registry of registries:** whitelisted primary sources (auditor registries,
   explorer APIs, certificate databases) get higher weight — mirrors how
   humans already adjudicate.
4. **Cross-chain trust API:** expose `get_trust` as an Intelligent Oracle-style
   responder so Base/ZKsync dApps can query without bridging.
5. **Claim templates:** structured claim types (audit-exists, tvl-claimed,
   agent-performance) with per-type prompts and evidence schemas.
6. **Governance:** adjust `fee_bps` / `min_stake` / source list via the
   builder council instead of redeploy.
