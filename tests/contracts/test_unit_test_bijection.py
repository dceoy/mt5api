"""Structural contract for production and unit-test module alignment."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PRODUCTION_ROOT = _REPOSITORY_ROOT / "mt5api"
_ROUTER_ROOT = _PRODUCTION_ROOT / "routers"
_TEST_ROOT = _REPOSITORY_ROOT / "tests"
_UNIT_ROOT = _TEST_ROOT / "unit"
_EXCLUDED_TOP_LEVEL_MODULES = {"__init__.py", "__main__.py"}


def _is_pytest_test_module(path: Path) -> bool:
    """Check whether a path matches either configured pytest file pattern."""
    return path.name.startswith("test_") or path.name.endswith("_test.py")


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


def _actual_unit_test_paths(request: pytest.FixtureRequest) -> set[Path]:
    """Find collected Python test modules beneath the unit tree."""
    actual: set[Path] = set()
    for item in request.session.items:
        path = Path(item.path).resolve()
        try:
            relative_path = path.relative_to(_UNIT_ROOT)
        except ValueError:
            continue
        if _is_pytest_test_module(relative_path):
            actual.add(relative_path)
    return actual


def _resolve_collection_argument(argument: str, *, pyargs: bool) -> Path:
    """Resolve a pytest collection argument to its filesystem path."""
    if not pyargs:
        return Path(argument).resolve()
    module_name = argument.split("::", maxsplit=1)[0]
    try:
        spec = importlib.util.find_spec(module_name)
    except (AttributeError, ImportError, ValueError):
        return Path(argument).resolve()
    if spec is None:
        return Path(argument).resolve()
    if spec.submodule_search_locations:
        return Path(spec.submodule_search_locations[0]).resolve()
    if spec.origin:
        return Path(spec.origin).resolve()
    return Path(argument).resolve()


def _is_full_test_suite(request: pytest.FixtureRequest) -> bool:
    """Check whether pytest selected the complete configured test tree."""
    collection_filters = (
        "-k",
        "-m",
        "--ignore",
        "--ignore-glob",
        "--deselect",
        "--lf",
        "--stepwise",
        "--stepwise-skip",
        "--stepwise-reset",
        "--override-ini",
    )
    if any(
        request.config.getoption(option, default=False) for option in collection_filters
    ):
        return False
    if request.config.getoption("--last-failed-no-failures", default="all") != "all":
        return False
    if any("::" in argument for argument in request.config.args):
        return False
    selected_paths = {
        _resolve_collection_argument(
            argument,
            pyargs=request.config.getoption("--pyargs", default=False),
        )
        for argument in request.config.args
    }
    if not selected_paths:
        return True
    test_root = _TEST_ROOT.resolve()
    if any(test_root.is_relative_to(path) for path in selected_paths):
        return True
    test_modules = {
        path.resolve()
        for path in test_root.rglob("*.py")
        if _is_pytest_test_module(path)
    }
    return bool(test_modules) and all(
        any(test_module.is_relative_to(path) for path in selected_paths)
        for test_module in test_modules
    )


def test_actual_unit_test_paths_only_includes_collected_modules(
    mocker: MockerFixture,
) -> None:
    """Only modules represented by collected pytest items count as unit tests."""
    request = mocker.Mock()
    request.session.items = [
        mocker.Mock(path=_UNIT_ROOT / "test_collected.py"),
    ]

    actual = _actual_unit_test_paths(request)

    assert actual == {Path("test_collected.py")}
    assert Path("test_empty.py") not in actual


@pytest.mark.parametrize(
    ("arguments", "pyargs", "expected"),
    [
        pytest.param(
            [_UNIT_ROOT, _TEST_ROOT / "contracts", _TEST_ROOT / "integration"],
            False,
            True,
            id="all-test-directories",
        ),
        pytest.param([_UNIT_ROOT], False, False, id="unit-only"),
        pytest.param(
            ["tests.unit", "tests.contracts", "tests.integration"],
            True,
            True,
            id="all-test-packages",
        ),
        pytest.param(
            [
                "tests.unit.test_auth::test_version_endpoint_requires_authentication",
                "tests.contracts.test_openapi::test_docs_and_openapi_available",
                "tests.integration.test_cli::test_main_uses_defaults",
            ],
            True,
            False,
            id="selected-test-packages",
        ),
    ],
)
def test_positional_paths_detect_complete_test_tree(
    mocker: MockerFixture,
    arguments: list[str | Path],
    pyargs: bool,
    expected: bool,
) -> None:
    """Complete positional test paths still run the full bijection check."""
    request = mocker.Mock()
    request.config.args = [str(argument) for argument in arguments]

    def get_option(option: str, default: object = False) -> object:
        return pyargs if option == "--pyargs" else default

    request.config.getoption.side_effect = get_option

    assert _is_full_test_suite(request) is expected


@pytest.mark.parametrize(
    "filter_option",
    [
        "-k",
        "-m",
        "--ignore",
        "--ignore-glob",
        "--deselect",
        "--lf",
        "--stepwise",
        "--stepwise-skip",
        "--stepwise-reset",
        "--override-ini",
    ],
)
def test_collection_filters_do_not_run_full_bijection(
    mocker: MockerFixture,
    filter_option: str,
) -> None:
    """Collection filters must not make the contract inspect partial items."""
    request = mocker.Mock()
    request.config.args = []

    def get_option(option: str, default: object = False) -> object:
        return filter_option if option == filter_option else default

    request.config.getoption.side_effect = get_option

    assert not _is_full_test_suite(request)


def test_last_failed_no_failures_filter_is_not_a_full_suite(
    mocker: MockerFixture,
) -> None:
    """A no-failures policy can deselect the collected test items."""
    request = mocker.Mock()
    request.config.args = []

    def get_option(option: str, default: object = False) -> object:
        return "none" if option == "--last-failed-no-failures" else default

    request.config.getoption.side_effect = get_option

    assert not _is_full_test_suite(request)


def test_unregistered_collection_options_use_safe_defaults(
    mocker: MockerFixture,
) -> None:
    """Optional pytest plugins may not register every collection option."""
    request = mocker.Mock()
    request.config.args = []

    def get_option(_option: str, default: object = False) -> object:
        return default

    request.config.getoption.side_effect = get_option

    assert _is_full_test_suite(request)


def test_unit_tests_mirror_production_modules(
    request: pytest.FixtureRequest,
) -> None:
    """Every eligible production module has exactly one aligned unit module."""
    if not _is_full_test_suite(request):
        pytest.skip("unit-test bijection requires an unfiltered test suite")
    expected = _expected_unit_paths()
    actual = _actual_unit_test_paths(request)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)

    assert not missing, f"Missing unit tests: {missing}"
    assert not unexpected, f"Unexpected unit tests: {unexpected}"
    assert len(actual) == len(expected)


def test_unit_tree_does_not_reintroduce_flattened_tests() -> None:
    """Legacy flattened test modules remain outside the aligned unit tree."""
    legacy_paths = sorted(
        path for path in _TEST_ROOT.glob("*.py") if _is_pytest_test_module(path)
    )
    assert not legacy_paths, f"Legacy flattened tests: {legacy_paths}"
