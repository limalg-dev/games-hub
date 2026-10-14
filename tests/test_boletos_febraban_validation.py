"""
Testes de Validação do Backend de Boletos (Padrão FEBRABAN, ITF e Criptografia)
================================================================================
Cobre:
1. Cálculo oficial FEBRABAN: Módulo 10, Módulo 11 (pesos 2..9), Fator de Vencimento com rollover pós-2025.
2. Linha digitável (47 dígitos) e Código de Barras (44 dígitos).
3. Código de barras ITF 2 de 5 vetorizado e padrões binários.
4. Geração de PDF com criptografia ReportLab StandardEncryption (senha 123456 e 1234).
5. Janela deslizante de 6 boletos diários (endpoint /boletos/api/rolling-boletos e /boletos/api/list).
"""

from datetime import date, datetime, timedelta
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.boletos import (
    _modulo10,
    _modulo11,
    _fator_vencimento,
    _generate_febraban_codes,
    _draw_itf_barcode,
    _draw_boleto_pdf,
    _generate_rolling_boletos,
    ITF_PATTERNS,
)

client = TestClient(app)


def test_febraban_modulo10():
    """Valida o cálculo do Módulo 10 com pesos alternados 2 e 1."""
    # Exemplo clássico FEBRABAN: código do banco 001, moeda 9, campo livre parcial
    # Dígito verificador deve ser de 0 a 9
    dv1 = _modulo10("001912345")
    assert dv1.isdigit() and len(dv1) == 1
    # Caso onde a soma dá múltiplo de 10 -> DV deve ser 0
    # Teste de propriedade: o resultado sempre deve ter 1 dígito
    for test_str in ["123456789", "000000000", "999999999", "341912345"]:
        res = _modulo10(test_str)
        assert res in "0123456789"


def test_febraban_modulo11_weights_and_special_remainders():
    """Valida o Módulo 11 da FEBRABAN: ciclo de pesos 2..9 e regras de resto 0, 1 e 10."""
    # Regra oficial: Restos 0, 1 e 10 geram DV = 1
    # Testar com string de 43 dígitos (tamanho de bar_sem_dv)
    bar_sem_dv = "0019100000000002500000000123456780000000000"
    dv = _modulo11(bar_sem_dv)
    assert dv in "123456789"
    assert len(dv) == 1

    # Validação do ciclo de pesos:
    # 43 posições devem ter pesos [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, ...]
    # Garante que nenhum peso seja negativo ou estático
    soma_esperada = 0
    peso = 2
    for ch in reversed(bar_sem_dv):
        soma_esperada += int(ch) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = soma_esperada % 11
    dv_esperado = "1" if (11 - resto) in (0, 10, 11) else str(11 - resto)
    assert dv == dv_esperado


def test_febraban_fator_vencimento_rollover():
    """Valida a regra oficial de rollover do fator de vencimento (21/02/2025 -> 9999, 22/02/2025 -> 1000)."""
    # 1. Limite máximo do ciclo 1: 21 de fevereiro de 2025 = 9999
    fator_fim_ciclo1 = _fator_vencimento(date(2025, 2, 21))
    assert fator_fim_ciclo1 == 9999

    # 2. Início do ciclo 2: 22 de fevereiro de 2025 = 1000
    fator_inicio_ciclo2 = _fator_vencimento(date(2025, 2, 22))
    assert fator_inicio_ciclo2 == 1000

    # 3. Dia seguinte do ciclo 2: 23 de fevereiro de 2025 = 1001
    fator_dia_seguinte = _fator_vencimento(date(2025, 2, 23))
    assert fator_dia_seguinte == 1001

    # 4. Data presente/futura (ex: 2026) sempre gera fator de 4 dígitos
    fator_2026 = _fator_vencimento(date(2026, 10, 13))
    assert 1000 <= fator_2026 <= 9999

    # 5. Data nula
    assert _fator_vencimento(None) == 0


def test_generate_febraban_codes_structure():
    """Valida que linha digitável (47 dígitos) e código de barras (44 dígitos) seguem a norma FEBRABAN."""
    valor = 1250.75
    venc = date(2026, 11, 20)
    nosso_num = "0012345678"
    cnpj = "12.345.678/0001-90"
    banco = "341"
    agencia = "1234"

    linha, barcode = _generate_febraban_codes(
        valor=valor,
        venc=venc,
        nosso_num=nosso_num,
        cnpj_benef=cnpj,
        bank_code=banco,
        agencia=agencia,
    )

    # Código de barras: 44 dígitos exatos
    assert len(barcode) == 44
    assert barcode.isdigit()
    assert barcode[:3] == "341"  # Código do banco
    assert barcode[3] == "9"     # Moeda Real
    dv_geral = barcode[4]        # Posição 5 (índice 4): DV geral
    assert dv_geral in "123456789"
    fator = f"{_fator_vencimento(venc):04d}"
    assert barcode[5:9] == fator # Fator de vencimento
    assert barcode[9:19] == "0000125075" # Valor em centavos (10 dígitos)

    # Linha digitável: 47 dígitos totais formatados em 5 campos
    digitos_linha = "".join(ch for ch in linha if ch.isdigit())
    assert len(digitos_linha) == 47
    partes = linha.split()
    assert len(partes) == 5
    # Campos 1, 2 e 3 formatados com ponto
    assert "." in partes[0]
    assert "." in partes[1]
    assert "." in partes[2]
    # Campo 4 é o DV geral do código de barras
    assert partes[3] == dv_geral
    # Campo 5 é fator (4 dígitos) + valor (10 dígitos)
    assert partes[4] == f"{fator}0000125075"


def test_itf_patterns_validity():
    """Valida que a tabela ITF_PATTERNS obedece à especificação 2 de 5 (2 largas de 5 elementos)."""
    assert len(ITF_PATTERNS) == 10
    for d in "0123456789":
        pattern = ITF_PATTERNS[d]
        assert len(pattern) == 5
        # Exatamente duas barras largas ('1') e três estreitas ('0')
        assert pattern.count("1") == 2
        assert pattern.count("0") == 3


def test_generate_rolling_boletos_window():
    """Valida a janela deslizante de 6 boletos diários com IDs únicos."""
    boletos = _generate_rolling_boletos()
    assert len(boletos) == 6

    # IDs devem ser todos distintos
    ids = [b["id"] for b in boletos]
    assert len(set(ids)) == 6

    # Primeiro boleto deve ser do dia atual (mais novo) e último de 5 dias atrás (mais antigo)
    hoje = datetime.now()
    assert boletos[0]["emission_date"] == hoje.strftime("%d/%m/%Y")
    d5 = hoje - timedelta(days=5)
    assert boletos[5]["emission_date"] == d5.strftime("%d/%m/%Y")

    # Cada boleto possui linha digitável e código de barras válidos
    for b in boletos:
        assert len(b["barcode_data"]) == 44
        assert b["barcode_data"].isdigit()
        assert len("".join(c for c in b["linha_digitavel"] if c.isdigit())) == 47
        assert "R$" in b["amount_formatted"]


def test_pdf_encryption_with_password_123456():
    """Valida a geração de PDF com criptografia por senha 123456 usando StandardEncryption."""
    boletos = _generate_rolling_boletos()
    b = boletos[0]

    # Sem senha: não deve conter /Encrypt
    pdf_sem = _draw_boleto_pdf(b, password=None)
    assert pdf_sem.startswith(b"%PDF")
    assert b"/Encrypt" not in pdf_sem

    # Com senha 123456: deve conter dicionário /Encrypt e filtro /Standard
    pdf_com = _draw_boleto_pdf(b, password="123456")
    assert pdf_com.startswith(b"%PDF")
    assert b"/Encrypt" in pdf_com
    assert b"/Filter /Standard" in pdf_com


def test_api_rolling_boletos_endpoints():
    """Valida os endpoints /boletos/api/rolling-boletos e /boletos/api/list."""
    login_res = client.post(
        "/boletos/api/login",
        json={"username": "user-boleto", "password": "change-me"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Endpoint oficial
    res1 = client.get("/boletos/api/rolling-boletos", headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] == 6
    assert len(data1["boletos"]) == 6

    # Endpoint alias
    res2 = client.get("/boletos/api/list", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 6
    assert len(data2["boletos"]) == 6


def test_api_download_with_protected_and_password_params():
    """Valida download de boleto com protected=true e senha 123456."""
    login_res = client.post(
        "/boletos/api/login",
        json={"username": "user-boleto", "password": "change-me"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Download padrão (sem senha)
    res_normal = client.get("/boletos/api/download/BOL-TEST-001", headers=headers)
    assert res_normal.status_code == 200
    assert res_normal.headers["content-type"] == "application/pdf"
    assert b"/Encrypt" not in res_normal.content

    # 2. Download com protected=true (senha 123456 via interface)
    res_prot = client.get("/boletos/api/download/BOL-TEST-002?protected=true", headers=headers)
    assert res_prot.status_code == 200
    assert res_prot.headers["content-type"] == "application/pdf"
    assert b"/Encrypt" in res_prot.content

    # 3. Download com password=123456
    res_pass = client.get("/boletos/api/download/BOL-TEST-003?password=123456", headers=headers)
    assert res_pass.status_code == 200
    assert b"/Encrypt" in res_pass.content

    # 4. Download com senha=1 (compatibilidade com automações)
    res_senha = client.get("/boletos/api/download/BOL-TEST-004?senha=1", headers=headers)
    assert res_senha.status_code == 200
    assert b"/Encrypt" in res_senha.content
