"""OATH MCP server — exposes the OATH trust API to any MCP-capable AI agent
(Claude Desktop, Cursor, Claude Code, …).

Tools
-----
    oath_get_trust(subject)              live time-decayed trust record
    oath_get_badge(subject)              attestation card (score, grade, svg)
    oath_get_claim(claim_id)             full claim record
    oath_get_verdict(claim_id)           verdict + rationale + citations
    oath_get_stats()                     protocol counters + configuration
    oath_list_categories()               claim categories -> jury rules
    oath_trust_gate(subjects, ...)       TRUSTED / UNTRUSTED decision

Configuration (environment variables)
-------------------------------------
    OATH_ADDRESS   deployed OathRegistry address (required)
    OATH_CHAIN     studionet | testnet_asimov | localnet   (default studionet)
    OATH_RPC       optional custom RPC endpoint
    OATH_KEY       optional funded private key — enables the write tools
                   (oath_file_claim / oath_adjudicate / …)

Run
---
    pip install genlayer-py mcp        # Python 3.12+
    python tools/mcp_server.py         # stdio transport

Claude Desktop / Cursor config example:
    {
      "mcpServers": {
        "oath": {
          "command": "python",
          "args": ["/path/to/OATH/tools/mcp_server.py"],
          "env": {"OATH_ADDRESS": "0x…", "OATH_CHAIN": "studionet"}
        }
      }
    }
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# allow `import oath_client` from the sdk/ folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sdk"))

try:
    # mcp 1.x (the widely deployed release)
    from mcp.server.fastmcp import FastMCP  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - mcp 2.x renamed FastMCP
    from mcp.server.mcpserver import MCPServer as FastMCP  # type: ignore


ADDRESS = os.environ.get("OATH_ADDRESS", "")
CHAIN = os.environ.get("OATH_CHAIN", "studionet")
RPC_URL = os.environ.get("OATH_RPC") or None
PRIVATE_KEY = os.environ.get("OATH_KEY") or None

mcp = FastMCP("oath")

_client = None


def _client_readonly():
    global _client
    if _client is None:
        from oath_client import OathClient
        _client = OathClient(address=ADDRESS, chain=CHAIN, rpc_url=RPC_URL)
    return _client


def _client_signing():
    from oath_client import OathClient
    if not PRIVATE_KEY:
        raise RuntimeError("write tools require the OATH_KEY environment variable")
    return OathClient(address=ADDRESS, chain=CHAIN, rpc_url=RPC_URL, private_key=PRIVATE_KEY)


def _need_address():
    if not ADDRESS:
        raise RuntimeError("set the OATH_ADDRESS environment variable to a deployed OathRegistry")


# ---------------------------------------------------------------------------
# read tools (always available)
# ---------------------------------------------------------------------------
@mcp.tool()
def oath_get_trust(subject: str) -> dict:
    """Live trust record for a subject: score (time-decayed), verdict counts,
    freshness window, last verdict. Call this before transacting."""
    _need_address()
    return _client_readonly().get_trust(subject)


@mcp.tool()
def oath_get_badge(subject: str) -> dict:
    """Machine-readable attestation card: score, grade A–F, color and an
    SVG badge ready to embed in a README or UI."""
    _need_address()
    return _client_readonly().get_badge(subject)


@mcp.tool()
def oath_get_claim(claim_id: int) -> dict:
    """Full on-chain record of a claim: subject, claim text, evidence URLs,
    status, verdict, stake, appeal state."""
    _need_address()
    return _client_readonly().get_claim(claim_id)


@mcp.tool()
def oath_get_verdict(claim_id: int) -> dict:
    """The jury's verdict for a claim: label, confidence, rationale, citations."""
    _need_address()
    return _client_readonly().get_verdict(claim_id)


@mcp.tool()
def oath_get_stats() -> dict:
    """Protocol counters (claims filed/adjudicated/contradicted/reverified,
    treasury) and configuration (min stake, fees, appeal terms, TTL)."""
    _need_address()
    return _client_readonly().get_stats()


@mcp.tool()
def oath_list_categories() -> dict:
    """The claim categories OATH supports and the extra judging rules each
    one adds to the jury prompt (audit, capability, compliance, tokenomics)."""
    _need_address()
    return _client_readonly().get_categories()


@mcp.tool()
def oath_trust_gate(subjects: list[str], min_score: int = 70,
                    require_fresh: bool = True) -> dict:
    """Decide whether to transact with the given subjects. Returns
    TRUSTED / UNTRUSTED plus per-subject reasons. THE agent primitive:
    call this before paying, shipping to, or signing with an unknown party."""
    _need_address()
    return _client_readonly().trust_gate(subjects, min_score=min_score,
                                         require_fresh=require_fresh)


# ---------------------------------------------------------------------------
# write tools (only when OATH_KEY is configured)
# ---------------------------------------------------------------------------
@mcp.tool()
def oath_file_claim(subject: str, claim_text: str, evidence_urls: list[str],
                    category: str = "general", stake_gen: float | None = None) -> dict:
    """File a claim against a subject with evidence URLs and a stake
    (staked GEN is refunded unless the claim is CONTRADICTED)."""
    _need_address()
    return _client_signing().file_claim(subject, claim_text, evidence_urls,
                                        category=category, stake_gen=stake_gen)


@mcp.tool()
def oath_adjudicate(claim_id: int) -> dict:
    """Run the OATH jury on a claim: fetches the evidence live, adjudicates
    with LLM consensus, writes the provisional verdict on-chain."""
    _need_address()
    return _client_signing().adjudicate(claim_id)


@mcp.tool()
def oath_finalize(claim_id: int) -> dict:
    """Finalize a claim once its appeal window has closed — this settles the
    stake and writes the verdict into the subject's trust score."""
    _need_address()
    return _client_signing().finalize(claim_id)


@mcp.tool()
def oath_reverify(claim_id: int, stake_gen: float | None = None) -> dict:
    """Reopen a finalized claim as a fresh one (freshness loop) when its
    verification has gone stale."""
    _need_address()
    return _client_signing().reverify(claim_id, stake_gen=stake_gen)


if __name__ == "__main__":
    mcp.run()  # stdio transport
