"""Run the test-suite with or without pytest installed.

The tests are written for pytest, because that is what an adopting agency will
have. This runner exists so that they also run on a bare Python with nothing
installed — which is the situation in a locked-down government environment, and
the situation this project promised to support.

    python tests/run_tests.py
"""

from __future__ import annotations

import importlib
import io
import math
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))


def _install_pytest_shim() -> None:
    try:
        import pytest  # noqa: F401
        return
    except ImportError:
        pass

    import types

    shim = types.ModuleType("pytest")

    class _Approx:
        def __init__(self, expected, rel=None, abs=None):
            self.expected = expected
            self.rel = rel
            self.abs = abs

        def _cmp(self, actual, expected) -> bool:
            if self.abs is not None:
                return math.isclose(actual, expected, abs_tol=self.abs)
            rel = self.rel if self.rel is not None else 1e-6
            return math.isclose(actual, expected, rel_tol=rel, abs_tol=1e-12)

        def __eq__(self, actual):
            if isinstance(self.expected, (list, tuple)):
                return (len(actual) == len(self.expected)
                        and all(self._cmp(a, e)
                                for a, e in zip(actual, self.expected)))
            return self._cmp(float(actual), float(self.expected))

        def __repr__(self):
            return f"approx({self.expected!r}, rel={self.rel}, abs={self.abs})"

    class _Raises:
        def __init__(self, exc, match=None):
            self.exc = exc
            self.match = match
            self.value = None

        def __enter__(self):
            return self

        def __exit__(self, et, ev, tb):
            if et is None:
                raise AssertionError(f"DID NOT RAISE {self.exc}")
            self.value = ev
            return issubclass(et, self.exc)

    class _MarkStub:
        def __getattr__(self, _name):
            def deco(fn=None, **_kw):
                return fn if fn is not None else (lambda f: f)
            return deco

    shim.approx = _Approx
    shim.raises = _Raises
    shim.mark = _MarkStub()
    shim.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
    shim.skip = lambda *a, **k: None
    sys.modules["pytest"] = shim


def main() -> int:
    _install_pytest_shim()
    modules = sorted(p.stem for p in (ROOT / "tests").glob("test_*.py"))
    passed = failed = 0
    failures = []
    for name in modules:
        mod = importlib.import_module(name)
        for attr in sorted(dir(mod)):
            if not attr.startswith("test_"):
                continue
            fn = getattr(mod, attr)
            if not callable(fn):
                continue
            try:
                with redirect_stdout(io.StringIO()):
                    fn()
                passed += 1
                print(f"  ok    {name}.{attr}")
            except Exception:
                failed += 1
                failures.append((f"{name}.{attr}", traceback.format_exc()))
                print(f"  FAIL  {name}.{attr}")
    print()
    for label, tb in failures:
        print("=" * 70)
        print(label)
        print(tb)
    print(f"{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
