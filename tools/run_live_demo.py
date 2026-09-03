"""Live demo driver: exercises the full deferred-settlement flow on Studio.

file -> adjudicate (PROVISIONAL) -> appeal -> re-adjudicate -> appeal ->
re-adjudicate -> finalize (appeals exhausted) -> claim_refund.

Run:  python3 tools/run_live_demo.py
"""
import os
import sys
import time
import secrets

import genlayer_py as g

CONTRACT = "0xb39AE79FFdEE708b228D9aadBCCcfE20bB73670F"
GEN = 10 ** 18
KEY_PATH = os.path.join(os.path.dirname(__file__), "..", ".oath_demo_account.key")

key = bytes.fromhex(open(KEY_PATH).read().strip())
acct = g.create_account(key)
print("demo account:", acct.address)
client = g.create_client(chain=g.studionet, account=acct)


def wait(tag, txhash, timeout=240):
    print(f"  [{tag}] submitted {txhash if isinstance(txhash,str) else (txhash.hex() if hasattr(txhash,'hex') else txhash)} — waiting for consensus…")
    h = txhash.hex() if hasattr(txhash, "hex") else str(txhash)
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = client.wait_for_transaction_receipt(h, interval=6000, retries=1)
            status = r.status if hasattr(r, "status") else None
            # wait_for_transaction_receipt raises until accepted
            print(f"  [{tag}] consensus reached in {int(time.time()-t0)}s")
            return r
        except Exception as e:
            msg = str(e)
            if "not found" in msg.lower() or "pending" in msg.lower() or "timeout" in msg.lower():
                time.sleep(5)
                continue
            # may raise on failure
            if "finalized" in msg.lower() or "accepted" in msg.lower():
                return r
            print(f"  [{tag}] wait note: {msg[:160]}")
            time.sleep(5)
    print(f"  [{tag}] timed out waiting; check explorer")
    return None


def view(fn, args):
    for i in range(4):
        try:
            return client.read_contract(CONTRACT, fn, args)
        except Exception as e:
            if "Rate limit" in str(e):
                time.sleep(20)
            else:
                raise
    raise RuntimeError(f"view {fn} failed after retries")


def gen(v):
    return f"{v/GEN:.2f} GEN"


# --- 1. file ---------------------------------------------------------------
subject = "ethereum.org"
claim_text = (
    "The Ethereum Foundation states on its official website that the Merge "
    "transitioned Ethereum from proof-of-work to proof-of-stake in September "
    "2022, and the site publishes this as the official account."
)
evidence = ["https://ethereum.org/en/about/", "https://ethereum.org/en/history/"]

print("\n1) FILING CLAIM (10 GEN stake)…")
tx = client.write_contract(
    CONTRACT, "file_claim",
    args=[subject, claim_text, __import__("json").dumps(evidence)],
    value=10 * GEN,
)
cid = wait("file", tx)
# read back to get the id
stats = view("get_stats", [])
claim_id = int(stats["claims_filed"])
print(f"  claim id: {claim_id}; filed total: {claim_id}")
time.sleep(3)

# --- 2. adjudicate (PROVISIONAL) -------------------------------------------
print("\n2) ADJUDICATE (records PROVISIONAL verdict only)…")
wait("adjudicate#1", client.write_contract(CONTRACT, "adjudicate", args=[claim_id]))
time.sleep(3)
c = view("get_claim", [claim_id])
t = view("get_trust", [subject])
print(f"  status={c['status']} verdict={c['verdict_label']} confidence={c['confidence']}")
print(f"  verdict_final={c['verdict_final']}  trust.total_verdicts={t['total_verdicts']} score={t['score']}  (must still be neutral: 50)")

# --- 3. appeal #1 (2x base = 20 GEN) then re-adjudicate --------------------
print("\n3) APPEAL #1 (20 GEN) then RE-ADJUDICATE…")
wait("appeal#1", client.write_contract(CONTRACT, "appeal", args=[claim_id], value=20 * GEN))
time.sleep(3)
c = view("get_claim", [claim_id])
print(f"  status after appeal: {c['status']} appeals={c['appeals']}")
wait("adjudicate#2", client.write_contract(CONTRACT, "adjudicate", args=[claim_id]))
time.sleep(3)
c = view("get_claim", [claim_id])
print(f"  re-adjudicated: status={c['status']} verdict={c['verdict_label']} confidence={c['confidence']}")

# --- 4. appeal #2 (4x base = 40 GEN) then re-adjudicate --------------------
print("\n4) APPEAL #2 (40 GEN) then RE-ADJUDICATE (appeals now exhausted)…")
wait("appeal#2", client.write_contract(CONTRACT, "appeal", args=[claim_id], value=40 * GEN))
time.sleep(3)
wait("adjudicate#3", client.write_contract(CONTRACT, "adjudicate", args=[claim_id]))
time.sleep(3)
c = view("get_claim", [claim_id])
print(f"  final jury verdict: {c['verdict_label']} confidence={c['confidence']} appeals={c['appeals']}")

# --- 5. finalize (only now does trust update + stake settle) ---------------
print("\n5) FINALIZE (trust updates + stake settles HERE ONLY)…")
wait("finalize", client.write_contract(CONTRACT, "finalize", args=[claim_id]))
time.sleep(3)
c = view("get_claim", [claim_id])
t = view("get_trust", [subject])
acc = view("get_accounting", [])
print(f"  status={c['status']} verdict_final={c['verdict_final']} settled={c['settled']}")
print(f"  refund_owed={gen(int(c['refund_owed_wei']))}  trust score now={t['score']} total_verdicts={t['total_verdicts']}")
print(f"  accounting: treasury={gen(int(acc['treasury_wei']))} pending_refunds={gen(int(acc['pending_refunds_wei']))} solvent={acc['solvent']} conserved={acc['conserved']}")

# --- 6. claim refund --------------------------------------------------------
if int(c["refund_owed_wei"]) > 0:
    print("\n6) CLAIM REFUND (filer withdraws stake minus fee)…")
    bal_before = int(client.get_balance(acct.address))
    wait("claim_refund", client.write_contract(CONTRACT, "claim_refund", args=[claim_id]))
    time.sleep(5)
    bal_after = int(client.get_balance(acct.address))
    c = view("get_claim", [claim_id])
    print(f"  balance {gen(bal_before)} -> {gen(bal_after)}; refund_owed now={c['refund_owed_wei']}")

print(f"\nDONE. Explorer: https://explorer-studio.genlayer.com/address/{CONTRACT}")
