"""Structural contract for production and unit-test module alignment."""

from __future__ import annotations

from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PRODUCTION_ROOT = _REPOSITORY_ROOT / "mt5api"
_ROUTER_ROOT = _PRODUCTION_ROOT / "routers"
_TEST_ROOT = _REPOSITORY_ROOT / "tests"
_UNIT_ROOT = _TEST_ROOT / "unit"
_EXCLUDED_TOP_LEVEL_MODULES = {"__init__.py", "__main__.py"}


def _expected_unit_paths() -> set[Path]:
    """Build the unit-test paths required by the production package tree."""
    top_level_paths = {
        Path(f"test_{path.stem}.py")
        for path in _PRODUCTION_ROOT.glob("*.py")
        if path.name not in _EXCLUDED_TOP_LEVEL_MODULES
    }
    router_paths = {
        Path("routers") / path.relative_to(_ROUTER_ROOT).parent / f"test_{path.stem}.py"
        for path in _ROUTER_ROOT.rglob("*.py")
        if path.name != "__init__.py"
    }
    return top_level_paths | router_paths


def _actual_unit_test_paths() -> set[Path]:
    """Find collected-style Python test modules beneath the unit tree."""
    return {
        path.relative_to(_UNIT_ROOT)
        for path in _UNIT_ROOT.rglob("*.py")
        if path.name not in {"__init__.py", "conftest.py"}
        and (path.name.startswith("test_") or path.name.endswith("_test.py"))
    }


def test_unit_tests_mirror_production_modules() -> None:
    """Every eligible production module has exactly one aligned unit module."""
    expected = _expected_unit_paths()
    actual = _actual_unit_test_paths()
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    assert not missing, f"Missing unit tests: {missing}"
    assert not unexpected, f"Unexpected unit tests: {unexpected}"
    assert len(actual) == len(expected)


def test_unit_tree_does_not_reintroduce_flattened_tests() -> None:
    """Legacy flattened test modules remain outside the aligned unit tree."""
    legacy_paths = sorted(_TEST_ROOT.glob("test_*.py"))
    assert not legacy_paths, f"Legacy flattened tests: {legacy_paths}"
