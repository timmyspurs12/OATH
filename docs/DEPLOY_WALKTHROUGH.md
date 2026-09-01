# OATH — Deploy & Demo Walkthrough (GenLayer Studio)

Goal: get `OathRegistry` live and produce a **real verdict on-chain**, then grab
the two evidence links the portal wants (Studio explorer + Studio contract link).

Time: ~10 minutes. No coding. Studio is gasless for EVM wallet flows.

---

## Step 0 — Open Studio & grab your address

1. Go to **https://studio.genlayer.com**
2. In the header, find your **account address** (a `0x…` string; if none, click
   the account/wallet selector to create/connect one).
3. **Copy that address.**

## Step 1 — Get testnet GEN (you need ≥ 10 GEN for the stake)

1. Open the faucet: **https://testnet-faucet.genlayer.foundation/**
2. Paste your address → request. You should receive testnet GEN shortly.
3. (On the portal, "Top-up with Testnet GEN" at portal.genlayer.foundation does
   the same thing if the faucet is empty or rate-limited.)

## Step 2 — Load the contract (use a FRESH project)

1. In Studio: **New Contract** → paste the entire contents of
   **`contracts/oath_registry.py`** (open it in **Notepad**, Ctrl+A → Ctrl+C).
2. **Verify the header is EXACTLY this shape** (this is what the schema
   compiler parses — do not merge the doc comment block into it):

   ```
   # { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
   <blank line>
   # ============================================================================
   #  OATH — Claim Verification Protocol ...
   ```

   - Line 1 = the pinned runner hash (matches the official GenLayer boilerplate
     and is what Studio's backend accepts — verified live against
     `studio.genlayer.com/api`).
   - Line 2 = **an empty line**. GenVM's text-contract parser glues EVERY
     comment line directly after the runner comment into the runner JSON, so a
     doc block touching line 1 corrupts it and Studio reports
     `invalid_contract` / "Could not load contract schema". (Fixed in v6.)
3. The **Constructor Inputs** pane should appear with `min_stake`, `fee_bps`, …
   If you instead see *"Could not load contract schema"*, close the browser tab,
   open **studio.genlayer.com** fresh (NOT any `/run-debug` link), and re-paste.
   (Studio caches failed contracts — Settings → Reset Storage helps.)

> **Which GenVM is Studio talking to?** `studio.genlayer.com` is the frontend
> only — by default it talks to **your own local GenVM** at
> **`http://127.0.0.1:4000/api`** (the Docker stack). Make sure your local
> GenVM is running (`docker ps` shows it) and is **v0.2.16 or newer** (check
> the version in Studio's Node Logs / `genvm --version`). If you switched the
> network selector in Studio to *"Genlayer Studio Network"*, it instead talks
> to `https://studio.genlayer.com/api` (hosted). Both accept the pinned hash.

### Step 2b — 30-second isolation test (only if Step 2 still fails)

Create a **new** contract and paste exactly this (message me the result):

```python
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *

class Hello(gl.Contract):
    name: str

    def __init__(self, name: str):
        self.name = name

    @gl.public.view
    def run(self) -> str:
        return f'Hello, {self.name}'
```

| Hello result | Meaning |
|---|---|
| Constructor Inputs appear | Environment + pin are fine → your Oath paste/copy is the problem → use the v6 file from the fresh `oath.zip` (NOT the old one in Downloads) |
| Still "Could not load contract schema" | Environment problem → reset Studio storage, hard-refresh, and paste me the FULL error from the Node Logs at the bottom of Studio |

## Step 3 — Deploy

1. In **Constructor Inputs**, leave the defaults (they already resolve to the
   right values: `min_stake = 10 GEN`, `fee_bps = 5%`, `max_evidence = 5`,
   `max_appeals = 2`, window 7 days). If a field is blank, type the defaults or
   use the **JSON** toggle.
2. Click **Deploy**.
3. On success, Studio shows the **contract address** (`0x…`) — **copy it.**

## Step 4 — File a real case

1. In **Write Methods**, expand **`file_claim`** (it's payable — Studio shows a
   **Value (GEN)** field).
2. Fill in:
   - `subject` — e.g. `arbswap.io`
   - `claim_text` — e.g. `"ArbSwap's core AMM contracts were audited by CertiK
     in March 2026 and the report is publicly available."`
   - `evidence_json` — a **JSON array of URLs**, all on one line, e.g.
     `["https://certik.com", "https://arbswap.io"]`
     (with double quotes around each URL — this is a single string field)
   - **Value (GEN)** — `10`
3. Execute. It returns the **case id** (e.g. `1`). Note it.

## Step 5 — Run the jury

1. Expand **`adjudicate`** → `claim_id` = the case id from Step 4 → execute.
2. **What you'll see:** the tx goes through consensus (leader + validators run
   the jury on their own models), then the verdict returns — e.g.
   `VERIFIED` — and `get_claim` / `get_verdict` now show `verdict`, `confidence`,
   `rationale`, `citations`, `status: VERDICTED`.
3. Check **`get_trust`** with your subject → score updated from the neutral 50.

## Step 6 — Screenshot & collect evidence links

- **Contract state / views** panel: screenshot `get_verdict` + `get_trust`
  results — these are your proof shots.
- **Studio explorer link (for the portal):**
  `https://explorer-studio.genlayer.com/address/<YOUR_CONTRACT_ADDRESS>`
- **Studio import link (also accepted):**
  `https://studio.genlayer.com/?import-contract=<YOUR_CONTRACT_ADDRESS>`
- **Testnet explorer (if you later deploy to Bradbury via CLI):**
  `https://explorer.testnet-chain.genlayer.com/address/<ADDRESS>`

## Step 7 — (Optional, shows depth) Appeal & finalize

1. `appeal` with `claim_id` (payable — value `20` GEN the first time).
2. `adjudicate` again → status `APPEALING → VERDICTED`.
3. `finalize` → `FINAL`. (In Studio, time is simulated — the 7-day window check
   may pass or be overridable; if finalize says "window still open", it's a
   Studio time feature, not a contract bug — you can also just leave it.)

---

## Troubleshooting

### "Could not load contract schema" — the error you hit

Studio compiles your code when you load it; then it fetches the generated schema
(ABI) for the **Constructor Inputs** pane. This message = **the compile step
failed**, so there is no schema to load. It is almost always one of:

| Cause | Fix |
|---|---|
| You opened a **shared deep-link** (e.g. `…/run-debug`) instead of the main page | Use **https://studio.genlayer.com** → **New Contract** → paste. Deep-links have no contract loaded — the error is built into that view |
| **Doc comments touching the runner comment (most common!)** | Line 2 must be a **blank line**. If the `# ====` banner directly follows line 1, GenVM glues it into the runner JSON → `invalid_contract`. Use the v6 file from `oath.zip` / GitHub |
| **Copy-paste mangling** — smart quotes (`“ ”`) or truncated paste | Get the file fresh: open `contracts/oath_registry.py` in Notepad → Ctrl+A → Ctrl+C → paste. **Never copy from a chat/preview render** |
| Stale/broken cached contract | Close the tab → **Settings → Reset Storage** → reload → re-paste. Also try a private/incognito window |
| Compile error in the pasted code | Read the **Node Logs** at the bottom of Studio — the real error (Python traceback, `invalid_contract`, etc.) is logged there. **Paste it to me and I'll fix the code in minutes.** |

> Also: Studio runs on **Docker** (ports 8080/4000/6678/5432/8545). If Docker
> Desktop isn't running or port conflicts exist, the backend can't compile —
> see the Studio troubleshooting docs. A **hard refresh (Ctrl+Shift+R)** and
> clearing localhost site data fixes most of these.

### Other issues

| Symptom | Fix |
|---|---|
| Deploy fails with runner error | Line 1 must be `# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }` with a **blank line 2**, and the whole file pasted (`py-genlayer:test` is a *local-debug only* alias and is rejected by the Studio backend) |
| `file_claim` → "stake too low" | You didn't enter `10` in **Value (GEN)**, or your faucet balance is below 10 GEN — top up and retry |
| `adjudicate` returns `ADJUDICATION_FAILED` | Transient — the tx rolls back to PENDING with `last_error`; check `last_error`, re-run `adjudicate` |
| `exec_prompt` errors on one URL | The jury keeps the leader result if validators can't fetch; use reliable URLs (registries/docs) for the demo |
| Studio can't reach a URL | Studio web access uses its local browser; prefer stable pages. Live-network behavior is validated on Bradbury |

## After this — the portal form

- §06 **Contract link (optional):** paste the `explorer-studio…/address/0x…` URL
- **Evidence:** add "GenLayer Explorer Contract" + "GenLayer Studio Contract"
  with those same URLs (auto-detected by the portal)
