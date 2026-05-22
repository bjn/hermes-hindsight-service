#!/usr/bin/env python3
"""Regression checks for the Hindsight 0.6.2 db_utils hotfix overlay."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path


def load_db_utils():
    # The patched file imports `.db.base.DatabaseBackend`; provide a tiny fake
    # package tree so this test can run without installing Hindsight itself.
    sys.modules["hindsight_api"] = types.ModuleType("hindsight_api")
    sys.modules["hindsight_api.engine"] = types.ModuleType("hindsight_api.engine")
    sys.modules["hindsight_api.engine.db"] = types.ModuleType("hindsight_api.engine.db")
    base = types.ModuleType("hindsight_api.engine.db.base")

    class DatabaseBackend:
        pass

    base.DatabaseBackend = DatabaseBackend
    sys.modules["hindsight_api.engine.db.base"] = base

    path = Path(__file__).resolve().parents[1] / "patches" / "hindsight_api" / "engine" / "db_utils.py"
    spec = importlib.util.spec_from_file_location("hindsight_api.engine.db_utils", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, DatabaseBackend


async def main() -> None:
    db_utils, DatabaseBackend = load_db_utils()

    class FakeContextManager:
        def __init__(self, backend):
            self.backend = backend

        async def __aenter__(self):
            self.backend.enter_calls += 1
            if self.backend.fail_enters:
                self.backend.fail_enters -= 1
                raise TimeoutError("connect timeout")
            return "conn"

        async def __aexit__(self, exc_type, exc, tb):
            self.backend.exit_args = (exc_type, type(exc).__name__ if exc else None)
            return False

    class FakeBackend(DatabaseBackend):
        def __init__(self, fail_enters: int = 0):
            self.fail_enters = fail_enters
            self.enter_calls = 0
            self.exit_args = None

        def acquire(self):
            return FakeContextManager(self)

    backend = FakeBackend(fail_enters=1)
    async with db_utils.acquire_with_retry(backend, max_retries=2) as conn:
        assert conn == "conn"
    assert backend.enter_calls == 2
    assert backend.exit_args == (None, None)

    backend = FakeBackend()
    try:
        async with db_utils.acquire_with_retry(backend, max_retries=2):
            raise asyncio.TimeoutError("operation timeout")
    except asyncio.TimeoutError:
        pass
    else:
        raise AssertionError("operation timeout was swallowed or retried")
    assert backend.enter_calls == 1
    assert backend.exit_args[0] is asyncio.TimeoutError


if __name__ == "__main__":
    asyncio.run(main())
    print("db_utils hotfix regression checks passed")
