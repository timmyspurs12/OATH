# Run a fresh live claim (new transaction for the reviewers)

Goal: produce a brand-new `file_claim` + `adjudicate` transaction on your
**already-deployed** OathRegistry, then see it appear in the live GitHub Pages
app. That proves the app reads real chain state it could never have hard-coded.
~10 minutes, no coding.

Your deployed contract (Studio network):
`0xe9B73DD18446a1f121090a21C544D51349a1e8Ad`
Explorer: https://explorer-studio.genlayer.com/address/0xe9B73DD18446a1f121090a21C544D51349a1e8Ad

> Pre-req: the updated app is already pushed and live —
> https://timmyspurs12.github.io/OATH/ shows the green **GENLAYER STUDIO · LIVE**
> badge and case #0001 (`certik`).

---

## Step 1 — Open your contract in GenLayer Studio

1. Go to **https://studio.genlayer.com**.
2. In the top network selector choose **"Genlayer Studio Network"** (the hosted
   network) — **not** local. This is the same network as explorer-studio where
   your contract lives.
3. Open this import link (it loads the deployed contract with its methods):

   **https://studio.genlayer.com/?import-contract=0xe9B73DD18446a1f121090a21C544D51349a1e8Ad**

   (or: Import contract by address → paste the address).
4. Check the account in the header (`0x…`). Studio wallet flows are gasless; if
   a call needs the 10 GEN stake and you don't have it, use the 💧 faucet in the
   account selector, or paste that address into
   https://testnet-faucet.genlayer.foundation/. (The stake is refunded for a
   VERIFIED/PARTIAL/UNVERIFIABLE result; only CONTRADICTED forfeits it.)

## Step 2 — File a fresh claim (`file_claim`, payable)

Under **Write methods → file_claim**, enter exactly:

- **subject**:
  ```
  ethereum.org
  ```
- **claim_text** (must be ≥ 20 characters — this one is self-evidently true, so
  the jury should return VERIFIED/PARTIAL and your stake is refunded):
  ```
  Ethereum.org is the official public website and resource hub for the Ethereum protocol and its community.
  ```
- **evidence_json** (a JSON array, double quotes, one line):
  ```
  ["https://ethereum.org/en/"]
  ```
- **Value (GEN)**: `10`

Click **Execute**; approve the signature if prompted. It returns the new case id
— expected **2** (the next id after `certik`). Copy the **transaction hash**.

> Want a CONTRADICTED example too (shows stake slashing)? Repeat with subject
> `fake-audit-demo.xyz`, claim_text "This protocol was audited by CertiK in 2026
> and the audit report is public.", evidence_json
> `["https://example.com/this-audit-does-not-exist"]`, value 10 → adjudicate →
> it should come back CONTRADICTED.

## Step 3 — Run the jury (`adjudicate`)

- **Write methods → adjudicate** → **claim_id** = the id returned above (`2`) →
  **Execute**.
- The contract now fetches the evidence URL itself and runs the LLM jury to
  consensus on the hosted network — this takes **~30–90 seconds**. Wait for it
  to finalize.
- It returns the verdict label (e.g. `VERIFIED` / `PARTIALLY_VERIFIED`). Copy
  this **transaction hash** too.
- If it returns `ADJUDICATION_FAILED`: that's transient (consensus timeout) —
  check `last_error` via `get_claim` and just run **adjudicate** again.

## Step 4 — Verify on the explorer

Open the contract on the explorer:
https://explorer-studio.genlayer.com/address/0xe9B73DD18446a1f121090a21C544D51349a1e8Ad

- You'll see the two new transactions. Open the **adjudicate** tx → its GenVM
  result shows the verdict, confidence, rationale and citation.
- Call **get_stats** (view method in Studio) → it now reads
  `claims_filed: 2, claims_adjudicated: 2`.

## Step 5 — Watch it appear in the live app (the money shot)

1. Go to **https://timmyspurs12.github.io/OATH/** and hard-refresh
   (Ctrl+Shift+R).
2. **Docket** → case **#0002** (`ethereum.org`) is now listed from `get_claim`
   discovery. Open it → the verdict stamp, confidence and jury transcript are
   rendered from `get_claim`/`get_verdict`.
3. **Trust Ledger** → type `ethereum.org` into the `get_trust("…")` bar → the
   seal score and verdict breakdown come back from the contract.

This is state that did not exist when you were reviewed — and the app displays
it with no demo data.

## Step 6 — Add to the portal evidence

- New `file_claim` tx: `https://explorer-studio.genlayer.com/tx/<file_hash>`
- New `adjudicate` tx: `https://explorer-studio.genlayer.com/tx/<adjudicate_hash>`
- Contract: `https://explorer-studio.genlayer.com/address/0xe9B73DD18446a1f121090a21C544D51349a1e8Ad`
- Live app: `https://timmyspurs12.github.io/OATH/`
- Screenshot the app showing case #0002.

---

### Optional — do it from the app itself (proves the app's own write buttons)

Instead of Steps 2–3 in Studio, you can file from the live app:

1. Install **MetaMask**. In the app click **CONNECT WALLET**; it prompts to add
   the GenLayer **Studio** network (chain id **61999**, RPC
   `https://studio.genlayer.com/api`) — approve.
2. Make sure that MetaMask account holds Studio GEN (faucet above).
3. Pre-flight → fill subject/claim/one evidence URL → **FILE CASE** (sign the
   10 GEN stake) → open the case → **RUN JURY**. The app waits for FINALIZED and
   re-reads state automatically.

If MetaMask funding on Studio gives you any trouble, just use Steps 1–3 in
Studio — the on-chain result is identical and the app still reads it.
