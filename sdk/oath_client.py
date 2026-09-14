"""OATH SDK — a thin agent-facing client for the OATH Claim Verification
Protocol on GenLayer.

Wraps `genlayer_py` (https://pypi.org/project/genlayer-py/, Python 3.12+) so
any agent, marketplace or service can query trust scores, badges and verdicts
— and file, adjudicate, appeal, finalize and reverify claims — without
touching calldata by hand.

Quickstart (reads — no key needed):

    from oath_client import OathClient
    oath = OathClient(address="0x…", chain="studionet")
    oath.get_trust("example.com")
    oath.badge_svg("example.com")            # README-ready badge
    oath.trust_gate(["vendor.example"])      # TRUSTED / UNTRUSTED decision

Writes (needs a funded key on the target network):

    oath = OathClient(address="0x…", chain="studionet", private_key=os.environ["KEY"])
    oath.file_claim("example.com", "This vendor holds a current SOC 2 report.",
                    ["https://vendor.example/soc2"], category="compliance")
"""

from __future__ import annotations

import time

GEN_TO_WEI = 10 ** 18

CHAIN_NAMES = ("studionet", "testnet_asimov", "localnet")

VERDICT_LABELS = {
    0: "NONE",
    1: "VERIFIED",
    2: "PARTIALLY_VERIFIED",
    3: "CONTRADICTED",
    4: "UNVERIFIABLE",
}


class OathError(RuntimeError):
    pass


class OathClient:
    """Read-mostly client with optional signing for write transactions."""

    def __init__(self, address: str, chain: str = "studionet",
                 rpc_url: str | None = None, private_key: str | None = None):
        if chain not in CHAIN_NAMES:
            raise OathError(f"chain must be one of {CHAIN_NAMES}, got {chain!r}")
        self.address = address
        self.chain_name = chain
        self._client = None          # genlayer_py client (lazy)
        self._read_account = None    # burner account, for reads
        self._private_key = private_key
        self._rpc_url = rpc_url

    # ------------------------------------------------------------------
    # plumbing
    # ------------------------------------------------------------------
    def _ensure_client(self):
        if self._client is not None:
            return self._client
        try:
            from genlayer_py import create_client, chains
            from eth_account import Account
        except ImportError as e:  # pragma: no cover - depends on env
            raise OathError(
                "OathClient requires genlayer-py (Python 3.12+): pip install genlayer-py"
            ) from e

        chain_cfg = getattr(chains, self.chain_name)
        kwargs = {}
        if self._rpc_url:
            kwargs["endpoint"] = self._rpc_url
        # genlayer_py needs a sender even for reads — use a burner unless a
        # signing key was provided.
        account = (Account.from_key(self._private_key) if self._private_key
                   else Account.create("oath-readonly"))
        self._read_account = account
        self._client = create_client(chain=chain_cfg, account=account, **kwargs)
        return self._client

    def _read(self, function_name: str, args: list | None = None):
        client = self._ensure_client()
        return client.read_contract(self.address, function_name, args=args or [])

    def _write(self, function_name: str, args: list | None = None, value: int = 0):
        if not self._private_key:
            raise OathError(
                f"{function_name} is a write — construct OathClient with private_key="
            )
        client = self._ensure_client()
        return client.write_contract(self.address, function_name,
                                     args=args or [], value=value)

    # ------------------------------------------------------------------
    # reads — the machine-queryable trust API
    # ------------------------------------------------------------------
    def get_trust(self, subject: str) -> dict:
        """Live trust record for a subject (score is time-decayed)."""
        return self._read("get_trust", [subject])

    def get_trust_batch(self, subjects: list[str]) -> list[dict]:
        """Trust records for many subjects in one call."""
        return json_loads(self._read("get_trust_batch", [json_dumps(subjects)]))

    def get_badge(self, subject: str) -> dict:
        """Machine-readable attestation card (score, grade, color, svg)."""
        return self._read("get_badge", [subject])

    def badge_svg(self, subject: str) -> str:
        """The rendered SVG badge string — embed it in a README or UI."""
        return str(self.get_badge(subject).get("svg", ""))

    def get_claim(self, claim_id: int) -> dict:
        return self._read("get_claim", [int(claim_id)])

    def get_verdict(self, claim_id: int) -> dict:
        return self._read("get_verdict", [int(claim_id)])

    def get_stats(self) -> dict:
        return self._read("get_stats", [])

    def get_categories(self) -> dict:
        """Claim category keys -> the judging rules each adds to the jury."""
        return self._read("get_categories", [])

    def get_appeal_terms(self) -> dict:
        return self._read("get_appeal_terms", [])

    def get_accounting(self) -> dict:
        return self._read("get_accounting", [])

    def min_stake_wei(self) -> int:
        return int(self.get_stats().get("min_stake_wei", 10 * GEN_TO_WEI))

    # ------------------------------------------------------------------
    # writes — the claim lifecycle
    # ------------------------------------------------------------------
    def file_claim(self, subject: str, claim_text: str, evidence_urls: list[str],
                   category: str = "general", stake_gen: float | None = None) -> dict:
        """File a claim with a stake (defaults to the contract minimum)."""
        stake = int(stake_gen * GEN_TO_WEI) if stake_gen is not None else self.min_stake_wei()
        return self._write("file_claim",
                           [subject, claim_text, json_dumps(list(evidence_urls)), category],
                           value=stake)

    def adjudicate(self, claim_id: int) -> dict:
        """Run the jury on a PENDING/APPEALING claim."""
        return self._write("adjudicate", [int(claim_id)])

    def appeal(self, claim_id: int, stake_gen: float | None = None) -> dict:
        """Appeal a VERDICTED claim; stake defaults to the quoted price."""
        stake = (int(stake_gen * GEN_TO_WEI) if stake_gen is not None
                 else int(self.get_claim(claim_id).get("next_appeal_stake_wei", 0)))
        return self._write("appeal", [int(claim_id)], value=stake)

    def finalize(self, claim_id: int) -> dict:
        """Lock the verdict after the appeal window; settles stake + trust."""
        return self._write("finalize", [int(claim_id)])

    def reverify(self, claim_id: int, stake_gen: float | None = None) -> dict:
        """Reopen a FINAL claim as a fresh one (the freshness loop)."""
        stake = int(stake_gen * GEN_TO_WEI) if stake_gen is not None else self.min_stake_wei()
        return self._write("reverify", [int(claim_id)], value=stake)

    def claim_refund(self, claim_id: int) -> dict:
        return self._write("claim_refund", [int(claim_id)])

    # ------------------------------------------------------------------
    # agent helpers — "check before you transact"
    # ------------------------------------------------------------------
    def trust_gate(self, subjects: list[str], min_score: int = 70,
                   require_fresh: bool = True) -> dict:
        """Decide whether to transact with these subjects.

        A subject passes when its live trust score >= min_score and (by
        default) at least one positive FINAL verdict is still inside its
        freshness window. Returns a machine-readable decision dict.
        """
        records = self.get_trust_batch(list(subjects))
        results = {}
        ok = True
        for r in records:
            subject = r.get("subject", "?")
            score = int(r.get("score", 50))
            fresh = bool(r.get("fresh", False))
            no_data = int(r.get("total_verdicts", 0)) == 0
            reasons = []
            if no_data:
                reasons.append("no final verdicts on record (unverified)")
            if score < min_score:
                reasons.append(f"score {score} < required {min_score}")
            if require_fresh and not fresh and not no_data:
                reasons.append("no verdict inside the freshness window — request reverification")
            passed = not reasons
            ok = ok and passed
            results[subject] = {
                "pass": passed,
                "score": score,
                "fresh": fresh,
                "grade": r.get("last_verdict_label", "NO_DATA"),
                "reasons": reasons,
            }
        return {
            "schema": "oath.trust_gate.v1",
            "decision": "TRUSTED" if ok else "UNTRUSTED",
            "min_score": min_score,
            "require_fresh": require_fresh,
            "subjects": results,
        }


# ----------------------------------------------------------------------
# small json helpers (keep the module import-light)
# ----------------------------------------------------------------------
def json_dumps(obj) -> str:
    import json
    return json.dumps(obj)


def json_loads(text):
    import json
    if isinstance(text, (dict, list)):
        return text
    return json.loads(text)
