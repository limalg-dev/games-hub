"""
Tests for Security Remediation (Workstream A - Backend Hardening)
Validates:
- IP validation in app/boletos.py against malicious headers
- Startup weak secret detection when ENVIRONMENT=production
- HTTP Security Headers in app/main.py middleware
- Input sanitization on POST /api/words
- Highscore player name sanitization across game routers
"""

from __future__ import annotations
import os
import pytest
from fastapi.testclient import TestClient
from fastapi import Request
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.boletos import _get_client_ip, _logs

client = TestClient(app)


def test_ip_validation_in_get_client_ip():
    # Valid IPv4
    class MockRequest:
        def __init__(self, headers, client_host=None):
            self.headers = headers
            self.client = type("Client", (), {"host": client_host})() if client_host else None

    # Valid IP
    req_valid = MockRequest(headers={"x-forwarded-for": "192.168.1.100"})
    assert _get_client_ip(req_valid) == "192.168.1.100"

    # Valid IPv6
    req_v6 = MockRequest(headers={"x-forwarded-for": "2001:db8::1"})
    assert _get_client_ip(req_v6) == "2001:db8::1"

    # Malicious XSS payload in X-Forwarded-For
    req_xss = MockRequest(headers={"x-forwarded-for": "<script>alert('xss')</script>"})
    assert _get_client_ip(req_xss) == "invalido"

    # Malicious injection in X-Real-IP
    req_real_xss = MockRequest(headers={"x-real-ip": "javascript:alert(1)"})
    assert _get_client_ip(req_real_xss) == "invalido"

    # Fallback to valid client.host
    req_client = MockRequest(headers={}, client_host="10.0.0.1")
    assert _get_client_ip(req_client) == "10.0.0.1"


def test_boletos_login_logs_sanitized_ip():
    # Attempt login with malicious X-Forwarded-For
    headers = {"X-Forwarded-For": "<img src=x onerror=alert(1)>"}
    response = client.post(
        "/boletos/api/login",
        json={"username": "fake_user", "password": "wrong_password"},
        headers=headers,
    )
    assert response.status_code == 401
    # Check log entry
    if _logs:
        latest_log = _logs[0]
        assert "<img" not in latest_log["ip"]
        assert latest_log["ip"] == "invalido"


@pytest.mark.asyncio
async def test_security_headers_present():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/")
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        csp = resp.headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in csp
        assert "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com" in csp
        assert "connect-src 'self' ws: wss:" in csp


def test_create_word_sanitization():
    # Post word with XSS payload
    payload = {
        "word": "<script>alert('pwned')</script>",
        "hint": "Dica com <b>HTML</b> e <img src=x onerror=alert(1)>",
        "category": "tecnologia",
        "difficulty": 1,
    }
    response = client.post("/api/words", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "<script>" not in data["word"]
    assert "&lt;script&gt;" in data["word"]
    assert "<img" not in data["hint"]
    assert "&lt;img" in data["hint"]


def test_bomberman_highscore_sanitization():
    response = client.post(
        "/api/bomberman/highscores",
        json={
            "name": "<script>HACK</script>",
            "score": 9999,
            "mode": "battle",
            "difficulty": "hard",
        },
    )
    assert response.status_code == 200
    entry = response.json()["entry"]
    assert "<script>" not in entry["name"]
    assert "&lt;SCRIPT&gt;" in entry["name"] or "&LT;SCRIPT&GT;" in entry["name"] or "&lt;script&gt;" in entry["name"].lower()


def test_tower_defense_highscore_sanitization():
    response = client.post(
        "/tower-defense/highscores",
        json={
            "name": "<svg onload=alert(1)>",
            "score": 15000,
            "difficulty": "normal",
            "waves_cleared": 10,
            "victory": False,
        },
    )
    assert response.status_code == 200
    entry = response.json()["entry"]
    assert "<svg" not in entry["name"]
    assert "&lt;SVG" in entry["name"] or "&lt;svg" in entry["name"].lower()


def test_colonia_hex_highscore_sanitization():
    response = client.post(
        "/colonia-hex/api/highscores",
        json={
            "player_name": "<script>alert(1)</script>",
            "score": 1800,
            "difficulty": "medium",
            "turns": 15,
            "map_size": "small",
            "won": True,
        },
    )
    assert response.status_code == 200
    entry = response.json()["entry"]
    assert "<script>" not in entry["name"]
    assert "&lt;SCRIPT&gt;" in entry["name"] or "&lt;script&gt;" in entry["name"].lower()


@pytest.mark.asyncio
async def test_production_secret_warning(monkeypatch, caplog):
    import logging
    from app.main import lifespan
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("BOLETOS_PASS", "change-me")
    with caplog.at_level(logging.WARNING, logger="uvicorn.error"):
        async with lifespan(app):
            pass
    assert any("SECURITY WARNING" in record.message for record in caplog.records)
