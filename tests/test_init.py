"""Tests for pdmt5 package initialization."""

import pytest

import pdmt5


class TestInit:
    """Test package initialization."""

    def test_version_attribute(self) -> None:
        """Test that __version__ attribute exists."""
        assert hasattr(pdmt5, "__version__")
        assert pdmt5.__version__ is not None

    @pytest.mark.parametrize(
        "export",
        [
            "Mt5Client",
            "Mt5Config",
            "Mt5DataClient",
            "Mt5RuntimeError",
            "Mt5TradingClient",
            "Mt5TradingError",
        ],
    )
    def test_exports_available(self, export: str) -> None:
        """Test that expected exports are accessible and listed in __all__."""
        assert hasattr(pdmt5, export), f"Missing export: {export}"
        assert export in pdmt5.__all__, f"Export {export} not in __all__"
