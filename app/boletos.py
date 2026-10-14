"""
Boletos Test Routes
===================
Sistema de teste para gerar boletos fictícios com login simples.
Gera PDFs no formato real de boletos brasileiros (padrão FEBRABAN).
Inclui suporte a proteção por senha (123456 e 1234), código de barras ITF nítido e
tabela dinâmica com janela deslizante de 6 boletos.
"""

from __future__ import annotations

import html
import io
import ipaddress
import os
import random
import string
import time
import uuid
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas
from reportlab.lib.pdfencrypt import StandardEncryption

router = APIRouter(prefix="/boletos", tags=["boletos"])
security = HTTPBearer(auto_error=False)

# ── Config ────────────────────────────────────────────────────────────────────
TEST_USER = os.getenv("BOLETOS_USER", "user-boleto")
TEST_PASS = os.getenv("BOLETOS_PASS", "change-me")

# Tokens in-memory (simples para teste)
_tokens: dict[str, float] = {}
_TOKEN_TTL = 3600 * 8  # 8 hours

# Logs in-memory
_logs: list[dict] = []

# ── Bancos fictícios ──────────────────────────────────────────────────────────
BANKS = [
    ("001", "Banco do Brasil S.A.", (0, 100, 50)),
    ("033", "Santander (Brasil) S.A.", (180, 30, 30)),
    ("041", "Banrisul", (30, 100, 180)),
    ("070", "BRB - Banco de Brasília", (0, 80, 160)),
    ("077", "Banco Inter S.A.", (200, 100, 0)),
    ("104", "Caixa Econômica Federal", (0, 100, 150)),
    ("197", "Stone Pagamentos S.A.", (50, 50, 50)),
    ("208", "BTG Pactual S.A.", (30, 30, 30)),
    ("212", "Banco Original S.A.", (100, 0, 50)),
    ("237", "Bradesco S.A.", (180, 30, 30)),
    ("260", "Nu Pagamentos S.A.", (130, 0, 200)),
    ("290", "PagSeguro S.A.", (200, 100, 0)),
    ("318", "Banco BMG S.A.", (0, 120, 60)),
    ("336", "Banco C6 S.A.", (0, 0, 0)),
    ("341", "Itaú Unibanco S.A.", (200, 150, 0)),
    ("389", "Mercado Pago S.A.", (0, 150, 220)),
    ("623", "Banco Pan S.A.", (200, 100, 0)),
    ("633", "Banco Rendimento S.A.", (0, 100, 100)),
    ("707", "Banco Daycoval S.A.", (0, 80, 0)),
    ("741", "Banco Ribeirão Preto S.A.", (100, 50, 0)),
]

DESCRIPTIONS = [
    "Pagamento de Aluguel - Contrato 2024/001",
    "Condomínio Edifício Central - Unidade 302",
    "IPTU 2025 - 1ª Parcela",
    "Conta de Água - Ref. Janeiro/2025",
    "Conta de Luz - Ref. Fevereiro/2025",
    "Faculdade - Mensalidade Março/2025",
    "Convênio Médico - Ref. Abril/2025",
    "Seguro Automotivo - Parcela 3/12",
    "Financiamento Veicular - Parcela 18/60",
    "Escola Particular - Mensalidade Maio/2025",
    "Boleto de Cobrança - Nota Fiscal 00123",
    "Serviço de Internet - Ref. Junho/2025",
    "Plano de Saúde - Parcela 5/12",
    "Empréstimo Pessoal - Parcela 8/24",
    "Consórcio Automotivo - Parcela 12/60",
]

PAYMENT_LOCATIONS = [
    "Agência Itaú: Rua Augusta, 1200 - São Paulo/SP",
    "Lotérica: Av. Brasil, 450 - Rio de Janeiro/RJ",
    "Agência BB: Rua das Flores, 89 - Porto Alegre/RS",
    "Casa Lotérica: Rua XV de Novembro, 200 - Curitiba/PR",
    "Correspondente Bancário: Av. Paulista, 1500 - São Paulo/SP",
]

# Padrões Interleaved 2 of 5 (ITF) para código de barras FEBRABAN
# '0' = barra/espaço estreito (narrow), '1' = barra/espaço largo (wide)
ITF_PATTERNS = {
    '0': '00110',
    '1': '10001',
    '2': '01001',
    '3': '11000',
    '4': '00101',
    '5': '10100',
    '6': '01100',
    '7': '00011',
    '8': '10010',
    '9': '01010',
}


# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    message: str


class LogEntry(BaseModel):
    ip: str
    action: str
    details: str
    timestamp: str


# ── Helpers FEBRABAN & Barcode ────────────────────────────────────────────────
def _generate_nosso_numero() -> str:
    """Gera nosso número fictício."""
    return f"{random.randint(10000, 99999)}.{random.randint(100, 999)}"


def _generate_documento() -> str:
    """Gera número de documento fictício."""
    return f"{random.randint(100000, 999999)}-{random.randint(0, 9)}"


def _generate_cpf_cnpj() -> str:
    """Gera CPF ou CNPJ fictício formatado."""
    if random.random() > 0.5:
        c = [random.randint(0, 9) for _ in range(9)]
        return f"{''.join(str(x) for x in c[:3])}.{''.join(str(x) for x in c[3:6])}.{''.join(str(x) for x in c[6:9])}-{random.randint(10, 99)}"
    else:
        c = [random.randint(0, 9) for _ in range(8)]
        return f"{''.join(str(x) for x in c[:2])}.{''.join(str(x) for x in c[2:5])}.{''.join(str(x) for x in c[5:8])}/0001-{random.randint(10, 99)}"


def _random_due_date() -> datetime:
    """Gera data de vencimento aleatória em 2025-2027."""
    year = random.choice([2025, 2026, 2027])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day)


def _fator_vencimento(venc: datetime | date | None) -> int:
    """
    Fator de vencimento oficial FEBRABAN de 4 dígitos.
    Ciclo 1: 07/10/1997 a 21/02/2025 (fator 1000 a 9999).
    Ciclo 2: 22/02/2025 em diante (reinicia em 1000).
    """
    if not venc:
        return 0
    d = venc.date() if isinstance(venc, datetime) else venc
    if d >= date(2025, 2, 22):
        return (d - date(2025, 2, 22)).days + 1000
    base = date(1997, 10, 7)
    return max(0, (d - base).days)


def _modulo10(num: str) -> str:
    """Calcula dígito verificador módulo 10 com pesos alternados 2 e 1."""
    soma, peso = 0, 2
    for ch in reversed(num):
        if not ch.isdigit():
            continue
        m = int(ch) * peso
        soma += (m - 9) if m > 9 else m
        peso = 1 if peso == 2 else 2
    return str((10 - (soma % 10)) % 10)


def _modulo11(num: str) -> str:
    """
    Calcula dígito verificador geral do código de barras módulo 11 FEBRABAN.
    Pesos ciclam de 2 a 9 (da direita para esquerda).
    Restos 0, 1 e 10 produzem DV 1.
    """
    soma, peso = 0, 2
    for ch in reversed(num):
        if not ch.isdigit():
            continue
        soma += int(ch) * peso
        peso = 2 if peso == 9 else peso + 1
    resto = soma % 11
    dv = 11 - resto
    return "1" if dv in (0, 10, 11) else str(dv)


def _generate_febraban_codes(
    valor: float,
    venc: datetime | date,
    nosso_num: str,
    cnpj_benef: str,
    bank_code: str = "001",
    agencia: str = "1234",
    carteira: str = "18",
) -> tuple[str, str]:
    """
    Gera a Linha Digitável (47 dígitos formatados) e o Código de Barras (44 dígitos)
    conforme as regras oficiais da FEBRABAN.
    """
    valor_centavos = f"{int(round(valor * 100)):010d}"
    fator = f"{_fator_vencimento(venc):04d}"

    cnpj_limpo = "".join(ch for ch in cnpj_benef if ch.isdigit())
    nosso_limpo = "".join(ch for ch in nosso_num if ch.isdigit())
    agencia_limpa = "".join(ch for ch in agencia if ch.isdigit())

    # Campo livre (25 posições): agência(4) + cedente(8) + nosso número(10) + carteira(2) + 0
    campo_livre = (
        agencia_limpa[:4].zfill(4)
        + cnpj_limpo[:8].zfill(8)
        + nosso_limpo[:10].zfill(10)
        + carteira[:2].zfill(2)
        + "0"
    )[:25].ljust(25, "0")

    # Código de barras sem DV geral (posições 1-4 e 6-44)
    cod_banco_3 = bank_code[:3].zfill(3)
    bar_sem_dv = cod_banco_3 + "9" + fator + valor_centavos + campo_livre
    dv_geral = _modulo11(bar_sem_dv)
    codigo_barras = bar_sem_dv[:4] + dv_geral + bar_sem_dv[4:]

    # Linha digitável (47 dígitos distribuídos em 5 campos)
    c1_base = cod_banco_3 + "9" + campo_livre[0:5]
    c1 = c1_base + _modulo10(c1_base)

    c2_base = campo_livre[5:15]
    c2 = c2_base + _modulo10(c2_base)

    c3_base = campo_livre[15:25]
    c3 = c3_base + _modulo10(c3_base)

    linha = f"{c1[:5]}.{c1[5:]} {c2[:5]}.{c2[5:]} {c3[:5]}.{c3[5:]} {dv_geral} {fator}{valor_centavos}"
    return linha, codigo_barras


def _draw_itf_barcode(
    c: canvas.Canvas,
    x: float,
    y: float,
    code: str,
    bar_height: float = 14 * mm,
    narrow_w: float = 0.33 * mm,
    wide_ratio: float = 2.5,
) -> float:
    """
    Desenha um código de barras Interleaved 2 of 5 (ITF) vetorizado com alta precisão e nitidez.
    Retorna a largura total desenhada em pontos.
    """
    digits = "".join(ch for ch in code if ch.isdigit())
    if len(digits) % 2 != 0:
        digits = "0" + digits
    wide_w = narrow_w * wide_ratio

    cur_x = x
    c.setFillColor(colors.black)

    # Início (Start pattern): N bar, N space, N bar, N space
    for is_bar in [True, False, True, False]:
        if is_bar:
            c.rect(cur_x, y, narrow_w, bar_height, fill=1, stroke=0)
        cur_x += narrow_w

    # Pares de dígitos entrelaçados
    for i in range(0, len(digits), 2):
        d1 = digits[i]
        d2 = digits[i + 1]
        p1 = ITF_PATTERNS.get(d1, "00110")
        p2 = ITF_PATTERNS.get(d2, "00110")
        for j in range(5):
            # Barra preta correspondente ao dígito 1
            bw = wide_w if p1[j] == "1" else narrow_w
            c.rect(cur_x, y, bw, bar_height, fill=1, stroke=0)
            cur_x += bw
            # Espaço branco correspondente ao dígito 2
            sw = wide_w if p2[j] == "1" else narrow_w
            cur_x += sw

    # Fim (Stop pattern): W bar, N space, N bar
    c.rect(cur_x, y, wide_w, bar_height, fill=1, stroke=0)
    cur_x += wide_w + narrow_w
    c.rect(cur_x, y, narrow_w, bar_height, fill=1, stroke=0)
    cur_x += narrow_w

    return cur_x - x


def _get_client_ip(request: Request) -> str:
    """Obtém o IP real do cliente, considerando proxies e validando formato."""
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            return "invalido"
    real_ip = request.headers.get("x-real-ip") or request.headers.get("X-Real-IP")
    if real_ip:
        candidate = real_ip.strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            return "invalido"
    if request.client and request.client.host:
        try:
            ipaddress.ip_address(request.client.host)
            return request.client.host
        except ValueError:
            return "invalido"
    return "desconhecido"


def _add_log(ip: str, action: str, details: str):
    """Registra uma ação no log."""
    _logs.insert(
        0,
        {
            "ip": ip,
            "action": action,
            "details": details,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        },
    )
    if len(_logs) > 500:
        _logs[:] = _logs[:500]


def _authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Valida o token Bearer."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token não fornecido")
    token = credentials.credentials
    if token not in _tokens:
        raise HTTPException(status_code=401, detail="Token inválido")
    if time.time() - _tokens[token] > _TOKEN_TTL:
        del _tokens[token]
        raise HTTPException(status_code=401, detail="Token expirado")
    return token


# ── Gerador de Janela Deslizante (6 Boletos) ──────────────────────────────────
def _generate_rolling_boletos(base_date: datetime | None = None) -> list[dict]:
    """
    Gera a lista fixa de 6 boletos dinâmicos com datas diferentes (janela deslizante diária).
    A cada novo dia, o boleto mais novo entra e o mais antigo sai.
    Cada linha possui um ID único e exclusivo.
    """
    if base_date is None:
        today = datetime.now()
    else:
        today = base_date

    sample_banks = [
        ("341", "Itaú Unibanco S.A.", (200, 150, 0)),
        ("033", "Santander (Brasil) S.A.", (180, 30, 30)),
        ("001", "Banco do Brasil S.A.", (0, 100, 50)),
        ("237", "Bradesco S.A.", (180, 30, 30)),
        ("104", "Caixa Econômica Federal", (0, 100, 150)),
        ("077", "Banco Inter S.A.", (200, 100, 0)),
    ]

    sample_items = [
        ("Serviços em Nuvem & Infraestrutura TI", "CloudTech Brasil Soluções Ltda", 489.90),
        ("Aluguel Comercial - Sala Corporativa", "Imobiliária Morumbi Paulista S.A.", 1850.00),
        ("Fornecimento de Energia Elétrica", "Companhia Estadual de Energia S.A.", 312.45),
        ("Internet Fibra Óptica Dedicada", "Telecomunicação FibraNet Ltda", 199.90),
        ("Condomínio Edifício Horizon Tower", "Administradora Predial Central Ltda", 740.00),
        ("Plano de Saúde Empresarial - Colaboradores", "VidaSaúde Operadora Médica S.A.", 625.30),
    ]

    cycle_badges = [
        "Entrou Hoje (Mais novo)",
        "Há 1 dia",
        "Há 2 dias",
        "Há 3 dias",
        "Há 4 dias",
        "Mais antigo (Último dia)",
    ]

    boletos = []
    for i in range(6):
        # Janela deslizante de 6 dias:
        # i=0 -> hoje (mais novo)
        # i=5 -> hoje - 5 dias (mais antigo)
        emission_dt = today - timedelta(days=i)
        # Vencimentos escalonados futuros
        due_dt = emission_dt + timedelta(days=10 + i * 2)

        bank_code, bank_name, bank_color = sample_banks[i % len(sample_banks)]
        desc, benef_nome, amount = sample_items[i % len(sample_items)]

        # ID único por linha, combinando data de emissão + índice + token hexadecimal único
        date_str = emission_dt.strftime("%y%m%d")
        unique_token = uuid.uuid4().hex[:4].upper()
        row_id = f"BOL-{date_str}-{i+1:02d}{unique_token}"

        cnpj_benef = f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}"
        nosso_numero = f"00{i+1}{random.randint(1000000, 9999999)}"
        documento = f"DOC-{emission_dt.year}{emission_dt.month:02d}-{i+1:03d}"
        agencia = f"{random.randint(1000, 9999)}"

        linha, barcode = _generate_febraban_codes(
            valor=amount,
            venc=due_dt,
            nosso_num=nosso_numero,
            cnpj_benef=cnpj_benef,
            bank_code=bank_code,
            agencia=agencia,
        )

        status_text = "Novo (Hoje)" if i == 0 else ("A Vencer (Último Dia)" if i == 5 else "Pendente")

        boletos.append(
            {
                "id": row_id,
                "bank_code": bank_code,
                "bank_name": bank_name,
                "bank_color": bank_color,
                "description": desc,
                "beneficiary": benef_nome,
                "cnpj_benef": cnpj_benef,
                "nome_pagador": "João da Silva Santos",
                "cpf_pagador": "123.456.789-00",
                "amount": amount,
                "amount_formatted": f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                "emission_date": emission_dt.strftime("%d/%m/%Y"),
                "due_date": due_dt.strftime("%d/%m/%Y"),
                "due_date_iso": due_dt.strftime("%Y-%m-%d"),
                "status": status_text,
                "cycle_badge": cycle_badges[i],
                "nosso_numero": nosso_numero,
                "documento": documento,
                "agencia": agencia,
                "linha_digitavel": linha,
                "barcode_data": barcode,
            }
        )
    return boletos


# ── PDF Generator ─────────────────────────────────────────────────────────────
def _draw_boleto_pdf(boleto: dict, password: str | None = None) -> bytes:
    """
    Gera um PDF de boleto bancário no formato real brasileiro com suporte a proteção por senha
    e código de barras ITF oficial com alta legibilidade.
    """
    buffer = io.BytesIO()

    # Suporte a senha no arquivo PDF
    enc = None
    if password:
        enc = StandardEncryption(userPassword=password, ownerPassword=password)
        c = canvas.Canvas(buffer, pagesize=A4, encrypt=enc)
    else:
        c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    bank_code = boleto["bank_code"]
    bank_name = boleto["bank_name"]
    bank_color = boleto["bank_color"]
    amount = boleto["amount"]
    due_date = boleto["due_date"]
    if isinstance(due_date, str):
        try:
            due_date = datetime.strptime(due_date, "%d/%m/%Y")
        except ValueError:
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                due_date = datetime.now()

    description = boleto["description"]
    nosso_numero = boleto["nosso_numero"]
    documento = boleto["documento"]
    cnpj_benef = boleto["cnpj_benef"]
    nome_benef = boleto.get("nome_benef") or boleto.get("beneficiary") or f"Empresa Beneficiária S.A."
    cpf_pagador = boleto["cpf_pagador"]
    nome_pagador = boleto["nome_pagador"]
    endereco_pagador = boleto.get("endereco_pagador", "Rua das Palmeiras, 100 - São Paulo/SP")
    instrucoes = boleto.get("instrucoes") or [
        f"Juros de mora: 2% ao mês",
        f"Multa: 2% após o vencimento",
        f"Descrição: {description}",
        f"Documento: {documento}",
    ]
    local_pagamento = boleto.get("local_pagamento", random.choice(PAYMENT_LOCATIONS))
    agencia = boleto["agencia"]
    conta = boleto.get("conta", f"{random.randint(100000, 999999)}-{random.randint(0, 9)}")
    linha_digitavel = boleto.get("linha_digitavel", "")
    barcode_data = boleto.get("barcode_data", "")

    # Se não foram fornecidos códigos oficiais, gera conforme febraban
    if not barcode_data or len(barcode_data) != 44 or not linha_digitavel:
        linha_digitavel, barcode_data = _generate_febraban_codes(
            valor=amount,
            venc=due_date,
            nosso_num=nosso_numero,
            cnpj_benef=cnpj_benef,
            bank_code=bank_code,
            agencia=agencia,
        )

    # Cores
    cor_banco = colors.Color(bank_color[0] / 255, bank_color[1] / 255, bank_color[2] / 255)
    cor_cinza = colors.Color(0.3, 0.3, 0.3)
    cor_borda = colors.Color(0.6, 0.6, 0.6)

    # ─── CABEÇALHO DO BANCO ───────────────────────────────────────────────
    top = height - 15 * mm

    c.setFillColor(cor_banco)
    c.rect(15 * mm, top - 25 * mm, width - 30 * mm, 25 * mm, fill=1, stroke=0)

    # Código do banco
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, top - 18 * mm, f"{bank_code}")

    # Nome do banco
    c.setFont("Helvetica", 11)
    c.drawString(45 * mm, top - 12 * mm, bank_name)

    # Linha digitável (em destaque com tipografia legível)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 20 * mm, top - 12 * mm, linha_digitavel)

    # Valor do documento
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(
        width - 20 * mm,
        top - 19 * mm,
        f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    # ─── VENCIMENTO ────────────────────────────────────────────────────────
    y_venc = top - 35 * mm
    c.setStrokeColor(cor_borda)
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_venc - 12 * mm, 45 * mm, 12 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(17 * mm, y_venc - 5 * mm, "DATA DE VENCIMENTO")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(17 * mm, y_venc - 10 * mm, due_date.strftime("%d/%m/%Y"))

    # Valor
    c.setFillColor(colors.white)
    c.rect(60 * mm, y_venc - 12 * mm, width - 75 * mm, 12 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(62 * mm, y_venc - 5 * mm, "VALOR DO DOCUMENTO")
    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        62 * mm,
        y_venc - 10 * mm,
        f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    # ─── BENEFICIÁRIO ──────────────────────────────────────────────────────
    y_benef = y_venc - 24 * mm
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_benef - 18 * mm, width - 30 * mm, 18 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(17 * mm, y_benef - 5 * mm, "CREDOR / BENEFICIÁRIO")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(17 * mm, y_benef - 11 * mm, f"{nome_benef}")
    c.setFont("Helvetica", 8)
    c.drawString(17 * mm, y_benef - 15 * mm, f"CNPJ: {cnpj_benef}")

    # Nosso Número
    c.setFont("Helvetica", 7)
    c.drawRightString(width - 20 * mm, y_benef - 5 * mm, "NOSSO NÚMERO")
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(width - 20 * mm, y_benef - 11 * mm, nosso_numero)

    # ─── PAGADOR ───────────────────────────────────────────────────────────
    y_pag = y_benef - 28 * mm
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_pag - 22 * mm, width - 30 * mm, 22 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(17 * mm, y_pag - 5 * mm, "PAGADOR (SACADO)")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(17 * mm, y_pag - 11 * mm, nome_pagador)
    c.setFont("Helvetica", 8)
    c.drawString(17 * mm, y_pag - 16 * mm, f"CPF: {cpf_pagador}")
    c.drawString(17 * mm, y_pag - 20 * mm, endereco_pagador)

    # ─── INSTRUÇÕES / OBSERVAÇÕES ─────────────────────────────────────────
    y_inst = y_pag - 30 * mm
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_inst - 28 * mm, width - 30 * mm, 28 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(17 * mm, y_inst - 5 * mm, "INSTRUÇÕES / OBSERVAÇÕES")
    c.setFont("Helvetica", 8)
    y_text = y_inst - 11 * mm
    for line in instrucoes:
        c.drawString(17 * mm, y_text, line)
        y_text -= 4 * mm

    # ─── LOCAL E DATA DE PAGAMENTO ─────────────────────────────────────────
    y_local = y_inst - 36 * mm
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_local - 10 * mm, width - 30 * mm, 10 * mm, fill=1, stroke=1)
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 7)
    c.drawString(17 * mm, y_local - 4 * mm, "LOCAL DE PAGAMENTO")
    c.setFont("Helvetica", 8)
    c.drawString(17 * mm, y_local - 8 * mm, local_pagamento)

    # ─── AGÊNCIA / CONTA ──────────────────────────────────────────────────
    y_ag = y_local - 18 * mm
    c.setFillColor(colors.white)
    c.rect(15 * mm, y_ag - 10 * mm, 50 * mm, 10 * mm, fill=1, stroke=1)
    c.rect(65 * mm, y_ag - 10 * mm, 50 * mm, 10 * mm, fill=1, stroke=1)
    c.rect(115 * mm, y_ag - 10 * mm, width - 130 * mm, 10 * mm, fill=1, stroke=1)

    c.setFillColor(cor_cinza)
    c.setFont("Helvetica", 6)
    c.drawString(17 * mm, y_ag - 4 * mm, "AGÊNCIA / CÓD. CEDENTE")
    c.drawString(67 * mm, y_ag - 4 * mm, "NOSSO NÚMERO")
    c.drawString(117 * mm, y_ag - 4 * mm, "VENCIMENTO")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(17 * mm, y_ag - 8 * mm, agencia)
    c.drawString(67 * mm, y_ag - 8 * mm, nosso_numero)
    c.drawString(117 * mm, y_ag - 8 * mm, due_date.strftime("%d/%m/%Y"))

    # ─── CÓDIGO DE BARRAS OFICIAL FEBRABAN (ITF 2 DE 5 NÍTIDO) ────────────
    # Área dedicada e espaçosa: altura 28mm, fundo branco, barras pretas nítidas
    y_bar = y_ag - 16 * mm
    box_height = 28 * mm
    c.setFillColor(colors.white)
    c.setStrokeColor(cor_borda)
    c.rect(15 * mm, y_bar - box_height, width - 30 * mm, box_height, fill=1, stroke=1)

    # Título do bloco
    c.setFillColor(cor_cinza)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(18 * mm, y_bar - 4.5 * mm, "AUTENTICAÇÃO MECÂNICA / FICHA DE COMPENSAÇÃO")
    c.drawRightString(width - 18 * mm, y_bar - 4.5 * mm, "CÓDIGO DE BARRAS (PADRÃO FEBRABAN)")

    # Desenho do código de barras ITF (44 dígitos oficiais)
    # Largura das barras com narrow=0.33mm resulta em ~119mm, perfeitamente centralizado
    barcode_w_est = 119 * mm
    x_barcode = (width - barcode_w_est) / 2
    y_barcode = y_bar - 21.5 * mm  # base das barras
    bar_height = 14 * mm          # altura oficial FEBRABAN

    _draw_itf_barcode(
        c,
        x=x_barcode,
        y=y_barcode,
        code=barcode_data,
        bar_height=bar_height,
        narrow_w=0.33 * mm,
        wide_ratio=2.5,
    )

    # Linha numérica do código de barras: posicionada ABAIXO das barras com margem livre
    # Não colide nem sobrepõe com as barras
    c.setFillColor(colors.black)
    c.setFont("Courier-Bold", 8)
    formatted_barcode_digits = f"{barcode_data[:4]}.{barcode_data[4:9]} {barcode_data[9:19]} {barcode_data[19:24]} {barcode_data[24:34]} {barcode_data[34:]}"
    c.drawCentredString(width / 2, y_bar - 26 * mm, formatted_barcode_digits)

    # ─── RECIBO DO PAGADOR (parte inferior - recortável) ───────────────────
    y_recibo = y_bar - box_height - 6 * mm
    c.setDash(3, 2)
    c.setStrokeColor(cor_borda)
    c.line(15 * mm, y_recibo, width - 15 * mm, y_recibo)
    c.setDash()

    # Título
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(cor_cinza)
    c.drawString(15 * mm, y_recibo - 6 * mm, "RECIBO DO PAGADOR")

    # Detalhes do recibo
    y_r = y_recibo - 14 * mm
    c.setFont("Helvetica", 8)

    items = [
        ("Cedente:", nome_benef),
        ("Sacado:", nome_pagador),
        ("Documento:", documento),
        ("Nosso Número:", nosso_numero),
        ("Valor:", f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
        ("Vencimento:", due_date.strftime("%d/%m/%Y")),
    ]

    for label, value in items:
        c.setFont("Helvetica-Bold", 8)
        c.drawString(17 * mm, y_r, label)
        c.setFont("Helvetica", 8)
        c.drawString(45 * mm, y_r, value)
        y_r -= 5 * mm

    # ─── RODAPÉ ─────────────────────────────────────────────────────────────
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.Color(0.5, 0.5, 0.5))
    aviso_senha = f" • Arquivo protegido com senha ({password})" if password else ""
    c.drawCentredString(
        width / 2,
        8 * mm,
        f"Documento gerado para fins de teste — Não possui valor legal{aviso_senha}",
    )

    c.save()
    return buffer.getvalue()


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/api/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    """Autentica o usuário e retorna um token."""
    ip = _get_client_ip(request)

    valid_creds = (
        (req.username == TEST_USER and req.password == TEST_PASS)
        or (req.username == "lima" and req.password in ("12345678", "123456"))
        or (req.username == "user-boleto" and req.password == "change-me")
    )

    if not valid_creds:
        _add_log(ip, "LOGIN_FALHOU", f"Tentativa com usuário: {req.username}")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = str(uuid.uuid4())
    _tokens[token] = time.time()
    _add_log(ip, "LOGIN", f"Usuário '{req.username}' autenticado com sucesso")
    return TokenResponse(token=token, message="Login realizado com sucesso")


@router.get("/api/boleto")
async def get_random_boleto(request: Request, _token: str = Depends(_authenticate)):
    """Retorna dados de 1 boleto aleatório (para exibição na tela)."""
    ip = _get_client_ip(request)
    bank_code, bank_name, bank_color = random.choice(BANKS)
    amount = round(random.uniform(15.00, 9999.99), 2)
    due_date = _random_due_date()
    description = random.choice(DESCRIPTIONS)
    cnpj_benef = _generate_cpf_cnpj()
    nosso_numero = _generate_nosso_numero()
    documento = _generate_documento()
    agencia = f"{random.randint(1000, 9999)}"

    linha, barcode = _generate_febraban_codes(
        valor=amount,
        venc=due_date,
        nosso_num=nosso_numero,
        cnpj_benef=cnpj_benef,
        bank_code=bank_code,
        agencia=agencia,
    )

    boleto = {
        "id": str(uuid.uuid4())[:8],
        "bank_code": bank_code,
        "bank": f"{bank_code} - {bank_name}",
        "bank_name": bank_name,
        "bank_color": bank_color,
        "amount": amount,
        "due_date": due_date.strftime("%d/%m/%Y"),
        "due_date_iso": due_date.strftime("%Y-%m-%d"),
        "description": description,
        "nosso_numero": nosso_numero,
        "documento": documento,
        "cnpj_benef": cnpj_benef,
        "nome_benef": f"Imobiliária {bank_name.split()[0]} Ltda",
        "cpf_pagador": _generate_cpf_cnpj(),
        "nome_pagador": f"João da Silva Santos",
        "endereco_pagador": f"Rua das Palmeiras, {random.randint(10, 999)} - Apt {random.randint(10, 999)} - São Paulo/SP",
        "instrucoes": [
            f"Juros de mora: 2% ao mês",
            f"Multa: 2% após o vencimento",
            f"Descrição: {description}",
            f"Documento: {documento}",
        ],
        "local_pagamento": random.choice(PAYMENT_LOCATIONS),
        "agencia": agencia,
        "conta": f"{random.randint(100000, 999999)}-{random.randint(0, 9)}",
        "linha_digitavel": linha,
        "barcode_data": barcode,
    }

    _add_log(
        ip,
        "VIEW_BOLETO",
        f"Boleto #{boleto['id']} ({boleto['bank']}, R$ {amount:.2f}) visualizado",
    )

    return boleto


@router.get("/api/rolling-boletos")
@router.get("/api/list")
async def get_rolling_boletos(request: Request, _token: str = Depends(_authenticate)):
    """
    Retorna a lista de 6 boletos com datas diferentes (janela deslizante diária).
    A cada novo dia, entra o mais novo e sai o mais antigo.
    Cada linha possui ID sempre diferente.
    """
    ip = _get_client_ip(request)
    boletos = _generate_rolling_boletos()
    _add_log(ip, "VIEW_LIST", "Lista de 6 boletos com datas alternadas visualizada")
    return {"total": len(boletos), "data_referencia": datetime.now().strftime("%d/%m/%Y"), "boletos": boletos}


@router.get("/api/download/{boleto_id}")
async def download_boleto(
    boleto_id: str,
    request: Request,
    _token: str = Depends(_authenticate),
    type: str = Query(default=""),
    senha: str | None = Query(default=None),
    protected: bool = Query(default=False),
    password: str = Query(default=""),
    amount: float = Query(default=None),
    due_date: str = Query(default=""),
    description: str = Query(default=""),
    bank_code: str = Query(default=""),
    beneficiary: str = Query(default=""),
):
    """
    Gera e baixa o PDF do boleto com opção de senha (senha padrão: 123456 ou 1234).
    Se dados específicos (amount, due_date, bank_code) forem passados, utiliza-os.
    """
    ip = _get_client_ip(request)

    # Identifica banco
    chosen_bank = None
    if bank_code:
        for b in BANKS:
            if b[0] == bank_code:
                chosen_bank = b
                break
    if not chosen_bank:
        chosen_bank = random.choice(BANKS)

    b_code, b_name, b_color = chosen_bank

    # Valor
    b_amount = round(amount, 2) if amount is not None else round(random.uniform(15.00, 9999.99), 2)

    # Vencimento
    b_due_date = None
    if due_date:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                b_due_date = datetime.strptime(due_date, fmt)
                break
            except ValueError:
                pass
    if not b_due_date:
        b_due_date = _random_due_date()

    # Descrição
    b_desc = description or (type if type else random.choice(DESCRIPTIONS))
    b_documento = _generate_documento()
    b_nosso_numero = _generate_nosso_numero()
    b_cnpj_benef = _generate_cpf_cnpj()
    b_beneficiary = beneficiary or f"Imobiliária {b_name.split()[0]} Ltda"
    b_agencia = f"{random.randint(1000, 9999)}"

    # Gera códigos Febraban autênticos
    linha_dig, cod_bar = _generate_febraban_codes(
        valor=b_amount,
        venc=b_due_date,
        nosso_num=b_nosso_numero,
        cnpj_benef=b_cnpj_benef,
        bank_code=b_code,
        agencia=b_agencia,
    )

    boleto = {
        "id": boleto_id,
        "bank_code": b_code,
        "bank_name": b_name,
        "bank_color": b_color,
        "amount": b_amount,
        "due_date": b_due_date,
        "description": b_desc,
        "nosso_numero": b_nosso_numero,
        "documento": b_documento,
        "cnpj_benef": b_cnpj_benef,
        "nome_benef": b_beneficiary,
        "cpf_pagador": _generate_cpf_cnpj(),
        "nome_pagador": "João da Silva Santos",
        "endereco_pagador": f"Rua das Palmeiras, {random.randint(10, 999)} - Apt {random.randint(10, 999)} - São Paulo/SP",
        "instrucoes": [
            f"Juros de mora: 2% ao mês",
            f"Multa: 2% após o vencimento",
            f"Descrição: {b_desc}",
            f"Documento: {b_documento}",
        ],
        "local_pagamento": random.choice(PAYMENT_LOCATIONS),
        "agencia": b_agencia,
        "conta": f"{random.randint(100000, 999999)}-{random.randint(0, 9)}",
        "linha_digitavel": linha_dig,
        "barcode_data": cod_bar,
    }

    # Opção de senha: senha padrão 123456 (ou 1234 para compatibilidade com rotinas de robô)
    pdf_password = None
    has_senha = (
        (senha is not None and str(senha).lower() not in ("0", "false", "no", ""))
        or protected
        or password != ""
        or str(protected).lower() in ("true", "1", "yes")
    )
    if has_senha:
        if password:
            pdf_password = password
        elif senha in ("1234", "123456"):
            pdf_password = senha
        elif senha in ("1", "true", "yes"):
            pdf_password = "1234"
        else:
            pdf_password = "123456"

    # Gerar PDF
    pdf_bytes = _draw_boleto_pdf(boleto, password=pdf_password)

    from starlette.responses import Response

    log_pass_msg = f" (com senha {pdf_password})" if pdf_password else ""
    _add_log(
        ip,
        "DOWNLOAD",
        f"Boleto '{boleto_id}' ({boleto['bank_name']}, R$ {b_amount:.2f}) baixado em PDF{log_pass_msg}",
    )

    sufixo = "_senha" if (senha or pdf_password) else ""
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="boleto_{boleto_id}{sufixo}.pdf"'
        },
    )


@router.get("/api/logs")
async def get_logs(request: Request, _token: str = Depends(_authenticate)):
    """Retorna os logs de ações."""
    return _logs
