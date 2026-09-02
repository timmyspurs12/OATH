# Update GitHub + fill the GenLayer Project Explorer form

## Part 1 — One-time setup on Windows (Git Bash)

You need Git (includes Git Bash + a credential helper that logs into GitHub in
your browser, no SSH keys or tokens to copy).

1. Download Git for Windows: https://git-scm.com/download/win → install (all
   defaults are fine). This gives you **Git Bash**.
2. The fixed files are in your Arena workspace (the folder `OATH`). Download
   them from the workspace so you have the folder locally, e.g. `C:\Users\<You>\Downloads\OATH`.
   The files that changed are: **`app/index.html`** (the live app),
   **`index.html`** (repo-root Pages copy — keep it byte-identical to
   `app/index.html`), **`README.md`**, and the **`docs/`** notes.

## Part 2 — Update the GitHub repo

Open **Git Bash** and run these (line by line). Replace `C:/Users/<You>/Downloads/OATH`
with where you actually saved the fixed folder:

```bash
# 1) Download your existing repo (you only do this once)
cd ~/Downloads
git clone https://github.com/timmyspurs12/OATH.git OATH-live
cd OATH-live

# 2) Copy the fixed files over it (from the workspace download), then:
cp ~/Downloads/OATH/app/index.html        app/index.html
cp ~/Downloads/OATH/index.html            index.html
cp ~/Downloads/OATH/README.md             README.md
cp ~/Downloads/OATH/docs/APPEAL_FIX.md    docs/APPEAL_FIX.md
cp ~/Downloads/OATH/docs/FRONTEND_BRIEF.md docs/FRONTEND_BRIEF.md

# sanity: the root copy and the app copy must be identical
cmp app/index.html index.html && echo "OK - copies match"

# 3) Stage, commit, push (first push opens a browser to authorize GitHub)
git add -A
git commit -m "Frontend: live GenLayerJS read/write flow against OathRegistry (no demo data)"
git push origin main
```

> If `git push` asks for a login: enter your GitHub **username** and a
> **personal-access-token** as the password, OR (easiest) install
> **GitHub CLI** from https://cli.github.com and run `gh auth login` once —
> Git Bash then pushes without asking.

GitHub Pages auto-rebuilds in ~1 minute. Verify: open
**https://timmyspurs12.github.io/OATH/** — it should load straight into the live
app showing the real on-chain case (no "demo records" banner, no seeded list).
The top-right badge should read **GENLAYER STUDIO · LIVE** with a green dot.

## Part 3 — (Recommended, strengthens the appeal) run one fresh real verdict

The reviewer clicks the live app and the Studio explorer. A fresh file →
adjudicate shows the whole path end-to-end.

1. Open the live app → **CONNECT WALLET** (MetaMask). It will offer to add the
   GenLayer Studio network (chain **61999**, RPC https://studio.genlayer.com/api).
   Studio GEN is free via the 💧 faucet inside GenLayer Studio (your address).
2. Pre-flight: subject + a ≥20-char claim + a reachable evidence URL → **FILE
   CASE** (10 GEN) → then open the case → **RUN JURY**. The verdict, confidence,
   transcript and seal all come back from the contract.
3. Copy the new transaction hash shown (and the contract address) for the form.

---

## Part 4 — What to type in each portal box

### 01 Identity (already fine — keep it)
- **Project name:** `OATH — Claim Verification Protocol`
- **Primary tag:** `AI & Agents`
- **Tag 1 / Tag 2:** keep `AI Policy Enforcement` + `Source Verification`
- Logo: optional (you can upload the `GL`-style or any 128–2048px PNG).

### 03 Description — "What is this project?" (≤1000 chars)

```
OATH verifies publicly-checkable claims ("this dApp is audited", "this agent finished 10k tasks", "this vendor is carbon-neutral") by doing the checking itself, on GenLayer. Anyone stakes 10 GEN and files a claim with evidence URLs; the Intelligent Contract fetches that evidence natively (no oracle), an LLM jury renders a verdict — VERIFIED / PARTIALLY_VERIFIED / CONTRADICTED / UNVERIFIABLE — with confidence, rationale and citations written on-chain, and a per-subject trust score any agent can query with get_trust(). Verdicts are appealable at stake ×2 then ×4 within 7 days, then finalized; a CONTRADICTED claim forfeits its stake.

The web app is now fully wired to the deployed contract via genlayer-js (createClient on the Studio network). Every case, verdict, trust score and counter on screen is read from contract views — get_claim, get_verdict, get_trust, get_trust_batch, get_stats — and filing, adjudicate, appeal and finalize are real, wallet-signed writeContract calls that wait for FINALIZED and re-read state. There is no demo data and nothing is simulated.
```
(≈960 chars.)

### 05 How-to — write the exact path (replace the old steps)

**Step 1 — heading:** `Open the live app`
**Instruction:**
```
Visit https://timmyspurs12.github.io/OATH/ — the app loads already connected to the deployed OathRegistry (0xe9B73DD18446a1f121090a21C544D51349a1e8Ad) on the GenLayer Studio network. The Docket, Trust Ledger and the rail counters are all read live from the contract; case #1 ("CertiK audits top blockchain projects") is shown with its on-chain verdict — no demo data.
```

**Step 2 — heading:** `Read a verdict on-chain`
**Instruction:**
```
Open the contract in the explorer: https://explorer-studio.genlayer.com/address/0xe9B73DD18446a1f121090a21C544D51349a1e8Ad — then open the FINALIZED adjudicate transaction and inspect its GenVM result: verdict PARTIALLY_VERIFIED, confidence 71, with rationale and citation(s). In the app, open Docket → Case #0001 to see the same verdict, confidence and jury transcript rendered from get_claim/get_verdict.
```

**Step 3 — heading:** `Query the trust API`
**Instruction:**
```
In the app go to Trust Ledger and type certik into the get_trust("…") scan bar — the seal score and VERIFIED/PARTIAL/CONTRADICTED/UNVERIFIABLE breakdown come from get_trust/get_trust_batch. Or open https://studio.genlayer.com/?import-contract=0xe9B73DD18446a1f121090a21C544D51349a1e8Ad and call get_trust("certik") yourself.
```

**Step 4 (optional, only if you ran Part 3) — heading:** `File and adjudicate a live claim`
**Instruction:**
```
Connect MetaMask (the app adds the GenLayer Studio network, chain 61999), file a claim with a real evidence URL and the 10 GEN stake, then open the case and press RUN JURY. The contract fetches the URL, runs the LLM jury to consensus, and the app shows the returned verdict after the transaction reaches FINALIZED — proving the full write path end to end.
```

### 06 Review verification — expected outcome (≤500 chars)

```
Following the steps, a steward sees the live OATH app at https://timmyspurs12.github.io/OATH/ already reading the deployed contract 0xe9B73DD18446a1f121090a21C544D51349a1e8Ad on the GenLayer Studio network: the Docket and Trust Ledger render state from get_claim/get_verdict/get_trust/get_stats with zero demo data. In the Studio explorer the FINALIZED adjudicate transaction shows GenVM result PARTIALLY_VERIFIED, confidence 71, rationale + citation — matching the verdict shown in the app. Filing and RUN JURY are real wallet-signed writeContract calls that wait for FINALIZED and re-read state.
```
(≈480 chars.)

### Evidence & supporting information
- **REQUIRED GitHub repo:** `https://github.com/timmyspurs12/OATH`
- **Add — live app (label "Other"):** `https://timmyspurs12.github.io/OATH/`
- **Keep — contract on explorer (label as "Contract"/address link):**
  `https://explorer-studio.genlayer.com/address/0xe9B73DD18446a1f121090a21C544D51349a1e8Ad`
- **Keep — the FINALIZED adjudicate tx (currently labelled "Other"; relabel to a contract/transaction type if the portal offers one):**
  `https://explorer-studio.genlayer.com/tx/0x54c722554c65435e9cf9cf1e0927304…` and the second tx you already added.
- If you ran Part 3, add the **new** transaction and contract links too.
