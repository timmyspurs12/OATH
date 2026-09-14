# OATH SDK

Agent-facing Python client for the **OATH Claim Verification Protocol**.

```bash
pip install genlayer-py          # Python 3.12+
```

## Reads — no key needed

```python
from oath_client import OathClient

oath = OathClient(address="0xe9B73DD18446a1f121090a21C544D51349a1e8Ad", chain="studionet")

oath.get_trust("example.com")        # live, time-decayed trust record
oath.get_badge("example.com")        # score, grade, color + ready-to-embed SVG
oath.badge_svg("example.com")        # the SVG string alone
oath.get_categories()                # claim categories -> jury rules
oath.trust_gate(["vendor.example"])  # {"decision": "TRUSTED"|"UNTRUSTED", ...}
```

## Writes — needs a funded key

```python
import os
oath = OathClient(address="0x…", chain="studionet", private_key=os.environ["OATH_KEY"])

receipt = oath.file_claim(
    "vendor.example",
    "This vendor holds a current SOC 2 Type II report.",
    ["https://vendor.example/soc2", "https://auditor.example/registry"],
    category="compliance",
)
cid = receipt["claim_id"] if "claim_id" in receipt else None
oath.adjudicate(1)          # run the jury
oath.finalize(1)            # after the appeal window: settles stake + trust
oath.reverify(1)            # months later: reopen as a fresh claim
```

## The trust gate (for agents & marketplaces)

```python
gate = oath.trust_gate(["a.example", "b.example"], min_score=70, require_fresh=True)
if gate["decision"] != "TRUSTED":
    for subject, r in gate["subjects"].items():
        print(subject, r["reasons"])
```

`trust_gate` is the one-call primitive the whole protocol exists for: before
an agent transacts with an unknown counterparty, it asks OATH.

## Chains

`chain=` accepts `"studionet"`, `"testnet_asimov"`, `"localnet"`; pass
`rpc_url=` to target a custom endpoint.
