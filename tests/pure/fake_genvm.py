"""An in-process fake GenVM, just rich enough to execute OathRegistry's
state machine (file -> adjudicate -> finalize -> reverify -> views) without
the GenLayer toolchain.

This is a TEST HARNESS, not a GenLayer implementation: consensus is collapsed
(run_nondet_unsafe runs the leader function once and validates its shape),
storage is plain zero-initialized dataclasses in dicts, and web/LLM calls are
mock registries. It lets CI run state-machine tests anywhere; the
authoritative direct-mode tests remain tests/direct/ (real gltoolchain).
"""

import dataclasses
import importlib.util
import re
import sys
import types
from pathlib import Path

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "oath_registry.py"


class UserError(Exception):
    """gl.vm.UserError — reverts with a human-readable message."""


class Return:
    """gl.vm.Return — a successful nondet result envelope."""

    def __init__(self, calldata=None):
        self.calldata = calldata


def _allow_storage(cls):
    """Zero-initialize every storage field; allow positional/kw construction."""
    fields = [(f.name, f.type) for f in dataclasses.fields(cls)]

    def __init__(self, *args, **kwargs):
        for name, t in fields:
            setattr(self, name, "" if t is str else 0)
        for (name, _t), val in zip(fields, args):
            setattr(self, name, val)
        for k, v in kwargs.items():
            setattr(self, k, v)

    cls.__init__ = __init__
    return cls


class _ZeroDict(dict):
    """TreeMap stand-in whose missing keys zero-initialize on demand."""

    def __init__(self, zero_factory):
        super().__init__()
        self._zero = zero_factory

    def get_or_insert_default(self, key):
        if key not in self:
            self[key] = self._zero()
        return self[key]


def _write(f=None):
    """@gl.public.write  /  @gl.public.write.payable"""
    if f is not None:
        return f
    return lambda g: g


_write.payable = _write


class _Public:
    view = staticmethod(lambda f: f)
    write = staticmethod(_write)


def _run_nondet_unsafe(leader_fn, validator_fn):
    """Collapsed consensus: leader runs once, validator checks the shape."""
    result = leader_fn()
    if not validator_fn(Return(result)):
        raise UserError("consensus failed (fake vm)")
    return result


class FakeGenLayer:
    """The `genlayer` module stand-in + mutable test controls."""

    def __init__(self):
        self.message = types.SimpleNamespace(value=0, sender_address="0xrequester")
        self.WEB_BODIES = {}       # url regex -> body (None = fetch failure)
        self.LLM_RESPONSES = []    # (prompt regex, payload)
        self.gl = self
        self.Contract = object
        self.u256 = lambda x: int(x)
        self.Address = str
        self.TreeMap = dict
        self.allow_storage = _allow_storage
        self.public = _Public()
        self.vm = types.SimpleNamespace(
            UserError=UserError, Return=Return, run_nondet_unsafe=_run_nondet_unsafe,
        )
        self.evm = types.SimpleNamespace(
            contract_interface=lambda cls: (
                setattr(cls, "emit_transfer", staticmethod(lambda value=0: None)) or cls
            ),
        )
        self.nondet = types.SimpleNamespace(
            web=types.SimpleNamespace(render=self._render),
            exec_prompt=self._exec_prompt,
        )

    # -- mock registries ------------------------------------------------------
    def _render(self, url, mode="text"):
        for pattern, body in self.WEB_BODIES.items():
            if re.search(pattern, url):
                if body is None:
                    raise RuntimeError(f"web fetch failed: {url}")
                return body
        raise RuntimeError(f"web fetch failed: {url}")

    def _exec_prompt(self, prompt, response_format=None):
        for pattern, payload in self.LLM_RESPONSES:
            if re.search(pattern, prompt):
                return payload
        raise RuntimeError("no LLM mock matched the prompt")


def load_contract():
    """Import contracts/oath_registry.py against the fake VM.

    Returns (FakeOath factory, fake controls)."""
    fake = FakeGenLayer()
    saved = sys.modules.get("genlayer")
    sys.modules["genlayer"] = fake
    try:
        spec = importlib.util.spec_from_file_location("oath_contract_stateful", str(CONTRACT_PATH))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        if saved is not None:
            sys.modules["genlayer"] = saved
        else:
            sys.modules.pop("genlayer", None)

    class Deployed:
        def __init__(self, **ctor):
            self.fake = fake
            self.m = m
            self.contract = m.OathRegistry(**ctor)
            # inject storage proxies (GenVM would auto-provision these)
            self.contract.claims = _ZeroDict(m.Claim)
            self.contract.subjects = _ZeroDict(m.SubjectScore)

        @property
        def sender(self):
            return fake.message.sender_address

        @sender.setter
        def sender(self, addr):
            fake.message.sender_address = addr

        @property
        def value(self):
            return fake.message.value

        @value.setter
        def value(self, v):
            fake.message.value = v

        def mock_web(self, pattern, body):
            fake.WEB_BODIES[pattern] = body

        def mock_llm(self, pattern, payload):
            fake.LLM_RESPONSES.append((pattern, payload))

        def clear_mocks(self):
            fake.WEB_BODIES.clear()
            fake.LLM_RESPONSES.clear()

        def __getattr__(self, name):
            return getattr(self.contract, name)

    return Deployed, fake


def reverts(deployed, fragment, fn, *args, **kwargs):
    """Call fn on the deployed contract, assert UserError containing fragment."""
    try:
        fn(*args, **kwargs)
    except UserError as e:
        assert fragment in str(e), f"revert message {str(e)!r} missing {fragment!r}"
        return
    raise AssertionError(f"expected revert containing {fragment!r}, but nothing raised")
