"""
Boletos Test Routes
===================
Sistema de teste para gerar boletos fictícios com login simples.
"""

from __future__ import annotations

import random
import string
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter(prefix="/boletos", tags=["boletos"])
security = HTTPBearer(auto_error=False)

# ── Config ────────────────────────────────────────────────────────────────────
TEST_USER = "user-boleto"
TEST_PASS = "123456secreta"

# Tokens in-memory (simples para teste)
_tokens: dict[str, float] = {}
_TOKEN_TTL = 3600 * 8  # 8 hours

# Boletos in-memory
_boletos: list[dict] = []

# Logs in-memory
_logs: list[dict] = []

# ── Bancos fictícios ──────────────────────────────────────────────────────────
BANKS = [
    ("001", "Banco do Brasil"),
    ("033", "Santander"),
    ("041", "Banrisul"),
    ("070", "BRB"),
    ("077", "Banco Inter"),
    ("104", "Caixa Econômica"),
    ("197", "Stone"),
    ("208", "BTG Pactual"),
    ("212", "Banco Original"),
    ("237", "Bradesco"),
    ("260", "Nu Pagamentos"),
    ("290", "PagSeguro"),
    ("318", "BMG"),
    ("336", "C6 Bank"),
    ("341", "Itaú Unibanco"),
    ("389", "Mercado Pago"),
    ("623", "Pan"),
    ("633", "Rendimento"),
    ("707", "Daycoval"),
    ("741", "Ribeirão Preto"),
]

DESCRIPTIONS = [
    "Pagamento de teste - Mensalidade",
    "Boleto de teste - Serviço",
    "Teste de integração - Fornecedor",
    "Remessa de teste - Contrato",
    "Lançamento de teste - Frete",
    "Boleto avulso - Consultoria",
    "Teste automatizado - Licença",
    "Pagamento teste - Hosting",
    "Boleto demo - Assinatura",
    "Simulação de cobrança - Aluguel",
    "Teste QA - Courseware",
    "Boleto piloto - Marketing",
    "Emissão teste - Software",
    "Gerado para homologação",
    "Cobrança fictícia - Treinamento",
]


# ── Models ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str
    message: str


class BoletoResponse(BaseModel):
    id: str
    barcode: str
    bank_code: str
    bank: str
    amount: float
    due_date: str
    description: str
    created_at: str


class LogEntry(BaseModel):
    ip: str
    action: str
    details: str
    timestamp: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _generate_barcode() -> str:
    """Gera código de barras fictício no formato boleto bancário."""
    # Formato: 5 blocos (47 dígitos total simulado)
    parts = [
        random.choice(BANKS)[0].ljust(3, "0"),       # banco 3 dig
        "".join(random.choices(string.digits, k=2)),  # moeda 2
        "".join(random.choices(string.digits, k=1)),  # dig verif
        "".join(random.choices(string.digits, k=5)),  # fator vencto 5
        "".join(random.choices(string.digits, k=10)), # valor 10
        "".join(random.choices(string.digits, k=1)),  # dig verif geral
        "".join(random.choices(string.digits, k=4)),  # campo livre 4
        "".join(random.choices(string.digits, k=10)), # campo livre 10
    ]
    return " ".join(parts)


def _random_due_date() -> str:
    """Gera data de vencimento aleatória em 2025-2027."""
    year = random.choice([2025, 2026, 2027])
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{day:02d}/{month:02d}/{year}"


def _create_boleto() -> dict:
    """Cria um boleto fictício."""
    bank_code, bank_name = random.choice(BANKS)
    amount = round(random.uniform(15.00, 9999.99), 2)
    b_id = str(uuid.uuid4())[:8]
    return {
        "id": b_id,
        "barcode": _generate_barcode(),
        "bank_code": bank_code,
        "bank": f"{bank_code} - {bank_name}",
        "amount": amount,
        "due_date": _random_due_date(),
        "description": random.choice(DESCRIPTIONS),
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


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


@router.get("/api/boletos")
async def list_boletos(request: Request, _token: str = Depends(_authenticate)):
    """Lista os boletos gerados na sessão atual."""
    return _boletos


@router.post("/api/generate", response_model=list[BoletoResponse])
async def generate_boletos(request: Request, _token: str = Depends(_authenticate)):
    """Gera um lote de boletos fictícios (5-15 boletos)."""
    ip = _get_client_ip(request)
    count = random.randint(5, 15)
    batch = [_create_boleto() for _ in range(count)]
    _boletos.clear()
    _boletos.extend(batch)
    _add_log(ip, "GERAR_BOLETOS", f"{count} boletos gerados")
    return batch


@router.get("/api/download/{boleto_id}")
async def download_boleto(
    boleto_id: str, request: Request, _token: str = Depends(_authenticate)
):
    """Simula o download de um boleto (retorna arquivo TXT fictício)."""
    ip = _get_client_ip(request)

    boleto = next((b for b in _boletos if b["id"] == boleto_id), None)
    if not boleto:
        raise HTTPException(status_code=404, detail="Boleto não encontrado")

    from starlette.responses import PlainTextResponse

    content = f"""
╔══════════════════════════════════════════════════════════════╗
║                    BOLETO DE PAGAMENTO                       ║
║                      (ARQUIVO DE TESTE)                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Banco:          {boleto['bank']:<43}║
║  Código Barras:  {boleto['barcode']:<43}║
║  Valor:          R$ {boleto['amount']:,.2f}{'':<39}║
║  Vencimento:     {boleto['due_date']:<43}║
║  Descrição:      {boleto['description']:<43}║
║  ID:             {boleto['id']:<43}║
║  Gerado em:      {boleto['created_at']:<43}║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  DOCUMENTO GERADO PARA TESTES - NÃO TEM VALIDADE         ║
╚══════════════════════════════════════════════════════════════╝

Código de Barras (linha digitável):
{boleto['barcode']}

Banco: {boleto['bank']}
Valor: R$ {boleto['amount']:,.2f}
Vencimento: {boleto['due_date']}
Descrição: {boleto['description']}
"""
    _add_log(
        ip,
        "DOWNLOAD",
        f"Boleto '{boleto['id']}' ({boleto['bank']}, R$ {boleto['amount']:.2f}) baixado",
    )

    return PlainTextResponse(
        content=content.strip(),
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="boleto_{boleto_id}.txt"'
        },
    )


@router.get("/api/logs")
async def get_logs(request: Request, _token: str = Depends(_authenticate)):
    """Retorna os logs de ações."""
    return _logs
