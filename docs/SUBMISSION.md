# Submitting OATH to the GenLayer Portal (Contribution Type 41)

Type 41 = **Projects**: *"Complete GenLayer apps, products, or platforms, where
GenLayer is central to the main workflow… one or more real Intelligent
Contracts, and app logic that actually interacts with GenLayer."*
Range **1–200 pts** (current multiplier 20×), AI-reviewed, escalates to the
Builder Council at 400 pts, max 2/week. A **GitHub repo is mandatory evidence.**

## The one-click evidence pack

| # | Evidence | URL format | Status |
|---|----------|-----------|--------|
| 1 | GitHub repo (required) | `https://github.com/<you>/oath` | ✔ must have |
| 2 | Deployed contract on explorer | `https://explorer...genlayer.com/address/0x…` | ✔ strong |
| 3 | Studio import link | `https://studio.genlayer.com/?...import-contract=0x…` | ✔ strong |
| 4 | X post w/ demo | `https://x.com/<you>/status/…` | ✔ cheap |
| 5 | YouTube short (60s demo) | `https://youtube.com/shorts/…` | optional boost |

Get **all five** — reviews weight evidence completeness, and the AI reviewer
checks that GenLayer is central, not a wrapper.

## What the reviewer is scoring (and how OATH answers it)

| Rubric axis | OATH answer |
|---|---|
| Real Intelligent Contracts | `oath_registry.py`: native web fetch + `exec_prompt` jury + Equivalence Principle consensus + appeal/finalize — none of this exists on EVM; it is *only* possible on GenLayer |
| GenLayer centrality | The whole product IS an Intelligent Contract; the web app is just a view |
| Use-case clarity | "Verify claims before you trust" — audit claims, agent capability claims, airdrop/tokenomics, compliance |
| Novelty vs ecosystem | No existing GenLayer project does evidence-fetching verdicts as a public registry (Internet Court = party arbitration; Rally = content scoring; MicroMarkets = prediction markets) |
| Usability / polish | `app/index.html` Pre-Flight UI, trust explorer, sample data |
| Docs & reproducibility | README + ARCHITECTURE.md + jury prompt spec + offline demo tool |
| Ecosystem value | A trust API the ecosystem's own projects query before transacting (drives decisions/day — GenLayer's own KPI) |

## Submission checklist

- [ ] `git init` the folder, push to GitHub, set description + topics + About URL
      (everything copy-paste ready in `docs/DEMO_SCRIPT.md` §1)
- [ ] Enable **GitHub Pages** → live demo URL (`docs/DEMO_SCRIPT.md` §4) — the
      single strongest evidence link; add it to the repo's About
- [ ] Deploy on **Bradbury** via Studio (import file, run `adjudicate` on a
      sample claim, screenshot the verdict, add the address to README)
- [ ] Write the submission description: 3 paragraphs — ready-to-paste version in
      `docs/DEMO_SCRIPT.md` §2 (audit → verdict → seal)
- [ ] Link the contract address (explorer) + Studio import link + repo + Pages
- [ ] X post: `docs/DEMO_SCRIPT.md` §3 (three variants) + attach the verdict clip
- [ ] 60s YouTube Short: shot list + VO in `docs/DEMO_SCRIPT.md` §5
- [ ] Submit; if AI review eschews to Council, say "appeal" in the summary if
      the feedback asks for something concrete — add it as a Milestone (type 47)
- [ ] Bonus: submit `prompts/jury_prompt.md` reasoning + contract snippets as a
      Documentation contribution (type 42) — separate category, extra points

## Points-maximizing tips

1. **Demonstrate the appeal path live** (claim → contradict → appeal → finalize)
   — reviewers explicitly reward depth over breadth.
2. **Show the trust score changing** across multiple verdicts; the score model
   is the part that makes it a protocol, not a page.
3. Keep evidence URLs in the submission (screenshots, txn hashes) — every
   portal review benefits from click-through proof.

## Files that make the repo review-friendly

- `README.md` — pitch, quickstart, API table
- `docs/ARCHITECTURE.md` — diagram + design rationale
- `prompts/jury_prompt.md` — the "product" explained
- `tools/offline_demo.py` — run the jury locally, no keys needed
