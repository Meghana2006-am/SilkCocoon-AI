"""
Tests for SilkCocoon AI Vercel WSGI entry points and REST API endpoints.
Verifies compatibility with Vercel Serverless Functions and local execution.
"""

import json
import pytest
from flask import Flask


def test_vercel_api_index_entrypoint():
    """Verify that api/index.py exports a valid WSGI callable for Vercel."""
    from api.index import app, handler

    assert app is not None
    assert isinstance(app, Flask)
    assert handler is app


def test_root_app_entrypoint():
    """Verify that root app.py exports a valid WSGI callable for Vercel fallback."""
    from app import app, handler

    assert app is not None
    assert isinstance(app, Flask)
    assert handler is app


def test_api_health_endpoint():
    """Verify GET /api/health returns 200 OK and JSON status."""
    from api_server import app

    client = app.test_client()
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert "SilkCocoon AI" in data["service"]
    assert "deployment" in data


def test_api_landing_page():
    """Verify GET / returns 200 OK with HTML content."""
    from api_server import app

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert "SilkCocoon AI" in response.get_data(as_text=True)


def test_api_standards_endpoint():
    """Verify GET /api/standards returns sericulture standards and defect weights."""
    from api_server import app

    client = app.test_client()
    response = client.get("/api/standards")

    assert response.status_code == 200
    data = response.get_json()
    assert "defect_penalties" in data
    assert "grade_thresholds" in data
    assert "Grade A" in data["grade_thresholds"]


def test_api_advisory_endpoint():
    """Verify POST /api/advisory endpoint handles queries."""
    from api_server import app

    client = app.test_client()
    response = client.post(
        "/api/advisory",
        json={"question": "What are the storage guidelines for Bivoltine cocoons?"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "advisory" in data
    assert "source" in data


def test_api_chat_endpoint():
    """Verify POST /api/chat endpoint handles farmer conversational assistant."""
    from api_server import app

    client = app.test_client()
    response = client.post(
        "/api/chat",
        json={"message": "Hello, how to test cocoon quality?"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "reply" in data
    assert "source" in data


def test_api_analyze_missing_image():
    """Verify POST /api/analyze returns 400 when no image is provided."""
    from api_server import app

    client = app.test_client()
    response = client.post("/api/analyze", json={})

    assert response.status_code == 400
    data = response.get_json()
    assert data["status"] == "ERROR"
