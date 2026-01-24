"""Test cases for pdmt5.utils module."""

# pyright: reportPrivateUsage=false

from collections.abc import Callable
from typing import Any

import pandas as pd
import pytest

from pdmt5.utils import (
    _convert_time_columns_in_df,
    _convert_time_values_in_dict,
    detect_and_convert_time_to_datetime,
    set_index_if_possible,
)


class TestConvertTimeValuesInDict:
    """Test _convert_time_values_in_dict function."""

    @pytest.mark.parametrize(
        ("input_factory", "expected"),
        [
            pytest.param(
                lambda: {
                    "time": 1704067200,  # 2024-01-01 00:00:00 UTC
                    "price": 100.5,
                    "volume": 1000,
                },
                {
                    "time": pd.Timestamp("2024-01-01 00:00:00"),
                    "price": 100.5,
                    "volume": 1000,
                },
                id="seconds",
            ),
            pytest.param(
                lambda: {
                    "time_msc": 1704067200000,
                    "time_setup_msc": 1704067200500,
                    "other_data": "test",
                },
                {
                    "time_msc": pd.Timestamp("2024-01-01 00:00:00"),
                    "time_setup_msc": pd.Timestamp("2024-01-01 00:00:00.500"),
                    "other_data": "test",
                },
                id="milliseconds",
            ),
            pytest.param(
                lambda: {
                    "time_setup": 1704067200,
                    "time_done": 1704067260,
                    "time_expiration": 1704067320,
                    "status": "complete",
                },
                {
                    "time_setup": pd.Timestamp("2024-01-01 00:00:00"),
                    "time_done": pd.Timestamp("2024-01-01 00:01:00"),
                    "time_expiration": pd.Timestamp("2024-01-01 00:02:00"),
                    "status": "complete",
                },
                id="prefixed-seconds",
            ),
            pytest.param(
                lambda: {
                    "time": "not a timestamp",
                    "time_text": "2024-01-01",
                    "time_none": None,
                },
                {
                    "time": "not a timestamp",
                    "time_text": "2024-01-01",
                    "time_none": None,
                },
                id="non-numeric",
            ),
            pytest.param(dict, {}, id="empty"),
            pytest.param(
                lambda: {"price": 100.5, "volume": 1000, "symbol": "EURUSD"},
                {"price": 100.5, "volume": 1000, "symbol": "EURUSD"},
                id="no-time-fields",
            ),
            pytest.param(
                lambda: {
                    "time_setup_msc": 1640995200000,
                    "time_done_msc": 1640995210000,
                    "regular_field": "unchanged",
                    "numeric_field": 123.45,
                },
                {
                    "time_setup_msc": pd.Timestamp("2022-01-01 00:00:00"),
                    "time_done_msc": pd.Timestamp("2022-01-01 00:00:10"),
                    "regular_field": "unchanged",
                    "numeric_field": 123.45,
                },
                id="additional-milliseconds",
            ),
            pytest.param(
                lambda: {
                    "time": 1640995200,
                    "time_setup": 1640995210,
                    "time_update": 1640995220,
                    "regular_field": "unchanged",
                    "string_field": "not_time",
                },
                {
                    "time": pd.Timestamp("2022-01-01 00:00:00"),
                    "time_setup": pd.Timestamp("2022-01-01 00:00:10"),
                    "time_update": pd.Timestamp("2022-01-01 00:00:20"),
                    "regular_field": "unchanged",
                    "string_field": "not_time",
                },
                id="additional-seconds",
            ),
        ],
    )
    def test_convert_time_values_in_dict(
        self,
        input_factory: Callable[[], dict[str, Any]],
        expected: dict[str, Any],
    ) -> None:
        """Test multiple time value conversion scenarios."""
        result = _convert_time_values_in_dict(input_factory())

        assert set(result.keys()) == set(expected.keys())
        for key, expected_value in expected.items():
            if isinstance(expected_value, pd.Timestamp):
                assert isinstance(result[key], pd.Timestamp)
            assert result[key] == expected_value


class TestConvertTimeColumnsInDf:
    """Test _convert_time_columns_in_df function."""

    @pytest.mark.parametrize(
        ("data_factory", "expected_dtypes", "expected_values", "expect_unchanged"),
        [
            pytest.param(
                lambda: pd.DataFrame({
                    "time": [1704067200, 1704067260, 1704067320],
                    "price": [100.5, 100.6, 100.7],
                }),
                {"time": "datetime64[ns]", "price": float},
                [("time", 0, pd.Timestamp("2024-01-01 00:00:00"))],
                False,
                id="seconds",
            ),
            pytest.param(
                lambda: pd.DataFrame({
                    "time_msc": [1704067200000, 1704067200500],
                    "time_setup_msc": [1704067201000, 1704067201500],
                    "volume": [100, 200],
                }),
                {
                    "time_msc": "datetime64[ns]",
                    "time_setup_msc": "datetime64[ns]",
                },
                [
                    ("time_msc", 0, pd.Timestamp("2024-01-01 00:00:00")),
                    ("time_setup_msc", 1, pd.Timestamp("2024-01-01 00:00:01.500")),
                ],
                False,
                id="milliseconds",
            ),
            pytest.param(
                lambda: pd.DataFrame({
                    "time_setup": [1704067200, 1704067260],
                    "time_done": [1704067260, 1704067320],
                    "status": ["pending", "complete"],
                }),
                {
                    "time_setup": "datetime64[ns]",
                    "time_done": "datetime64[ns]",
                    "status": object,
                },
                [],
                False,
                id="prefixed-seconds",
            ),
            pytest.param(
                pd.DataFrame,
                {},
                [],
                True,
                id="empty",
            ),
            pytest.param(
                lambda: pd.DataFrame({
                    "price": [100.5, 100.6],
                    "volume": [1000, 2000],
                    "symbol": ["EURUSD", "GBPUSD"],
                }),
                {},
                [],
                True,
                id="no-time-columns",
            ),
        ],
    )
    def test_convert_time_columns_in_df(
        self,
        data_factory: Callable[[], pd.DataFrame],
        expected_dtypes: dict[str, Any],
        expected_values: list[tuple[str, int, Any]],
        expect_unchanged: bool,
    ) -> None:
        """Test multiple time column conversion scenarios."""
        data_df = data_factory()
        original_df = data_df.copy(deep=True)

        result = _convert_time_columns_in_df(data_df)

        if expect_unchanged:
            pd.testing.assert_frame_equal(result, original_df)
            return

        for column, expected_dtype in expected_dtypes.items():
            assert result[column].dtype == expected_dtype

        for column, index, expected_value in expected_values:
            value = result[column].iloc[index]
            if isinstance(expected_value, pd.Timestamp):
                assert isinstance(value, pd.Timestamp)
            assert value == expected_value


class TestDetectAndConvertTimeToDatetime:
    """Test detect_and_convert_time_to_datetime decorator."""

    def test_decorator_with_dict_result(self) -> None:
        """Test decorator with function returning dict."""

        @detect_and_convert_time_to_datetime()
        def get_data() -> dict[str, Any]:
            return {"time": 1704067200, "price": 100.5}

        result = get_data()
        assert isinstance(result["time"], pd.Timestamp)
        assert result["time"] == pd.Timestamp("2024-01-01 00:00:00")

    def test_decorator_with_list_result(self) -> None:
        """Test decorator with function returning list of dicts."""

        @detect_and_convert_time_to_datetime()
        def get_data() -> list[dict[str, Any]]:
            return [
                {"time": 1704067200, "price": 100.5},
                {"time": 1704067260, "price": 100.6},
            ]

        result = get_data()
        assert len(result) == 2
        assert all(isinstance(d["time"], pd.Timestamp) for d in result)

    def test_decorator_with_dataframe_result(self) -> None:
        """Test decorator with function returning DataFrame."""

        @detect_and_convert_time_to_datetime()
        def get_data() -> pd.DataFrame:
            return pd.DataFrame({
                "time": [1704067200, 1704067260],
                "price": [100.5, 100.6],
            })

        result = get_data()
        assert result["time"].dtype == "datetime64[ns]"

    def test_decorator_with_skip_toggle(self) -> None:
        """Test decorator with skip_toggle parameter."""

        @detect_and_convert_time_to_datetime(skip_toggle="skip_to_datetime")
        def get_data(skip_to_datetime: bool = False) -> dict[str, Any]:  # noqa: ARG001
            return {"time": 1704067200, "price": 100.5}

        # With conversion (default)
        result1 = get_data(skip_to_datetime=False)
        assert isinstance(result1["time"], pd.Timestamp)

        # Without conversion
        result2 = get_data(skip_to_datetime=True)
        assert isinstance(result2["time"], int)
        assert result2["time"] == 1704067200

    def test_decorator_with_other_result_type(self) -> None:
        """Test decorator with function returning other types."""

        @detect_and_convert_time_to_datetime()
        def get_string() -> str:
            return "test string"

        @detect_and_convert_time_to_datetime()
        def get_number() -> int:
            return 42

        @detect_and_convert_time_to_datetime()
        def get_none() -> None:
            return None

        assert get_string() == "test string"
        assert get_number() == 42
        assert get_none() is None

    def test_decorator_with_list_of_mixed_types(self) -> None:
        """Test decorator with list containing mixed types."""

        @detect_and_convert_time_to_datetime()
        def get_data() -> list[Any]:
            return [
                {"time": 1704067200, "price": 100.5},
                "not a dict",
                42,
                None,
            ]

        result = get_data()
        assert isinstance(result[0]["time"], pd.Timestamp)
        assert result[1] == "not a dict"
        assert result[2] == 42
        assert result[3] is None


class TestSetIndexIfPossible:
    """Test set_index_if_possible decorator."""

    def test_decorator_with_index_parameter(self) -> None:
        """Test decorator with index parameter provided."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG001
            return pd.DataFrame({
                "symbol": ["EURUSD", "GBPUSD"],
                "price": [1.1, 1.3],
            })

        result = get_data(index_keys="symbol")
        assert result.index.name == "symbol"
        assert list(result.index) == ["EURUSD", "GBPUSD"]

    def test_decorator_without_index_parameter(self) -> None:
        """Test decorator without index parameter."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG001
            return pd.DataFrame({
                "symbol": ["EURUSD", "GBPUSD"],
                "price": [1.1, 1.3],
            })

        result = get_data()
        assert isinstance(result.index, pd.RangeIndex)

    def test_decorator_with_empty_dataframe(self) -> None:
        """Test decorator with empty DataFrame."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG001
            return pd.DataFrame()

        result = get_data(index_keys="symbol")
        assert result.empty

    def test_decorator_with_non_dataframe_raises(self) -> None:
        """Test decorator raises TypeError for non-DataFrame return."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: str | None = None) -> dict[str, Any]:  # noqa: ARG001
            return {"data": "not a dataframe"}

        with pytest.raises(
            TypeError,
            match=(
                r"Function get_data returned non-DataFrame result: "
                r"dict\. Expected DataFrame\."
            ),
        ):
            get_data()

    def test_decorator_with_no_index_parameters(self) -> None:
        """Test decorator with no index_parameters specified."""

        @set_index_if_possible()
        def get_data() -> pd.DataFrame:
            return pd.DataFrame({
                "symbol": ["EURUSD", "GBPUSD"],
                "price": [1.1, 1.3],
            })

        result = get_data()
        assert isinstance(result.index, pd.RangeIndex)

    def test_decorator_preserves_function_metadata(self) -> None:
        """Test decorator preserves original function metadata."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: str | None = None) -> pd.DataFrame:  # noqa: ARG001
            """Get test data."""
            return pd.DataFrame()

        assert get_data.__name__ == "get_data"
        assert get_data.__doc__ == "Get test data."

    def test_decorator_with_multiple_columns_index(self) -> None:
        """Test decorator with list of columns as index."""

        @set_index_if_possible(index_parameters="index_keys")
        def get_data(index_keys: list[str] | None = None) -> pd.DataFrame:  # noqa: ARG001
            return pd.DataFrame({
                "date": ["2024-01-01", "2024-01-02"],
                "symbol": ["EURUSD", "GBPUSD"],
                "price": [1.1, 1.3],
            })

        result = get_data(index_keys=["date", "symbol"])
        assert isinstance(result.index, pd.MultiIndex)
        assert result.index.names == ["date", "symbol"]
