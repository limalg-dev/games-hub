"""Boleto com senha: o PDF baixado com ?senha=1 vem criptografado."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token() -> str:
    res = client.post("/boletos/api/login", json={"username": "lima", "password": "12345678"})
    assert res.status_code == 200
    return res.json()["token"]


def _baixar(params: str) -> bytes:
    res = client.get(f"/boletos/api/download/teste{params}", headers={"Authorization": f"Bearer {_token()}"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    return res.content


def test_boleto_sem_senha_nao_e_criptografado():
    assert b"/Encrypt" not in _baixar("")


def test_boleto_com_senha_e_criptografado():
    pdf = _baixar("?senha=1")
    assert pdf.startswith(b"%PDF")
    assert b"/Encrypt" in pdf


def test_nome_do_arquivo_com_senha():
    res = client.get("/boletos/api/download/abc?senha=1", headers={"Authorization": f"Bearer {_token()}"})
    assert 'filename="boleto_abc_senha.pdf"' in res.headers["content-disposition"]
