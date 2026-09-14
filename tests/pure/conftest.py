"""Minimal in-process stub of the `genlayer` module (and its runtime names) so
the contract's PURE helpers — prompt building, category rules, freshness math,
grading, badge rendering — can be imported and unit-tested without GenVM.

These tests run anywhere:  pytest tests/pure -v
(direct-mode consensus tests live in tests/direct and need the gltoolchain.)
"""

import json
import sys
import types

import pytest


# ---------------------------------------------------------------------------
# stub module: genlayer
# ---------------------------------------------------------------------------
def _make_stub():
    mod = types.ModuleType("genlayer")

    mod.u256 = lambda x: int(x)
    mod.Address = str
    mod.allow_storage = lambda cls: cls

    class TreeMap(dict):
        def get_or_insert_default(self, key):
            if key not in self:
                self[key] = None
            return self[key]

    mod.TreeMap = TreeMap

    def _decorator(f=None, **_kw):
        if f is not None:
            return f

        def inner(g):
            return g

        return inner

    _decorator.payable = _decorator

    class _Public:
        write = _decorator
        view = staticmethod(lambda f: f)

    class _VM:
        class UserError(Exception):
            pass

        class Return:
            def __init__(self, calldata=None):
                self.calldata = calldata

        class _Nondet:
            class web:
                pass

            @staticmethod
            def exec_prompt(*_a, **_k):  # pragma: no cover - never used in pure tests
                raise RuntimeError("nondet unavailable in pure tests")

        nondet = _Nondet()

    class _EVM:
        @staticmethod
        def contract_interface(cls):
            return cls

    class _Message:
        value = 0
        sender_address = "0x0"

    class _GL:
        Contract = object
        public = _Public
        vm = _VM
        evm = _EVM
        message = _Message

    mod.gl = _GL()
    return mod


@pytest.fixture(scope="session")
def oath():
    """The contract module, imported with the genlayer stub active."""
    stub = _make_stub()
    saved = sys.modules.get("genlayer")
    sys.modules["genlayer"] = stub
    import importlib.util
    from pathlib import Path

    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "oath_registry.py"
    spec = importlib.util.spec_from_file_location("oath_contract", str(contract_path))
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    finally:
        if saved is not None:
            sys.modules["genlayer"] = saved
        else:
            sys.modules.pop("genlayer", None)
    return m
