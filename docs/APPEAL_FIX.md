# OATH — Appeal: frontend now implements the documented GenLayer read/write flow

**Rejection feedback addressed:** *"The submitted app simulates filings,
verdicts, appeals, and on-chain records without calling the contract. Implement
the documented GenLayer read/write flow against OathRegistry and derive
displayed state from contract views instead of local demo data."*

That feedback was correct for the submitted build. It has now been fixed in
`app/index.html` (and the byte-identical GitHub-Pages root `index.html`).

## What was wrong

The frontend shipped a `DemoClient`: a hard-coded 14-case docket
(`CASES = [...]`), a `runDemoFiling()` that generated a random verdict locally,
`submitAppeal()` that flipped a local status flag, fabricated evidence HTTP
200/404 chips, and computed trust scores from the local array. None of it called
the deployed `OathRegistry`.

## What changed (the fix)

The frontend is now **live-first and contract-backed**, using the exact
[GenLayerJS](https://docs.genlayer.com/api-references/genlayer-js) flow from the
official docs (read client with no wallet; write client with an EIP-1193
wallet; wait for `FINALIZED`; check the execution result; then re-read state).

**Reads — the source of truth for everything on screen:**
- `get_claim(1…N)` discovers the docket deterministically (reads ids until the
  first `claim not found`; `next_id` is monotonic and claims are never deleted).
- `get_verdict(claim_id)` / `get_claim` drive the case file (status, verdict,
  confidence, rationale, citations, appeal count, timestamps, requester).
- `get_trust(subject)` and `get_trust_batch(subjects_json)` drive the wax-seal
  trust scores, run-rate breakdown and ledger history.
- `get_stats()` drives the rail counters (filed / adjudicated / contradicted /
  treasury) and the minimum stake + fee shown on the filing form.

**Writes — real transactions through a wallet on GenLayer Bradbury:**
- `file_claim(subject, claim_text, evidence_json)` — payable, `value` = the
  minimum stake read from the contract (default `10n * 10n ** 18n` GEN).
- `adjudicate(claim_id)` — runs the on-chain jury (native web fetch + LLM
  consensus); the app only waits and then re-reads the resulting verdict.
- `appeal(claim_id)` — payable; the required stake is **derived from the
  contract**, not hard-coded: `stake × appeal_multiplier^(appeal_count+1)`
  (×2, then ×4), matching `OathRegistry.appeal`.
- `finalize(claim_id)` — respects the contract's appeal-window rules.
- Every write waits for `TransactionStatus.FINALIZED` and verifies
  `receipt.txExecutionResultName === ExecutionResult.FINISHED_WITH_RETURN`
  before refreshing; on `FINISHED_WITH_ERROR` it reports that state was not
  changed. There are no optimistic local mutations.

**Wallet / network:**
- SDK imported as an ESM browser bundle
  (`https://esm.sh/genlayer-js@1.1.8` + `/types`) — no build step, works on
  GitHub Pages.
- Reads: `createClient({ chain: testnetBradbury })` (no wallet).
- Writes: `createClient({ chain: testnetBradbury, account, provider:
  window.ethereum })`, then `client.connect('testnetBradbury')`, with an
  EIP-1193 `wallet_switchEthereumChain` / `wallet_addEthereumChain` fallback for
  chain id **4221** (`https://rpc-bradbury.genlayer.com`, explorer
  `https://explorer-bradbury.genlayer.com`).

**No fabricated fields.** The contract does not persist a claim-type field or
evidence HTTP status/content. Instead of inventing them, the live UI labels
cases `PUBLIC CLAIM` and exhibits `ON-CHAIN EVIDENCE`. The old seeded records,
random verdict generator, fake 200/404 chips, fake appeal log and local trust
math were all deleted. `tools/offline_demo.py` remains an isolated developer
utility and is not used by the frontend.

**Configuration (static build, no env vars):** open the app with
`?contract=0x<deployed OathRegistry>` or use **CONFIGURE CONTRACT** in the rail;
the address is persisted to `localStorage`. Reads work without a wallet; writes
prompt for a wallet holding testnet GEN (faucet:
https://testnet-faucet.genlayer.foundation/).

## How to verify

1. Open the GitHub Pages app with a deployed contract:
   `https://<user>.github.io/OATH/?contract=0x<OathRegistry address>`
   (or deploy `contracts/oath_registry.py` in GenLayer Studio / via
   `genlayer-cli` to Bradbury and paste the address).
2. **Docket / ledger / rail counters populate from contract views** with no
   wallet connected.
3. Connect MetaMask (Bradbury chain 4221, GEN from the faucet) → file a claim →
   the wallet signs `file_claim` with the 10 GEN stake; the case appears as
   `PENDING` from `get_claim`.
4. Open the case → **RUN JURY** → `adjudicate` runs consensus; the verdict
   stamp, confidence, transcript and citations all come back from
   `get_verdict`/`get_claim`, and the subject's seal updates from `get_trust`.
5. **Submit appeal** shows the contract-derived stake (×2 = 20 GEN, ×4 = 40
   GEN); after appeal + re-adjudicate, **Finalize** locks the record (`FINAL`).
6. Cross-check any value against the explorer:
   `https://explorer-bradbury.genlayer.com/address/<contract>`.

## Files

- `app/index.html` / `index.html` — live GenLayerJS frontend (demo client removed).
- `contracts/oath_registry.py` — the OathRegistry Intelligent Contract (unchanged; already deployed/deployable).
- `docs/FRONTEND_BRIEF.md` — updated with the live-integration status note.
