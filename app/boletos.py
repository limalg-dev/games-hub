"""
Boletos Test Routes
===================
Sistema de teste para gerar boletos fictícios com login simples.
Gera PDFs no formato real de boletos brasileiros.
"""

from __future__ import annotations

import io
import random
import string
import time
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas

router = APIRouter(prefix="/boletos", tags=["boletos"])
security = HTTPBearer(auto_error=False)

# ── Config ────────────────────────────────────────────────────────────────────
TEST_USER = "user-boleto"
TEST_PASS = "123456secreta"

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


# ── Helpers ───────────────────────────────────────────────────────────────────
def _generate_nosso_numero() -> str:
    """Gera nosso número fictício."""
    return f"{random.randint(10000, 99999)}.{random.randint(100, 999)}"


def _generate_documento() -> str:
    """Gera número de documento fictício."""
    return f"{random.randint(100000, 999999)}-{random.randint(0, 9)}"


def _generate_barcode_data() -> str:
    """Gera dados do código de barras (47 dígitos)."""
    bank_code, _, _ = random.choice(BANKS)
    digits = "".join(random.choices(string.digits, k=47 - len(bank_code)))
    return bank_code + digits


def _generate_cpf_cnpj() -> str:
    """Gera CPF ou CNPJ fictício."""
    if random.random() > 0.5:
        # CPF
        c = [random.randint(0, 9) for _ in range(9)]
        # dígitos verificadores simplificados
        return f"{''.join(str(x) for x in c[:3])}.{''.join(str(x) for x in c[3:6])}.{''.join(str(x) for x in c[6:9])}-{random.randint(10, 99)}"
    else:
        # CNPJ
        c = [random.randint(0, 9) for _ in range(8)]
        return f"{''.join(str(x) for x in c[:2])}.{''.join(str(x) for x in c[2:5])}.{''.join(str(x) for x in c[5:8])}/0001-{random.randint(10, 99)}"


def _random_due_date() -> datetime:
    """Gera data de vencimento aleatória em 2025-2027."""
    year = random.choice([2025, 2026, 2027])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return datetime(year, month, day)


def _get_client_ip(request: Request) -> str:
    """Obtém o IP real do cliente, considerando proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


def _add_log(ip: str, action: str, details: str):
    """Registra uma ação no log."""
    _logs.insert(0, {
        "ip": ip,
        "action": action,
        "details": details,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    })
    # Manter apenas últimos 500 logs
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


# ── PDF Generator ─────────────────────────────────────────────────────────────
def _draw_boleto_pdf(boleto: dict) -> bytes:
    """
    Gera um PDF de boleto bancário no formato real brasileiro.
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    bank_code = boleto["bank_code"]
    bank_name = boleto["bank_name"]
    bank_color = boleto["bank_color"]
    amount = boleto["amount"]
    due_date = boleto["due_date"]
    description = boleto["description"]
    nosso_numero = boleto["nosso_numero"]
    documento = boleto["documento"]
    cnpj_benef = boleto["cnpj_benef"]
    nome_benef = boleto["nome_benef"]
    cpf_pagador = boleto["cpf_pagador"]
    nome_pagador = boleto["nome_pagador"]
    endereco_pagador = boleto["endereco_pagador"]
    instrucoes = boleto["instrucoes"]
    local_pagamento = boleto["local_pagamento"]
    agencia = boleto["agencia"]
    conta = boleto["conta"]

    # Cores
    cor_banco = colors.Color(bank_color[0] / 255, bank_color[1] / 255, bank_color[2] / 255)
    cor_cinza = colors.Color(0.3, 0.3, 0.3)
    cor_claro = colors.Color(0.93, 0.93, 0.93)
    cor_borda = colors.Color(0.6, 0.6, 0.6)

    # ─── RECORTAR (parte superior do boleto) ──────────────────────────────
    top = height - 15 * mm

    # Cabeçalho do banco
    c.setFillColor(cor_banco)
    c.rect(15 * mm, top - 25 * mm, width - 30 * mm, 25 * mm, fill=1, stroke=0)

    # Código do banco
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, top - 18 * mm, f"{bank_code}")

    # Nome do banco
    c.setFont("Helvetica", 11)
    c.drawString(45 * mm, top - 12 * mm, bank_name)

    # Linha digitável (simulada)
    c.setFont("Helvetica", 9)
    linha_digitavel = f"{bank_code}.{random.randint(100, 999)} {random.randint(1000, 9999)}.{random.randint(1000, 9999)} {random.randint(1000, 9999)}.{random.randint(1000, 9999)} {random.randint(1000, 9999)} {random.randint(10000, 99999)}"
    c.drawString(width - 100 * mm, top - 12 * mm, linha_digitavel)

    # Valor do documento
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 20 * mm, top - 18 * mm, f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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
    c.drawString(62 * mm, y_venc - 10 * mm, f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

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

    # ─── CÓDIGO DE BARRAS (simulado visual) ────────────────────────────────
    y_bar = y_ag - 24 * mm
    # Fundo
    c.setFillColor(colors.Color(0.98, 0.98, 0.98))
    c.rect(15 * mm, y_bar - 18 * mm, width - 30 * mm, 18 * mm, fill=1, stroke=1)

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6)
    c.drawString(17 * mm, y_bar - 5 * mm, "CÓDIGO DE BARRAS")

    # Desenhar barras simuladas
    x_start = 20 * mm
    y_barcode = y_bar - 16 * mm
    barcode_data = boleto["barcode_data"]
    seed_val = sum(ord(ch) for ch in barcode_data[:10])
    rng = random.Random(seed_val)

    x = x_start
    total_width = width - 40 * mm
    num_bars = 120
    bar_width_unit = total_width / num_bars

    for i in range(num_bars):
        bar_w = rng.choice([1, 1, 2, 3, 1, 2, 1, 1, 3, 2]) * bar_width_unit * 0.4
        if rng.random() > 0.4:
            c.setFillColor(colors.black)
            c.rect(x, y_barcode, bar_w, 10 * mm, fill=1, stroke=0)
        x += bar_width_unit * 0.8
        if x > width - 20 * mm:
            break

    # Texto do código abaixo das barras
    c.setFont("Courier", 6)
    c.drawString(17 * mm, y_bar - 13 * mm, barcode_data[:20] + "  " + barcode_data[20:])

    # ─── RECIBO DO PAGADOR (parte inferior - recortável) ───────────────────
    y_recibo = y_bar - 24 * mm
    c.setDash(3, 2)
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
    c.drawCentredString(width / 2, 12 * mm, "Documento gerado para fins de teste — Não possui valor legal")

    c.save()
    return buffer.getvalue()


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/api/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request):
    """Autentica o usuário e retorna um token."""
    ip = _get_client_ip(request)

    if req.username != TEST_USER or req.password != TEST_PASS:
        _add_log(ip, "LOGIN_FALHOU", f"Tentativa com usuário: {req.username}")
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token = str(uuid.uuid4())
    _tokens[token] = time.time()
    _add_log(ip, "LOGIN", f"Usuário '{req.username}' autenticado com sucesso")
    return TokenResponse(token=token, message="Login realizado com sucesso")


@router.get("/api/boleto")
async def get_random_boleto(request: Request, _token: str = Depends(_authenticate)):
    """
    Retorna dados de 1 boleto aleatório (para exibição na tela).
    """
    ip = _get_client_ip(request)
    bank_code, bank_name, bank_color = random.choice(BANKS)
    amount = round(random.uniform(15.00, 9999.99), 2)
    due_date = _random_due_date()
    description = random.choice(DESCRIPTIONS)

    boleto = {
        "id": str(uuid.uuid4())[:8],
        "bank_code": bank_code,
        "bank": f"{bank_code} - {bank_name}",
        "bank_name": bank_name,
        "bank_color": bank_color,
        "amount": amount,
        "due_date": due_date,
        "description": description,
        "nosso_numero": _generate_nosso_numero(),
        "documento": _generate_documento(),
        "cnpj_benef": _generate_cpf_cnpj(),
        "nome_benef": f"Imobiliária {bank_name.split()[0]} Ltda",
        "cpf_pagador": _generate_cpf_cnpj(),
        "nome_pagador": f"João da Silva Santos",
        "endereco_pagador": f"Rua das Palmeiras, {random.randint(10, 999)} - Apt {random.randint(10, 999)} - São Paulo/SP - CEP 0{random.randint(100, 999)}-{random.randint(100, 999)}",
        "instrucoes": [
            f"Juros de mora: 2% ao mês",
            f"Multa: 2% após o vencimento",
            f"Descrição: {description}",
            f"Documento: {_generate_documento()}",
        ],
        "local_pagamento": random.choice(PAYMENT_LOCATIONS),
        "agencia": f"{random.randint(1000, 9999)}-{random.randint(0, 9)} / {random.randint(10000, 99999)}-{random.randint(0, 9)}",
        "conta": f"{random.randint(100000, 999999)}-{random.randint(0, 9)}",
        "barcode_data": _generate_barcode_data(),
    }

    _add_log(
        ip,
        "VIEW_BOLETO",
        f"Boleto #{boleto['id']} ({boleto['bank']}, R$ {amount:.2f}) visualizado",
    )

    return boleto


@router.get("/api/download/{boleto_id}")
async def download_boleto(
    boleto_id: str, request: Request, _token: str = Depends(_authenticate)
):
    """
    Gera e baixa o PDF do boleto.
    """
    ip = _get_client_ip(request)

    # Gerar boleto aleatório para este download
    bank_code, bank_name, bank_color = random.choice(BANKS)
    amount = round(random.uniform(15.00, 9999.99), 2)
    due_date = _random_due_date()
    description = random.choice(DESCRIPTIONS)
    documento = _generate_documento()

    boleto = {
        "id": boleto_id,
        "bank_code": bank_code,
        "bank_name": bank_name,
        "bank_color": bank_color,
        "amount": amount,
        "due_date": due_date,
        "description": description,
        "nosso_numero": _generate_nosso_numero(),
        "documento": documento,
        "cnpj_benef": _generate_cpf_cnpj(),
        "nome_benef": f"Imobiliária {bank_name.split()[0]} Ltda",
        "cpf_pagador": _generate_cpf_cnpj(),
        "nome_pagador": f"João da Silva Santos",
        "endereco_pagador": f"Rua das Palmeiras, {random.randint(10, 999)} - Apt {random.randint(10, 999)} - São Paulo/SP - CEP 0{random.randint(100, 999)}-{random.randint(100, 999)}",
        "instrucoes": [
            f"Juros de mora: 2% ao mês",
            f"Multa: 2% após o vencimento",
            f"Descrição: {description}",
            f"Documento: {documento}",
        ],
        "local_pagamento": random.choice(PAYMENT_LOCATIONS),
        "agencia": f"{random.randint(1000, 9999)}-{random.randint(0, 9)} / {random.randint(10000, 99999)}-{random.randint(0, 9)}",
        "conta": f"{random.randint(100000, 999999)}-{random.randint(0, 9)}",
        "barcode_data": _generate_barcode_data(),
    }

    # Gerar PDF
    pdf_bytes = _draw_boleto_pdf(boleto)

    from starlette.responses import Response

    _add_log(
        ip,
        "DOWNLOAD",
        f"Boleto '{boleto_id}' ({boleto['bank_name']}, R$ {amount:.2f}) baixado em PDF",
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="boleto_{boleto_id}.pdf"'
        },
    )


@router.get("/api/logs")
async def get_logs(request: Request, _token: str = Depends(_authenticate)):
    """Retorna os logs de ações."""
    return _logs
