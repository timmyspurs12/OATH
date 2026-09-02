<div align="center">

# ⚖️ OATH
### The Claim Verification Protocol · an Intelligent Contract for GenLayer

*Machine-queryable truth for the agentic economy — evidence-fetching, jury-adjudicated, appealable verdicts on claims, in minutes, on-chain.*

[Contracts](#the-contract) · [Jury](#the-jury) · [App](#the-app) · [Deploy](#deploy) · [Submit](docs/SUBMISSION.md)

</div>

---

## What it does

OATH verifies **publicly checkable claims** — *"this dApp is audited"*, *"this
agent completed 10k tasks"*, *"this vendor is certified carbon-neutral"* — by
doing the checking itself:

1. A claimant files a claim + evidence URLs + a **stake** (10 GEN).
2. The Intelligent Contract **fetches every evidence URL itself** (native web
   access — no oracle, no cron, no photoshopping).
3. A leader validator + peer validators run the same **jury prompt** on diverse
   LLMs and reach consensus (Equivalence Principle).
4. The verdict — `VERIFIED / PARTIALLY_VERIFIED / CONTRADICTED / UNVERIFIABLE`
   + confidence + rationale + citations — is written on-chain and **updates a
   trust score** for the subject.
5. Any party can **appeal** within 7 deterministic days (stake ×2, ×4), then
   **finalize** to lock the verdict. Filing a claim that gets CONTRADICTED
   **loses the stake** — false claims are expensive.

Any wallet, agent, marketplace or x402 payer can then call
`get_trust(subject)` before transacting. **One call replaces "DYOR".**

## Why GenLayer (why not EVM)

| OATH needs | GenLayer primitive |
|---|---|
| Contract fetches live evidence | `gl.nondet.web.request(…)` native web access |
| Judgment, not keyword-matching | `gl.nondet.exec_prompt(…, response_format='json')` |
| Consensus over non-determinism | `gl.vm.run_nondet_unsafe(leader, validator)` |
| Appealable, time-boxed verdicts | deterministic txn timestamps |
| Stakes & slashing | `@gl.public.write.payable` + `emit_transfer` |

## Repo layout

```
oath/
├── contracts/oath_registry.py    # THE Intelligent Contract (single file, Studio-ready)
├── prompts/jury_prompt.md        # canonical jury prompt + tuning knobs
├── app/index.html                # single-file SPA (see "The app" below)
├── tools/offline_demo.py         # run the jury prompt locally, no keys
├── docs/ARCHITECTURE.md          # diagram + design rationale
└── docs/SUBMISSION.md            # portal type-41 submission walkthrough
```

## The contract — public API

| Method | Kind | Purpose |
|---|---|---|
| `file_claim(subject, claim_text, evidence_json)` | write·payable | file a claim, stake GEN (`evidence_json` is a JSON array string of URLs) |
| `adjudicate(claim_id)` | write | run the jury (web + LLM + consensus), settle stake, update trust |
| `appeal(claim_id)` | write·payable | re-jury with higher stake (×2, ×4) |
| `finalize(claim_id)` | write | lock verdict after appeal window |
| `get_claim(claim_id)` | view | full claim record |
| `get_verdict(claim_id)` | view | verdict + rationale + citations |
| `get_trust(subject)` | view | **the trust score** (0–100, 50 = no data) |
| `get_trust_batch(subjects_json)` | view | batch scores (JSON array string in, JSON string out) |
| `get_stats()` | view | counters + treasury |

Constructor knobs: `min_stake`, `fee_bps`, `max_evidence`, `max_appeals`,
`appeal_multiplier`, `appeal_window_days`.

## Deploy

### Option A — GenLayer Studio (fastest, recommended)

**Follow the full step-by-step (address → faucet → deploy → file → jury →
verdict → evidence links): `docs/DEPLOY_WALKTHROUGH.md`.**

1. Open [studio.genlayer.com](https://studio.genlayer.com)
2. New contract → paste / import `contracts/oath_registry.py`
3. Constructor defaults are fine → **Deploy** (testnet GEN from the faucet)
4. In the playground: `file_claim` with a subject + claim + evidence URL
   (e.g. paste any live page), then `adjudicate(<claim_id>)`
5. Watch the verdict land. Copy the contract address.

### Option B — CLI

```bash
npx genlayer-cli env up            # local network
npx genlayer-cli contracts deploy contracts/oath_registry.py
npx genlayer-cli contracts call <addr> file_claim --arg '...'
npx genlayer-cli contracts call <addr> adjudicate --arg '<claim_id>'
```

Configure a testnet network (Bradbury) in `genlayer-cli config` to deploy
there — see [network config docs](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration).

> Note: line 1 of the contract is a runner pin:
> `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }`
> (hash pin works in Studio AND production — verified against
> `studio.genlayer.com/api`). Line 2 MUST be a blank line: GenVM glues every
> comment line directly after the runner comment into the runner JSON, so the
> doc banner must not touch line 1. (`py-genlayer:test` is a local-debug-only
> alias that the Studio backend rejects.)

## The app

**`app/index.html`** — the OATH frontend, a single self-contained file (no build
step, no framework). Open it directly, or serve the folder
(`python3 -m http.server`), or ship it as-is.

> **GitHub Pages entry point:** the repo root also carries `index.html` (a
> byte-identical copy of `app/index.html`) plus `.nojekyll`, so
> `https://<you>.github.io/OATH/` serves the styled app directly. Keep the two
> copies in sync after any frontend edit (`cp app/index.html index.html`).
> Without the root `index.html`, Pages renders the README instead of the app.

It is a **live, contract-backed** hash-routed SPA. It ships **no seeded cases**
and **simulates nothing** — every case, verdict, trust score, counter and status
on screen is read from the deployed OathRegistry via the documented
[GenLayerJS](https://docs.genlayer.com/api-references/genlayer-js) read/write
flow against GenLayer **Bradbury** testnet.

| Route | Screen | Contract source |
|---|---|---|
| `#/preflight` | File a case: subject, claim, Exhibit A–E evidence rows; the board explains the on-chain fetch → jury → stamp → seal flow | `file_claim` (payable, min stake from `get_stats`) |
| `#/docket` | Sortable/filterable ledger of every case | discovered from `get_claim(1…N)` until the first missing id; counters from `get_stats()` |
| `#/case/:id` | Case file: verdict stamp, exhibits, typewriter jury transcript + citations, RUN JURY / appeal (×2/×4) / finalize | `get_claim` · `get_verdict` · `adjudicate` · `appeal` · `finalize`; seal from `get_trust` |
| `#/ledger` | Trust explorer: `get_trust("…")` scan bar, wax-seal score, run-rate breakdown, subject history | `get_trust` · `get_trust_batch` |
| `#/protocol` | The three pillars, decision-tree SVG, verdict taxonomy, on-chain API table, FAQ | — |

**GenLayerJS flow (exactly as documented):**

```js
// reads — no wallet needed
const { createClient, testnetBradbury } = await import('genlayer-js');
const readClient = createClient({ chain: testnetBradbury });
const trust = await readClient.readContract({
  address: OATH_ADDRESS, functionName: 'get_trust', args: [subject], stateStatus: 'accepted',
});

// writes — EIP-1193 wallet (MetaMask) on Bradbury
const writeClient = createClient({ chain: testnetBradbury, account, provider: window.ethereum });
await writeClient.connect('testnetBradbury');                 // adds/switches chain 4221
const tx = await writeClient.writeContract({
  address: OATH_ADDRESS, functionName: 'file_claim',
  args: [subject, claimText, JSON.stringify(evidenceUrls)],
  value: 10n * 10n ** 18n,                                    // 10 GEN minimum stake
});
const receipt = await writeClient.waitForTransactionReceipt({
  hash: tx.transactionHash, status: TransactionStatus.FINALIZED,
});
// receipt.txExecutionResultName must === ExecutionResult.FINISHED_WITH_RETURN,
// then the app RE-READS state from contract views (no optimistic local records).
```

- **Configuration is runtime-only** (no build step for GitHub Pages). The app
  ships pre-pointed at the deployed **Studio-network** contract
  `0xe9B73DD18446a1f121090a21C544D51349a1e8Ad`, so opening
  `https://timmyspurs12.github.io/OATH/` immediately shows the live docket
  (case #1: *"CertiK audits top blockchain projects"* → PARTIALLY_VERIFIED, 71).
  Switch **STUDIO / BRADBURY** from the left rail, or open with
  `?network=bradbury&contract=0x…`; the network and address persist to
  `localStorage`. Reads work with no wallet; the wallet is only requested for
  writes (on Studionet MetaMask uses chain 61999, RPC `https://studio.genlayer.com/api`;
  on Bradbury chain 4221).
- **Source-of-truth rule:** the UI never invents state. The contract does not
  persist a claim-type field or evidence HTTP status/content, so the live UI
  labels cases `PUBLIC CLAIM` and exhibits `ON-CHAIN EVIDENCE` rather than
  fabricating values.
- **Appeal stake is derived from the contract**, not hard-coded: the extra stake
  = `stake × appeal_multiplier^(appeal_count+1)` (×2 then ×4), matching
  `OathRegistry.appeal`.
- **Design system** per `docs/FRONTEND_BRIEF.md` §3: ink/paper palette, Fraunces +
  IBM Plex Mono, ink-stamp verdicts, wax-seal scores, paper grain, wire ticker.
  Fonts load from Google Fonts with `Georgia`/`ui-monospace` fallbacks.
- `tools/offline_demo.py` remains an isolated developer utility for previewing
  the jury prompt; it is **not** imported or used by the frontend.

## The jury (the actual product)

The verdict quality lives in the prompt. `prompts/jury_prompt.md` documents:

- the exact prompt the contract sends (`_build_prompt`),
- the four verdict classes and their meaning,
- evidence hygiene: truncation, dead-link semantics, primary-source preference,
- prompt-injection defense (instructions inside evidence are data, never
  instructions),
- the validator's structure + categorical-agreement rules (never exact-match,
  per GenLayer's non-determinism guidance).

## Demo it locally

```bash
python3 tools/offline_demo.py https://example.com https://example.org
# → prints the exact jury prompt; pipe into any local LLM
```

## License

MIT — build on it, fork it, submit it.

<p align="center"><i>Built for the GenLayer Portal — Contribution Type 41 (Projects). See <a href="docs/SUBMISSION.md">docs/SUBMISSION.md</a> for the submission pack.</i></p>
