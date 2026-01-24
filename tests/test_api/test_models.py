"""Tests for API request models."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from pdmt5.api.models import HistoryOrdersRequest


def test_history_request_requires_filters() -> None:
    """History requests must include date range or ticket/position."""
    with pytest.raises(ValueError, match="Either"):
        HistoryOrdersRequest()


def test_history_request_rejects_invalid_date_range() -> None:
    """History requests reject date ranges where start >= end."""
    with pytest.raises(ValueError, match="date_from must be before date_to"):
        HistoryOrdersRequest(
            date_from=datetime(2024, 1, 2, tzinfo=UTC),
            date_to=datetime(2024, 1, 1, tzinfo=UTC),
        )
