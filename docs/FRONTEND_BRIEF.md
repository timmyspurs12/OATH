# OATH — Frontend Build Brief (v1)

> **✅ LIVE INTEGRATION SHIPPED (current `app/index.html`).** The frontend now
> implements the §8 GenLayerJS read/write flow for real: it loads
> `genlayer-js` from an ESM CDN (no build step), reads all state from
> OathRegistry views (`get_claim` discovery for the docket, `get_verdict`,
> `get_trust`, `get_trust_batch`, `get_stats`), and sends real writes
> (`file_claim` payable with the minimum stake, `adjudicate`, `appeal` with the
> contract-derived ×2/×4 stake, `finalize`) through an EIP-1193 wallet on
> GenLayer Bradbury — waiting for `FINALIZED`, checking
> `txExecutionResultName === FINISHED_WITH_RETURN`, then re-reading from chain.
> The §7 seeded `DemoClient` and all simulated verdicts/fetches/appeals were
> **removed**; cases read `PUBLIC CLAIM` and exhibits read `ON-CHAIN EVIDENCE`
> because the contract does not persist those fields. Contract address is set at
> runtime via `?contract=0x…` or the **CONFIGURE CONTRACT** control (persisted to
> `localStorage`); reads need no wallet. Verified with `node --check` and a jsdom
> runtime smoke test driving file → adjudicate → appeal → finalize against an
> in-memory OathRegistry — 0 console errors.
>
> The brief below is kept as the original design specification (§7's demo mode
> was superseded by the live integration above).

> **Original delivered build:** this brief was implemented as a single-file SPA at
> `app/index.html` (no build step, demo-mode default, hash routes, seeded
> 14-case docket, ink-stamp verdicts, wax-seal scores). Verified: JS syntax
> clean, `node --check` + jsdom runtime smoke test — 0 console errors across
> all five screens, case-file open, demo filing, and ledger scan.
> Live-mode wiring per §8 remains the integration step (`genlayer-js` +
> `VITE_OATH_CONTRACT`).

> Hand this entire file to Claude (Claude Code / claude.ai) and say:
> **"Build the frontend exactly to this brief. Use the stack in §9. Default to demo mode (§7). Do not ask clarifying questions — make the listed decisions."**

---

## 0. What we're building

**OATH — the claim verification protocol on GenLayer.** A decentralized LLM jury fetches
a claim's evidence URLs itself, adjudicates the claim, and writes an appealable verdict +
trust score on-chain. Anyone (wallets, agents, marketplaces) calls `get_trust(subject)`
before transacting.

**The user's action:** paste a subject (dapp domain / agent ID / address), a claim, and
evidence links → watch the contract fetch the evidence, the jury deliberate, and a verdict
stamp land. Then browse the docket of all cases and the trust ledger of every subject.

**Product name:** OATH. **Tagline:** *Every claim faces a jury.*

---

## 1. The one sentence that kills "generic"

> **This is a forensic case-file / courtroom docket — not a crypto dashboard.**

No purple gradients, no glassmorphism, no rounded-2xl cards, no centered hero with a
grid background, no sparkline charts, no "Join the revolution" copy. If a screen looks
like it could ship on any Web3 site, it's wrong. The visual language is: **dark
courtroom (ink), warm paper, a red wax seal, monospace exhibits, serif headlines, a
ticker of verdicts running like a news wire.** The product is a *dossier*, and the UI
is the *file that proves it*.

---

## 2. Brand & copy principles

**Voice: dry, forensic, precise. Zero hype.**

| Moment | Copy (use this, or stay in this register) |
|---|---|
| Hero | **Every claim faces a jury.** |
| Hero sub | OATH verifies public claims — audits, agent track records, tokenomics, compliance — by fetching the evidence and letting a decentralized jury of AI models deliver the verdict, on-chain, in minutes. |
| File a claim | **File a case** · **Present your evidence** · **The jury deliberates** · **Verdict recorded** |
| Empty docket | *The docket is empty. File the first case.* |
| Verdict labels | VERIFIED · PARTIALLY VERIFIED · CONTRADICTED · UNVERIFIABLE |
| Trust legend | Verified — the evidence held up. Partially verified — half the story checks out. Contradicted — the evidence says otherwise. Unverifiable — the links went nowhere. |
| Appeal | **Submit an appeal** — stake ×2, window closes in 7 days. |
| Footer line | *Verification is the new diligence.* |

**Naming in UI:** claims are **cases** (CASE #0001). Evidence links are **exhibits**
(EXHIBIT A, B, C). The verdict is a **stamp**. The feed is the **docket**. The score is
the **seal**. The AI step is **the jury**. The on-chain record is the **record**.

---

## 3. Design system

**Theme: dark by default ("the courtroom is dark").** No light mode required; if added,
it's "paper mode" (#F2EBDD surfaces, ink text) — do not spend budget on it.

### Color tokens

| Token | Hex | Use |
|---|---|---|
| `ink` | `#131009` | page background |
| `ink-2` | `#1C1712` | panels, cards, rails |
| `ink-3` | `#262017` | raised surfaces, inputs |
| `line` | `#2E2619` | 1px borders (warm, not gray) |
| `paper` | `#F2EBDD` | primary text + paper surfaces |
| `paper-dim` | `#A89C82` | secondary text |
| `seal-red` | `#B3442E` | CONTRADICTED + brand accent (stamps, seals) |
| `verdict-green` | `#3E8A62` | VERIFIED |
| `verdict-amber` | `#C08A2E` | PARTIALLY VERIFIED |
| `verdict-blue` | `#4E7CA8` | UNVERIFIABLE |
| `gold` | `#D9A83C` | sparing accent (case numbers, active states) |

### Type

| Role | Font | Notes |
|---|---|---|
| Headlines / case numbers | **Fraunces** (variable, `opsz` + `SOFT`/`WONK` on) | serif, old-print warmth — NOT Inter Bold |
| Data, IDs, hashes, evidence, timestamps, labels | **IBM Plex Mono** | the entire "evidentiary" layer |
| Body / controls | **Inter** | quiet, secondary |

Self-host via `@fontsource-variable/fraunces`, `@fontsource/ibm-plex-mono`,
`@fontsource-variable/inter` — **no Google Fonts CDN** (preview iframe has no network).
Ship `font-display: swap`. Set `font-feature-settings` for Fraunces: `"SS01"` if available.

### Surfaces & texture

- Cards are **file folders**: `ink-2` panel, 1px `line` border, **slightly square
  corners (6–10px, never 20px+)**, and a **folder tab** (a small notched tab on the top
  edge that holds the folder label, e.g. `CASE #0417`). Implement the tab with a CSS
  pseudo-element or clip-path.
- **Paper grain**: a fixed SVG `feTurbulence` noise as a data-URI, `opacity: 0.04`,
  `pointer-events: none`, over the whole page. (No external images, ever.)
- Numbers and IDs in mono, uppercase, letterspaced: `CASE #0417` / `EXHIBIT B` /
  `http_status: 404` / `14:32 UTC`.
- Divider rules: 1px `line`, sometimes double (`border-top: 3px double` for doc headers).
- Right-side "docket stamp" column: verdict stamps sit at a slight rotation
  (`rotate(-3deg)`), like a rubber stamp on paper.

### Signature components (build these; they ARE the design)

1. **Stamp** — the verdict stamp. Ink-stamp animation: scale `2.4 → 1` with
   `opacity 0 → 1` over ~350ms (cubic-bezier(.2,.9,.3,1.2)), landing `rotate(-3deg)` with a
   60ms shake; color per verdict; inside: the verdict label (mono, bold, letterspaced,
   uppercase, in a **double-line rounded border**, `ink`-colored text on verdict color
   or inverted). Plus a tiny "ink bleed" blur at impact (`filter: blur(3px)` fading out).
2. **Seal score** — trust score as a **wax seal** (SVG): a notched circular seal with the
   number in Fraunces centered, a ribbon tail, color by band (≥70 green, 40–69 amber,
   <40 red, 50 exactly = "no data" gray). **Not** a progress ring. Animate edges with a
   seeded jagged wobble; "50" renders as an empty seal with `—`.
3. **Docket row** — one line: `CASE #0417` (gold, mono) · subject (serif) · claim-type
   chip · verdict stamp mini · time. Hovering lifts the row and reveals "open case →".
4. **Wire ticker** — a thin strip at the very top (or above the footer): marquee of the
   last verdicts, `◈ VERIFIED · 14:32 · arbswap.io` repeating, linear 40s, pauses on hover.
5. **Exhibit pin** — evidence card: `EXHIBIT A` tab, URL in mono (clipped, copyable),
   fetch status chip (`fetched · 200` green / `dead · 404` red / `binary · pdf` blue),
   and a short content preview block (first ~160 chars, mono, dimmed, blurred with
   `filter: blur(1.5px)` until hovered — "classified" feel).
6. **Jury transcript** — the rationale, typewriter-revealed (60–90ms/char, skip on
   click), then citations listed as `⌗ url` links. Header: `JURY TRANSCRIPT — 3 models
   in agreement`.

### Motion

- Durations 200–350ms; spring for the stamp (`stiffness 260, damping 22`).
- Evidence rows stagger in at 40ms; docket rows slide from `x: -8px` + fade.
- Respect `prefers-reduced-motion`: everything snap, no marquee.

---

## 4. Screens

Single-page app, 5 views via **hash tabs** (`#/preflight`, `#/docket`, `#/case/:id`,
`#/ledger`, `#/protocol`). A persistent left **docket rail** (~280px) on desktop:
logo, nav, live `get_stats()` counters (`cases filed · adjudicated · contradicted ·
treasury`), and the seal of the day. Rail collapses to a top bar under 900px.

### S1 — Pre-Flight (home, `#/preflight`)

The hero and the product in one screen. **Editorial, asymmetric — two columns
(58/42), not a centered card.**

- **Left (the filing):** serif headline "Every claim faces a jury." + one-line sub.
  Under it, the **case form**, styled like a legal filing:
  - Field 1: `SUBJECT` — text input, placeholder `app.defiplatform.xyz` (mono).
  - Field 2: `THE CLAIM` — textarea, placeholder `"This platform's contracts were
    audited by CertiK in May 2026 and the audit is public."` (serif, large-ish).
  - Field 3: `EXHIBITS (up to 5)` — dynamic URL rows, `EXHIBIT A` mono labels, `+ add`
    ghost button. Enter key adds a row.
  - **Claim-type chips** (single-select, enforced by §4 rule "the type is visible on the
    record"): `Audit / security` · `Agent capability` · `Airdrop / tokenomics` ·
    `Team & docs` · `Compliance / green` · `Reputation dispute`. Icons: simple SVG glyphs
    (shield, node, coins, group, leaf, scales).
  - Submit button: **`FILE CASE →`** (paper background, ink text; hover: gold).
  - Under it, the stake line (mono, dim): `stake 10.00 GEN · refunded unless
    CONTRADICTED · fee 5%`.
- **Right (the exhibit board — this is the differentiator):** a vertical "caseboard"
  showing **what happens after you file**, as if the current case is on the board:
  1. `EVIDENCE FETCHED` — the URL chips get pinged one-by-one (status flips to
     `fetched 200 · 1.2s` with a green tick, or `dead 404` in red).
  2. `JURY DELIBERATION` — 3 model chips (CLAUDE · GPT · GEMINI) light up in sequence,
     then join into `AGREEMENT: 2/3`.
  3. `VERDICT RECORDED` — the **Stamp** lands.
  4. `SEAL UPDATED` — the subject's seal score nudges.
  Board entries are pinned with red thumbtack dots; on load, one *past* case plays
  through in looped demo mode so nobody sees an empty board.
- Bottom strip: **the wire ticker** (§3, component 4) with real-looking historical
  verdicts.

### S2 — The Docket (`#/docket`)

The live ledger of cases. A dense, monospaced table (NOT cards):
`# · SUBJECT · TYPE · STATUS · VERDICT · CONFIDENCE · FILED(UTC) · STAKE · →`.
- Sortable columns (subject, type, verdict, filed, stake); client-side, no server.
- Filters: verdict chips (VERIFIED / PARTIAL / CONTRADICTED / UNVERIFIABLE /
  APPEALING / PENDING) + subject search box.
- Row click → S3. New rows animate in at the top (docket row slide-in).
- Header row is sticky; background `ink-2`; table borders only horizontal 1px `line`.
- Status capitalization in mono; verdict cells carry a **mini stamp** (small, same
  rotation, no animation). Confidence as `88%` mono, colored by band.

### S3 — Case File (`#/case/:id`)

**The money screen.** A full "case file folder" layout, three zones:

- **File header:** folder tab `CASE #0417`, huge Fraunces subject line, the claim text
  in a serif pull-quote with a left 3px `seal-red` or `gold` rule, meta strip in mono:
  `FILED 14:32:08 UTC · BY 0x8f3…c41 · STAKE 10.00 GEN · TYPE AUDIT/SECURITY`.
- **The file's right column:** the **Stamp** (large, current verdict) + confidence +
  `RECORDED ON-CHAIN` line with the tx/contract reference (mono, copyable) + **seal score**
  of the subject + two actions:
  - `SUBMIT APPEAL` (only when status = VERDICTED & window open) — shows `stake ×2
    (20.00 GEN)` then `×4 (40.00 GEN)` on second appeal, window countdown `closes in
    6d 04h`.
  - `FINALIZE` (when window closed or appeals exhausted) — disabled state reads
    `WINDOW CLOSED`.
- **Evidence zone (tabs):** `EXHIBIT A/B/C` tabs → Exhibit pin (§3, component 5). Tabs
  show a colored dot for status. Below, the **Jury transcript** (§3, component 6) with
  citations; each citation row: `⌗ https://…` (mono, links out, `target="_blank"`).
- **Appeal history:** if appeals exist, a small chronology `L1 · 2026-08-28 ·
  RE-JURIED — verdict upheld (PARTIALLY VERIFIED, 61%)`.

### S4 — Trust Ledger (`#/ledger`)

"Scan any subject before you trust it."

- Big centered **scan bar** (mono, `get_trust("…")` as a shell prompt: `$ get_trust`
  prefix in gold, then the subject). Enter → result card:
  - **Seal score** (§3, component 2) large on the left of the card.
  - Right: verdict run-rate breakdown as four mono rows with counts
    (`VERIFIED 3 · PARTIAL 2 · CONTRADICTED 1 · UNVERIFIABLE 0`) + `SCORE 68/100 ·
    WEIGHTED — VERIFIED 1.0 · PARTIAL 0.5 · UNVERIFIABLE 0.25 · CONTRADICTED 0.0`.
  - Below: **history** (docket rows, small) with `when` stamps ("3d ago").
  - Unknown subject → the empty seal at 50 + note `NO VERDICTS ON RECORD. 50 =
    NEUTRAL. TRUST NOTHING UNVERIFIED.` (capitalized, dim, mono).
- Below: "top subjects" table (by # of verdicts) linking to case files.

### S5 — Protocol (`#/protocol`)

The explainer — but on-brand, no generic "3 features" section:

- Three pillars as **three file folders side by side**, each with folder tab and a
  full-page metaphor: `EXHIBIT 1 — THE FETCH` (native web access; the contract reads
  the evidence, you can't doctor it), `EXHIBIT 2 — THE JURY` (leader + validators,
  diverse models, Equivalence Principle — judgment, not keywords), `EXHIBIT 3 — THE
  RECORD` (stake, verdict, appeal ×2/×4, 7-day window, finalize).
- A **decision tree** (SVG): claim → evidence reachable? (no → UNVERIFIABLE) →
  contradicts claim? (yes → CONTRADICTED) → fully supports? (yes → VERIFIED) →
  else PARTIALLY VERIFIED. Animated path drawing on scroll.
- Verdict taxonomy table (4 rows, verdict classes & their stake consequences).
- FAQ accordion (5 items: what counts as evidence / who pays / can verdicts be
  appealed / what is the seal / is this a court? → "No. It's a protocol. You bring
  the claim.")
- Footer: `OATH — CLAIM VERIFICATION PROTOCOL · INTELLIGENT CONTRACTS ON GENLAYER ·
  BUILD ON BRADBURY TESTNET · CONTRACT 0x…` + links (docs, GitHub, X).

---

## 5. Contract API → frontend types

Contract address (configure at build: `VITE_OATH_CONTRACT`). All calls go through the
typed client in `src/lib/api.ts`:

```ts
export type VerdictCode = 0 | 1 | 2 | 3 | 4;            // 0=none,1=VERIFIED,2=PARTIAL,3=CONTRADICTED,4=UNVERIFIABLE
export type VerdictLabel = 'VERIFIED' | 'PARTIALLY_VERIFIED' | 'CONTRADICTED' | 'UNVERIFIABLE' | 'NONE';
export type CaseStatus = 'PENDING' | 'ADJUDICATING' | 'VERDICTED' | 'APPEALING' | 'FINAL';

export interface CaseRecord {            // get_claim / get_verdict
  id: bigint; requester: string; subject: string; claim: string;
  evidence_urls: string[]; stakeWei: bigint; status: CaseStatus;
  verdict: VerdictCode; verdictLabel: VerdictLabel; confidence: number;
  rationale: string; citations: string[]; appeals: number;
  createdAt: string; adjudicatedAt: string; lastError: string;
}

export interface SubjectScore {          // get_trust / get_trust_batch
  subject: string; totalVerdicts: number; verified: number; partial: number;
  contradicted: number; unverifiable: number; score: number;   // 0..100, 50 = no data
  lastVerdict: VerdictLabel; lastUpdated: string;
}

export interface OathStats {             // get_stats
  claimsFiled: number; claimsAdjudicated: number; claimsContradicted: number;
  treasuryWei: bigint; minStakeWei: bigint; feeBps: number;
}
```

**Contract methods** (signatures as deployed):

| Function | Kind | Args | Returns | Frontend use |
|---|---|---|---|---|
| `file_claim` | write · payable | `(subject: str, claim_text: str, evidence_urls_json: str)` — JSON array string | `u256 caseId` | S1 form, **value = stakeWei** |
| `adjudicate` | write | `(claim_id: u256)` | `str label` | after filing (or S3 button `RUN JURY`) |
| `appeal` | write · payable | `(claim_id: u256)` | `str` | S3 appeal, **value = next multiplier × stake** |
| `finalize` | write | `(claim_id: u256)` | `str` | S3 finalize |
| `get_claim` | view | `(claim_id)` | `Claim` | S3 full record |
| `get_verdict` | view | `(claim_id)` | dict | S3 verdict block |
| `get_trust` | view | `(subject)` | `SubjectScore` | S4, S3 seal |
| `get_trust_batch` | view | `(subjects[])` | `SubjectScore[]` | S4 top subjects |
| `get_stats` | view | — | dict | rail counters |

**Important mapping rules:** `DynArray[str]` serializes as a plain string array;
`u256`/`u*` arrive as `bigint`/`number` (format wei→GEN at ÷10¹⁸, 2 decimals, no
float-precision nonsense); verdict codes are `1|2|3|4` — map via the table; `Address`
is a `0x…` string. `conflict`: `get_verdict` returns `requester` as string.

---

## 6. Claim types (the taxonomy)

| Type | id | Default exhibit hint |
|---|---|---|
| Audit / security | `audit` | auditor's registry page, report URL |
| Agent capability | `agent` | agent's public task log, dashboard |
| Airdrop / tokenomics | `tokenomics` | token page, allocation table, explorer |
| Team & docs | `team` | GitHub org, docs site, LinkedIn trail |
| Compliance / green | `compliance` | certificate database, regulator page |
| Reputation dispute | `reputation` | the statement itself + rebuttal link |

---

## 7. Demo data & demo mode (MANDATORY)

The preview/build must work with **zero network, zero wallet, zero env vars**. Default
mode = **demo**: a `DemoClient implements OathApi` seeded with ~14 realistic `CaseRecord`s
across all six types and 6 subjects with seals. The demo must replay the full flow:
filing instantly "runs" the jury (setTimeout sequence: exhibits fetch → jury → stamp →
seal) and appends the case to the top of the docket + updates the subject's seal.

Seed subjects: `arbswap.io` (audit VERIFIED, 88%), `defiplatform.xyz` (audit
CONTRADICTED 93% — the poster child), `agent-oracle-7` (capability PARTIAL 61%),
`greenlogistics.na` (compliance UNVERIFIABLE), `nova-token.xyz` (tokenomics VERIFIED),
`chainpilot.dev` (reputation VERIFIED + one appeal). Seed one case with status
`APPEALING`, one `FINAL`, one `PENDING`, one with `lastError`. Timestamps relative to
"now" minus hours/days (compute, don't hardcode).

Every demo verdict gets a **plausible rationale** (2–4 sentences citing concrete
evidence: registry IDs, HTTP codes, date mismatches) and 2–3 citation URLs. Write them
in the dry forensic register — e.g., for the CONTRADICTED case:

> *The cited audit URL returns HTTP 404 and the auditor's public registry shows no
> engagement for this project. The auditor's published client list omits the project
> entirely. The claim is contradicted by the authoritative registry.*

**Demo badge:** a persistent chip `● DEMO — OFFLINE RECORDS` (top-right, mono, dim);
in live mode it becomes `● BRADBURY TESTNET` (green dot). Also show a one-time banner on
S1 in demo mode: `Demo records. Deploy contracts/oath_registry.py in GenLayer Studio and
set VITE_OATH_CONTRACT to go live.` — with the Studio link.

---

## 8. Live mode wiring

```ts
import { createClient } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';

const client = createClient({ chain: testnetBradbury });

// reads: no account needed
const res = await client.readContract({
  address: OATH_ADDRESS, functionName: 'get_trust', args: [subject],
});
const score = res.result as { score: bigint };

// writes: account from connected wallet (EIP-1193 via viem), wrong-chain → client.connect()
const { transactionHash } = await client.writeContract({
  account, address: OATH_ADDRESS, functionName: 'file_claim',
  args: [subject, claimText, urls], value: stakeWei,
});
await client.waitForTransactionReceipt({ hash: transactionHash, status: TransactionStatus.FINALIZED });
```

- Env: `VITE_OATH_CONTRACT` (0x…), `VITE_NETWORK=testnetBradbury` (default).
- `client.connect()` on write errors so WalletConnect users can switch chains.
- Wallet connect button in the rail; non-connected users can read + explore freely.
- Faucet link (testnet GEN): `https://testnet-faucet.genlayer.foundation/`.
- Explore links: explorer at `https://explorer.testnet-chain.genlayer.com/` (address /
  tx links from the case file).
- Never block UI on chain: every call is wrapped, demo client is the fallback for
  *anything* that throws (show the demo record + a `LIVE CALL FAILED — showing demo`
  note), so the app never hard-fails in a sandboxed/no-network preview.

---

## 9. Stack & structure (do it exactly)

- **Vite + React 18 + TypeScript**, **Tailwind v4** (or plain CSS with design tokens —
  either way, the tokens in §3 are the source of truth) + **Framer Motion** for the
  stamp/board/choreography. No shadcn, no Material, no daisyUI, no template kits.
- Fonts via `@fontsource*` (bundled — preview-safe).
- Icons: hand-drawn 1.5px stroke SVGs as components (no icon libraries).
- Routing: hash-based tabs, no router lib.
- i18n: no. SEO: not needed (SSR no).
- File tree:
  ```
  src/
    main.tsx  App.tsx
    styles/{tokens.css, base.css}
    lib/{types.ts, api.ts, client.ts, demoData.ts, format.ts}
    components/{Stamp, SealScore, DocketRow, WireTicker, Exhibit, JuryTranscript,
                FolderTab, TypeChips, StatusChip, Rail, DemoBadge}.tsx
    screens/{PreFlight, Docket, CaseFile, Ledger, Protocol}.tsx
  ```
- Responsive: rail → top bar < 900px; table → stacked rows < 720px; test at 360px.
- **Preview constraint (critical):** the sandboxed preview iframe has **no network
  access** — no CDN fonts, no external images, no API calls. Everything bundled;
  default demo mode; SVG noise/texture only.

---

## 10. Anti-generic rules (the review gate)

**Do**
- Mono uppercase letterspaced labels everywhere; serif Fraunces headlines.
- Warm dark palette; always show the verdict color as a *stamp*, not a pill.
- Folder tabs on cards, double rules, paper grain, pinned exhibits, red thumbtacks.
- Show real numbers & IDs (`CASE #0417`, `0x8f3…c41`, `http_status 404`, `6d 04h`).

**Don't**
- No gradients (except the subtle ink-bleed blur), no glassmorphism, no `rounded-[24px]`,
  no emoji as icons, no "🚀", no purple/blue neon, no generic 3-column feature grid,
  no carousel, no hero image, no "web3 × AI" buzzwords in copy.
- No charts of TVL/user growth. The only "chart" allowed is the verdict run-rate rows.

---

## 11. Acceptance checklist

- [ ] Runs offline in demo mode; every screen populated with seed data; no console errors.
- [ ] The stamp animation + seal score + docket row + wire ticker all exist and feel
      like one design system.
- [ ] Filing a demo case replays fetch → jury → stamp → seal and appends to the docket.
- [ ] Case file shows exhibit tabs with status chips, jury transcript typewriter, appeal
      math (×2/×4) and finalize states.
- [ ] Trust ledger renders seals per subject and the neutral "no data" state.
- [ ] Live mode compiles with `VITE_OATH_CONTRACT` set; writes go through genlayer-js;
      failures fall back to demo with a visible note.
- [ ] `prefers-reduced-motion` respected; keyboard-navigable; 360px usable.
- [ ] Zero external assets at runtime (fonts bundled, all images are SVG inline/data-URI).
