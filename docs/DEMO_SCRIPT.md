# OATH — Launch Assets & Evidence Pack

Everything you need to publish the repo, post it, and demo it. Use the copy as-is
or adapt — but keep the forensic register (no hype words).

---

## 1. GitHub repo setup

**Repo name:** `oath` (or `oath-genlayer` if `oath` is taken)

**Description (paste in GitHub's "Description" field):**
> OATH — on-chain verification of public claims. An Intelligent Contract that
> fetches your evidence, puts it before a decentralized jury of AI models, and
> stamps VERIFIED / PARTIALLY VERIFIED / CONTRADICTED / UNVERIFIABLE on-chain —
> with appeal, stake slashing, and a trust score any agent can query. Built on
> GenLayer.

**Topics:** `genlayer` `intelligent-contracts` `genvm` `ai-agents`
`verification` `trust` `web3` `python` `decentralized-ai` `claim-verification`

**Website (optional, high value):** your GitHub Pages URL (see §4) — a live demo
link is the single strongest evidence in the portal submission.

**README:** already in the repo (`README.md`). Make sure the repo's "About" also
points the GitHub Pages site at the app (`https://<you>.github.io/oath/`).

**License:** MIT (already in repo).

---

## 2. Portal submission text (type 41 — Projects)

Paste into the submission description (3 paragraphs, ~1,800 chars):

> **Problem.** In the agentic economy, everyone makes claims: "audited by X",
> "97% success rate", "certified compliant", "non-custodial". Verifying a claim
> costs more than trusting it — so agents, wallets and marketplaces trust first
> and discover the truth later. There is no existing public primitive that
> answers "is this claim true?" at machine speed.
>
> **What OATH does.** OATH is a single Intelligent Contract on GenLayer that
> verifies publicly checkable claims. A claimant files a subject, a plain-English
> claim and up to five evidence URLs, staking 10 GEN. The contract fetches every
> URL itself via native web access — the claimant cannot doctor what the jury
> sees — then a leader validator plus peer validators run the same adjudication
> prompt on diverse LLMs and reach consensus through the Equivalence Principle.
> The verdict (VERIFIED / PARTIALLY VERIFIED / CONTRADICTED / UNVERIFIABLE),
> confidence, rationale and citations are written on-chain. Any party can appeal
> within a deterministic 7-day window (stake ×2, then ×4) before the verdict is
> finalized; filing a claim that gets CONTRADICTED forfeits the stake. Every
> verdict updates a persistent, machine-queryable trust score per subject —
> `get_trust(subject)` — so wallets, agents and marketplaces can screen before
> transacting.
>
> **Why GenLayer.** None of this is possible on a deterministic chain: evidence
> fetch, semantic judgment and non-deterministic consensus must happen inside
> the execution environment itself. GenLayer's native web access, LLM jury
> consensus and Python contract model let ~300 lines of code replace the
> oracle + human-review + appeal stack that every verification marketplace
> currently needs. OATH turns trust into an on-chain primitive — and every
> check it performs is exactly the kind of decision GenLayer exists to settle.
> Live on Bradbury testnet; frontend demo + full source in the repo.

---

## 3. X posts

### Post A — launch (recommended)

> Claims are cheap. Verification is expensive.
>
> OATH makes it cheap too — an Intelligent Contract on @GenLayer that fetches
> your evidence, puts it before a jury of AI models, and stamps
> VERIFIED / CONTRADICTED on-chain in minutes.
>
> • evidence fetched by the contract, not by you
> • stake-slashing for false claims
> • appeal ×2, ×4 → final verdict
> • one call: get_trust("any.xyz")
>
> Every claim faces a jury. 🧵
>
> 📄 repo / contract / live demo ↓

### Post B — short (for a quote-reply / follow-up)

> "This dApp is audited."
>
> Who says? The filing page says.
>
> OATH asks the evidence itself — the auditor's registry, the explorer, the
> report URL — then lets a jury of AI models decide. On-chain. In minutes.
>
> Trust is now a stamp, not a slogan. @GenLayer

### Post C — agent-economy angle (for the Agent Tank crowd)

> Agents will transact with each other before humans ever read a contract.
> So agents need a cheap way to ask: is this claim true?
>
> OATH = the primitive for that question. Fetch evidence → AI jury → verdict →
> trust score. Every agent gets a reputation, provable in one call.
>
> Built on GenLayer. Contract + demo in thread ↓

**Posting checklist:** attach the 60s short (§5) or a screen recording of a real
Bradbury verdict; link repo + GitHub Pages demo; tag @GenLayer, use
`#GenLayer` `#IntelligentContracts` `#AIagents`.

---

## 4. Live demo on GitHub Pages (free, 2 minutes — do this FIRST)

The app is a single self-contained file with hash routing — it deploys as-is.

1. After pushing: GitHub repo → **Settings → Pages**
2. Source: **Deploy from a branch** → `main` / root → Save
3. Wait ~1 min → `https://<your-username>.github.io/oath/`
4. Put this URL in: GitHub About, the X post, the portal submission, and as the
   `actionHref` style link wherever the portal asks for a live demo.

> **IMPORTANT — the repo root MUST contain `index.html`** (a byte-identical
> copy of `app/index.html` — deploy entry point) and a `.nojekyll` marker.
> If the root `index.html` is missing, GitHub Pages silently falls back to
> rendering `README.md` through Jekyll and the styled app disappears from
> `<your-username>.github.io/oath/`. Keep both copies in sync:
> `cp app/index.html index.html`.

> The sandboxed in-app preview blocks external fonts; GitHub Pages doesn't.
> On Pages you get full Fraunces + IBM Plex Mono — the real design.

---

## 5. 60-second demo video (YouTube Short)

### One-line logline
*Watch a claim get exposed — and a stamp land out of nowhere.*

### Shot list (60s, tight cuts, ~7 shots; any phone screen recording works)

| Time | Shot | What's on screen | VO (if narrating) |
|---|---|---|---|
| 0:00–0:04 | 1 | Title card: ink background, "EVERY CLAIM FACES A JURY" in Fraunces, wax-seal logo stamps in | "Every claim faces a jury." |
| 0:04–0:12 | 2 | Pre-Flight form: type subject + claim "audited by CertiK…", evidence rows fill in | "This platform says it's audited. So we filed a case — with the auditor's own registry as evidence." |
| 0:12–0:22 | 3 | Exhibit board: URLs ping → 200 ✓ / 404 ✗ | "The contract doesn't take our word for it. It fetches every link itself." |
| 0:22–0:32 | 4 | Jury deliberation: model chips light up → AGREE | "Three AI models, two jurisdictions of truth — one verdict." |
| 0:32–0:40 | 5 | STAMP LANDS: CONTRADICTED, rationale typewrites | "Contradicted. The registry has no such audit." |
| 0:40–0:48 | 6 | Case file: appeal math ×2/×4, trust seal drops to red | "False claims cost the filer their stake. And the subject's seal just dropped." |
| 0:48–0:56 | 7 | Trust ledger: `get_trust("defiplatform.xyz")` → score | "One call. Any agent, wallet or marketplace can check before it pays." |
| 0:56–1:00 | 8 | Outro: logo + URL on ink | "OATH. Every claim faces a jury." Caption: link in bio / repo |

### Formatting notes
- 9:16 vertical, 1080×1920, captions on ("Case #0417", "CONTRADICTED" as stamps).
- Sound: none needed if captions carry it; if VO, read the right column in a flat,
  forensic tone (no youtuber voice).
- Title: `This AI jury catches fake audits on-chain 📁 OATH on GenLayer`
- Description: one line + repo link + Pages link + `#GenLayer #IntelligentContracts`.

---

## 6. Push order (get the strongest evidence fastest)

1. Push to GitHub (§ below) → **Pages on** (§4)
2. Deploy contract on Bradbury, run one real `adjudicate`, copy the address
3. Post X (Post A) + Short (video from §5 with the real verdict)
4. Submit portal type 41 with: repo + Pages + Studio/explorer contract link +
   X post + YouTube Short as evidence
5. Backfill: add the deployed address to README's "Live on" line; push again as a
   Milestone (type 47).

---

## 7. Git Bash push — the exact commands

Your `oath.zip` is in **Downloads**. In Git Bash, Downloads is `~/Downloads`
(which is really `C:\Users\<YourWindowsUsername>\Downloads`). The zip extracts to
a folder named `oath`, so the project lives at `~/Downloads/oath`.

```bash
# 0) one-time Git identity (use your GitHub email)
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"

# 1) create the repo on github.com FIRST (New repo → name "oath" → Public → NO README)
#    — or with gh CLI:   gh auth login  &&  gh repo create oath --public --source . --push

# 2) go to Downloads and extract the zip, then enter the project folder
cd ~/Downloads
#    Extract: right-click oath.zip → "Extract All" (Windows Explorer)
#    …or if unzip exists in Git Bash:
unzip oath.zip

cd oath                                  # → ~/Downloads/oath

# 3) init, stage, commit
git init -b main
git add .
git commit -m "OATH: claim verification protocol on GenLayer — intelligent contract, jury prompt, SPA, docs"

# 4) connect & push (github.com/<YOUR-USERNAME>/oath must already exist)
git remote add origin https://github.com/<YOUR-USERNAME>/oath.git
git push -u origin main
```

**Auth note:** GitHub removed password auth for HTTPS. Use either
`gh auth login` (easiest — handles it for you), or an SSH key:
`ssh-keygen -t ed25519` → add the pubkey at github.com/settings/keys → then use
`git@github.com:<YOUR-USERNAME>/oath.git` as the remote instead of the HTTPS URL.

**Verify (run after each risky step — anything prints red, paste it to me):**
```bash
pwd                          # must end in …Downloads/oath
git status                   # "On branch main / nothing to commit" = staged OK
git log --oneline            # 1 commit: c87353f-style hash, your message
git remote -v                # origin → your repo URL
```

**Already extracted before?** Skip the `unzip` line — `cd ~/Downloads/oath` works
as long as the folder exists. If you previously made a repo in that folder and
want a clean start: `rm -rf ~/Downloads/oath/.git` (this deletes only git history,
**not** your files) and re-run from step 3.
