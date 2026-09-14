# Deploy OATH v2 + collect milestone evidence

Everything in this walkthrough uses **GenLayer Studio** in the browser — same
flow as the original deployment, ~20 minutes total. Do the steps in order and
fill in `docs/MILESTONE_V1.md` §5 as you go.

> The v2 contract is a **fresh deployment** (it adds storage fields). Leave
> the original v1 registry running; its cases and trust scores stay intact.

## 0 · Get the v2 code onto your machine

```bash
git clone https://github.com/timmyspurs12/OATH.git OATH-v2 && cd OATH-v2
# use the milestone branch if the PR isn't merged yet:
#   git checkout <milestone-branch>
```

The contract to deploy is `contracts/oath_registry.py`.

## 1 · Deploy the v2 registry (main deployment — production defaults)

1. Open <https://studio.genlayer.com> → **New contract** → paste
   `contracts/oath_registry.py` (or import from GitHub).
2. Constructor defaults are the v2 production config
   (`min_stake 10 GEN, fee 5%, max 5 evidence, 2 appeals, ×2 multiplier,
   7-day window, **verdict_ttl_days 90**`) → **Deploy**.
3. Copy the new address → **this is the v2 registry**.
   - Fill it into `docs/MILESTONE_V1.md` §5 and the submission text.
   - Update the app default: `app/index.html` line with
     `const DEFAULT_CONTRACT = '0x…'` → your v2 address, then
     `cp app/index.html index.html` and push.

## 2 · Run the full loop live (the evidence transactions)

In the Studio playground **on the v2 deployment**, with faucet GEN
(<https://testnet-faucet.genlayer.foundation/>):

| Step | Call | Expected |
|------|------|----------|
| 1 | `file_claim("example.com", "Example.com is operated by the Internet Assigned Numbers Authority and displays its official documentation.", ["https://www.iana.org/"], "compliance")` + 10 GEN | returns new claim id `n` |
| 2 | `adjudicate(n)` | verdict stamped (30–90s consensus) |
| 3 | `get_verdict(n)` | verdict + rationale + citations |
| 4 | `finalize(n)` | `"FINALIZED"` — trust settled |
| 5 | `get_claim(n)` | `finalized_at` + `verified_until` ≈ +90 days, `fresh: true` |
| 6 | `get_badge("example.com")` | `schema oath.badge.v1`, grade A, SVG |
| 7 | `reverify(n)` + 10 GEN | returns new claim id `m`, `reverified_from = n` |
| 8 | `adjudicate(m)` | fresh jury run linked to the old case |

> For the **fast-lane demo deployment** (finalize immediately instead of
> waiting 7 days): deploy a second instance with `appeal_window_days = 0` and
> `max_appeals = 0`, and repeat steps 1–8 there. Keep the 7-day deployment as
> the "main" one.

For each step, screenshot or copy the **transaction hash / explorer link**.
Five links (file, adjudicate, finalize, badge read, reverify) are plenty.

## 3 · Show the agent stack reading the live registry

```bash
pip install genlayer-py          # Python 3.12+
export OATH_ADDRESS=0x<v2-address>

# trust-gated agent, live reads
python tools/agent_example.py --min-score 70

# MCP server (plug into Claude Desktop / Cursor config)
python tools/mcp_server.py
```

Screenshot the agent gate output — that's the "real integration" evidence.

## 4 · Update the repo (so stewards see everything in one place)

- [ ] `DEFAULT_CONTRACT` in `app/index.html` = v2 address; `cp app/index.html index.html`
- [ ] `docs/MILESTONE_V1.md` §5 filled in (address, network, explorer links, claim ids)
- [ ] README "Deploy" section: note the v2 constructor knob `verdict_ttl_days`
- [ ] Commit + push; verify <https://timmyspurs12.github.io/OATH/> shows the
      v2 docket (category chips on cases, FRESH/STALE on finalized verdicts)
- [ ] Run the test suites and paste the summary into the PR description:
      `pytest tests/pure -v` (54 passed) and, with the GenLayer toolchain,
      `pytest tests/direct -v`

## 5 · Submit the milestone

Portal → Milestones (type 47), using the text in
`docs/MILESTONE_V1.md` §6 with your real address/claim ids. Evidence links:
explorer txs, the live app, and this repo's `docs/MILESTONE_V1.md`.
