from __future__ import annotations

import pytest


def test_health_endpoint() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from pdmt5_api.rest.app import create_app

    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["detail"] == {"status": "ok"}
