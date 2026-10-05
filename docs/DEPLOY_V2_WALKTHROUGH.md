# Deploy OATH v2 → Explorer → Milestone evidence (click-by-click)

Goal: a **fresh v2 deployment visible on the GenLayer explorer**, one complete
live loop (file → adjudicate → **finalize** → get_badge → **reverify** →
adjudicate), and the evidence links the milestone form wants.

Time: ~25 minutes. No coding. Same flow as your previous Studio deployment.

Explorer links (what "deployed to the explorer" means — the deployment shows
up automatically once the tx is mined):

| Network | Explorer URL | Notes |
|---|---|---|
| **GenLayer Studio network** (recommended) | `https://explorer-studio.genlayer.com/address/0x…` | chain 61999; what your app + previous deployments use |
| Bradbury testnet (CLI) | `https://explorer-bradbury.genlayer.com/address/0x…` | chain 4221, RPC `https://rpc-bradbury.genlayer.com` |

---

## Troubleshooting (learned from the first live v2 deploy, Sep 14 2026)

| Symptom (explorer → GenVM Execution) | Cause | Fix |
|---|---|---|
| `file_claim` rolls back with **`max 0 evidence URLs`** | The contract was deployed with `max_evidence = 0` — a Constructor Inputs field didn't land as typed (happened on the first real v2 deploy; every `file_claim` with ≥1 URL then reverts, and later `adjudicate` calls report `claim not found`) | Redeploy. Use the JSON constructor toggle and paste `[10000000000000000000, 500, 5, 0, 2, 0, 90]` so field mapping can't be wrong |
| `adjudicate` / `get_claim` roll back with **`claim not found`** | Nothing is filed yet — `claim_id 1` is *created by* a successful `file_claim`. If the filing rolled back, no claim exists | Fix the filing first (see above), then re-run `adjudicate` |
| "Did my 10 GEN get lost in a rolled-back `file_claim`?" | No — a rollback reverts all state; the value never left the wallet | Re-run the call on the fixed deployment |
| **How to self-debug any tx:** open it on the explorer and scroll to **GenVM Execution → Execution Result / Error Message** | The contract's own revert message tells you exactly which check failed | Match the message to the contract's `UserError` texts |

---

## 0 · Get the v2 contract file

The file to deploy is **`contracts/oath_registry.py`** on the milestone branch
(PR #1 / `arena/01a09b16-oath`, or `main` after merge). Download the repo as
ZIP from GitHub (Code → Download ZIP) or `git clone`, and open
`contracts/oath_registry.py` in **Notepad** → Ctrl+A → Ctrl+C.

> Sanity check before pasting: **line 1** must be the pinned runner comment
> `# { "Depends": "py-genlayer:1jb45…" }` and **line 2 must be a blank line**.
> Never copy the file from a rendered chat/preview — always from the raw file.

## 1 · Studio + address + faucet GEN

1. Open **https://studio.genlayer.com** (main page — not a `/run-debug` link).
2. In the network selector choose **"GenLayer Studio Network"** (so it deploys
   to the hosted network with the public explorer, not your local Docker VM).
3. Copy your account address from the header (`0x…`).
4. Faucet: **https://testnet-faucet.genlayer.foundation/** → paste the address
   → request. You need ≥ 30 GEN for this walkthrough (three 10-GEN stakes).

## 2 · Paste + deploy the v2 registry

1. **New Contract** → paste the whole file.
2. The **Constructor Inputs** pane must appear (if you see *"Could not load
   contract schema"* instead: line 2 isn't blank or the paste was mangled —
   see the troubleshooting section of `docs/DEPLOY_WALKTHROUGH.md`).
3. Constructor values — this milestone's evidence loop needs to finalize
   TODAY, so use the **fast-lane config**:

   | arg | value | why |
   |---|---|---|
   | `min_stake` | `10000000000000000000` | 10 GEN (default) |
   | `fee_bps` | `500` | 5% fee (default) |
   | `max_evidence` | `5` | default |
   | `max_appeals` | `0` | **fast-lane**: finalize immediately (no appeal wait) |
   | `appeal_multiplier` | `2` | default |
   | `appeal_window_days` | `0` | **fast-lane**: window closed at once |
   | `verdict_ttl_days` | `90` | **v2** — the freshness window |

4. Click **Deploy** → Studio shows the **contract address `0x…`** → copy it.

> Optional second deployment (only if you also want a production-config
> instance on the explorer): repeat with defaults (`max_appeals 2`,
> `appeal_window_days 7`). Its finalize will revert "appeal window still open"
> until time passes — that's correct behavior, not a bug.

## 3 · Run the live evidence loop (the transactions stewards can verify)

In the Studio playground **on the v2 deployment**. Do these in order and log
every tx (Step 4).

| # | Method | Field values | Expect |
|---|---|---|---|
| 1 | `file_claim` (payable) | `subject` = `iana.org` · `claim_text` = `The Internet Assigned Numbers Authority operates the iana.org domain as the authoritative registry for root zone and protocol parameters.` · `evidence_json` = `["https://www.iana.org/about"]` · `category` = `compliance` · **Value (GEN)** = `10` | returns claim id **n** (e.g. `1`) |
| 2 | `adjudicate` | `claim_id` = `n` | verdict lands in 30–90s (compliance category = issuer-register rules in the jury prompt) |
| 3 | `get_verdict` | `claim_id` = `n` | verdict + rationale + citations → **screenshot** |
| 4 | `finalize` | `claim_id` = `n` | returns `FINALIZED` |
| 5 | `get_claim` | `claim_id` = `n` | `finalized_at` set · `verified_until` ≈ **+90 days** · `fresh: true` → **screenshot** |
| 6 | `get_badge` | `subject` = `iana.org` | `schema oath.badge.v1` · grade `A` · color · `svg: <svg…>` → **screenshot** |
| 7 | `reverify` (payable) | `claim_id` = `n` · **Value (GEN)** = `10` | returns new claim id **m**, `reverified_from` = `n` |
| 8 | `adjudicate` | `claim_id` = `m` | fresh jury over the same claim — the freshness loop, live |

Also check `get_trust("iana.org")` — the score is now time-decayed on-chain,
and `get_stats()` shows `claims_reverified: 1` plus the `verdict_ttl_days`
knob. These two screenshots round out the story.

## 4 · Collect the explorer links (fill in as you go)

Open `https://explorer-studio.genlayer.com/address/<YOUR_V2_ADDRESS>` — your
contract, its methods and its transaction history are all there. Copy each tx
link from the explorer's transaction list (right-click → copy link).

```text
EVIDENCE LOG — OATH v2 (fill in)
--------------------------------
v2 contract address : 0x____________________________
network             : GenLayer Studio network (61999)
explorer (contract) : https://explorer-studio.genlayer.com/address/0x____
studio import link  : https://studio.genlayer.com/?import-contract=0x____
file_claim (n)      : tx 0x____
adjudicate (n)      : tx 0x____
finalize (n)        : tx 0x____
get_badge (read)    : screenshot ____ .png
reverify (m)        : tx 0x____
adjudicate (m)      : tx 0x____
```

## 5 · Point the world at the v2 registry

1. `app/index.html` → line ~442: `const DEFAULT_CONTRACT = '0x<v2 address>';`
2. `cp app/index.html index.html` (keep the Pages copy byte-identical).
3. Fill the same address + claim ids into `docs/MILESTONE_V1.md` §5, and swap
   the placeholders into the Version A submission text (§6).
4. Commit + push, wait ~1 min, then verify **https://timmyspurs12.github.io/OATH/**
   loads the v2 docket: category chips (`COMPLIANCE`), the FRESH badge +
   "verified until" date on case `n`, and the REVERIFY flow reachable.
   (You can also preview instantly with `?contract=0x<v2>` on the live URL.)
5. Pushing from this workspace needs a fresh coding session (this one's GitHub
   access is closed) — or push from your machine: download the changed files
   (`app/index.html`, `index.html`, `docs/MILESTONE_V1.md`), copy them over a
   `git clone` of your repo, `git add -A && git commit -m "v2 deployment" && git push`.

## 6 · (Optional, 5 min) Show the agent stack reading the live registry

```bash
pip install genlayer-py            # Python 3.12+
set OATH_ADDRESS=0x<v2 address>
python tools/agent_example.py      # live trust gate against your deployment
```

Screenshot the gate output → one more evidence link ("real integration").

## 7 · Submit the milestone

Portal → Milestones → paste **Version A** from `docs/MILESTONE_V1.md` §6
(real address/ids), evidence links in the §6 order: PR #1 →
`docs/MILESTONE_V1.md` → live app → explorer contract → explorer txs.
