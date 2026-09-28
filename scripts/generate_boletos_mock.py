#!/usr/bin/env python3
"""Gera mocks de boletos (dados 100% ficticios) para a tela de boletos.

Baseado no modelo do boleto Santander JOHNSON (apenas como REFERENCIA DE LAYOUT),
mas com banco ficticio, valores novos e 10 CNPJs mockados.

Uso: python3 scripts/generate_boletos_mock.py
Saida: static/mocks/boletos.json
"""
import json
import os
from datetime import date

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "static", "mocks", "boletos.json")

# Banco FICTICIO (o usuario pediu para trocar o banco do exemplo)
BANCO = {"codigo": "748", "nome": "Banco Ficticio S.A.", "digito": "X", "agencia": "0134", "carteira": "18", "moeda": "9", "especie": "R$"}


def cnpj_dv(base12: str) -> str:
    """Calcula os 2 digitos verificadores de um CNPJ (12 primeiros digitos)."""
    def calc(nums, pesos):
        s = sum(int(n) * p for n, p in zip(nums, pesos))
        r = 11 - (s % 11)
        return "0" if r > 9 else str(r)

    d1 = calc(base12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc(base12 + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return d1 + d2


def make_cnpj(base12: str) -> str:
    """Forma XX.XXX.XXX/XXXX-DD a partir de 12 digitos + DV calculado."""
    dv = cnpj_dv(base12)
    d = base12 + dv
    return f"{d[0:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:14]}"


def fator_vencimento(d: date) -> int:
    """Fator de vencimento da linha digitavel (base 03/07/2000, reinicia em 2025)."""
    base = date(2000, 7, 3)
    f = (d - base).days
    return f if f <= 9999 else f - 9000  # ciclo reinicia em 22/02/2025


def linha_digitavel(valor: float, venc: date, nosso_num: str, cnpj_num: str):
    """Monta linha digitavel (47 digitos) e codigo de barras (44 digitos) — layout FEBRABAN."""
    valor_centavos = f"{int(round(valor * 100)):010d}"
    fator = str(fator_vencimento(venc))

    def modulo10(num: str) -> str:
        soma, peso = 0, 2
        for ch in reversed(num):
            m = int(ch) * peso
            soma += (m - 9) if m > 9 else m
            peso = 1 if peso == 2 else 2
        return str((10 - (soma % 10)) % 10)

    def modulo11(num: str) -> str:
        soma, peso = 0, 2
        for ch in reversed(num):
            soma += int(ch) * peso
            peso = 9 if peso == 9 else peso - 1
        dv = 11 - (soma % 11)
        return "1" if dv > 9 else str(dv)

    # Campo livre (25 posicoes, pos 20-44): agencia(4) + cedente(8) + nosso numero(10) + carteira(2) + 1
    campo_livre = f"{BANCO['agencia']}{cnpj_num[:8]}{nosso_num}{BANCO['carteira']}0"[:25].ljust(25, "0")

    # Codigo de barras (44 digitos: banco+moeda+fator+valor+campolivre, DV geral na pos 5)
    bar_sem_dv = BANCO["codigo"] + BANCO["moeda"] + fator + valor_centavos + campo_livre
    dv_geral = modulo11(bar_sem_dv)
    codigo_barras = bar_sem_dv[:4] + dv_geral + bar_sem_dv[4:]

    # Linha digitavel: campo1(10) + campo2(11) + campo3(11) + DV(1) + fator(4) + valor(10) = 47
    c1_base = BANCO["codigo"] + BANCO["moeda"] + campo_livre[0:5]
    c1 = c1_base + modulo10(c1_base)
    c2_base = campo_livre[5:15]
    c2 = c2_base + modulo10(c2_base)
    c3_base = campo_livre[15:25]
    c3 = c3_base + modulo10(c3_base)
    linha = f"{c1[:5]}.{c1[5:]} {c2[:5]}.{c2[5:]} {c3[:5]}.{c3[5:]} {dv_geral} {fator}{valor_centavos}"
    return linha, codigo_barras


# ── 10 clientes mockados (3 obrigatorios + 7 ficticios) ──────────────────────
CLIENTES = [
    # (nome_fantasia, endereco, cnpj_base12 OU cnpj pronto, empresa_razao, email, telefone)
    # 3 OBRIGATORIOS (CNPJs exatamente como pedidos — apenas formatados)
    ("Loja Centro", "Av. Paulista, 1000 - Sao Paulo/SP", "42.108.400/0001-65", "Empresa Alpha Comercio de Artigos Oticos LTDA", "contato@alpha.com.br", "+55 (11) 3021-4567"),
    ("Loja Shopping", "Rua Q F, 12 - Setor Bueno, Goiania/GO", "12.333.222/0001-00", "Empresa Beta Comercio LTDA", "liam@tes.com", "+55 (11) 95477-3016"),
    ("Loja Mage", "Rua B, 340 - Jardins, Sao Paulo/SP", "32.108.400/0001-89", "Mage Otica e Commodities LTDA", "financeiro@mage.com.br", "+55 (21) 98123-4400"),
    # 7 ADICIONAIS (CNPJs ficticios com DV valido calculado)
    ("Filial Norte", "Av. Amazonas, 2500 - Belo Horizonte/MG", make_cnpj("278491350001"), "Delta Distribuicao LTDA", "pgto@delta.com.br", "+55 (31) 3344-8890"),
    ("Loja Leste", "Rua do commerce, 89 - Recife/PE", make_cnpj("319924560001"), "Epsilon Varejo LTDA", "epsilon@epsilon.com.br", "+55 (81) 3055-2231"),
    ("Filial Sul", "Av. Ipiranga, 6681 - Porto Alegre/RS", make_cnpj("501287340001"), "Zeta Comercio de Oticas LTDA", "financeiro@zeta.com.br", "+55 (51) 3021-9087"),
    ("Loja Oeste", "Rua Marechal Deodoro, 450 - Campo Grande/MS", make_cnpj("637459180001"), "Eta Comercio LTDA", "eta@eta.com.br", "+55 (67) 3321-7789"),
    ("Loja Sudeste", "Av. Rio Branco, 156 - Rio de Janeiro/RJ", make_cnpj("771204830001"), "Teta Importadora LTDA", "teta@teta.com.br", "+55 (21) 2222-3141"),
    ("Filial Centro-Oeste", "Av. Beira Rio, 1200 - Cuiaba/MT", make_cnpj("847390510001"), "Iota Comercial LTDA", "iota@iota.com.br", "+55 (65) 3667-1204"),
    ("Loja Nordeste", "Av. Oceânica, 2200 - Salvador/BA", make_cnpj("912348760001"), "Kappa Servicos Oticos LTDA", "kappa@kappa.com.br", "+55 (71) 3245-6690"),
]

# Valores novos (o usuario pediu para alterar os valores do exemplo)
VALORES = [187.50, 342.00, 60.22, 529.90, 118.75, 743.40, 256.30, 98.99, 465.00, 331.85]
DIA_VENC = [10, 12, 15, 18, 20, 22, 25, 27, 28, 30]


def format_cnpj(c: str) -> str:
    if "." in c:
        return c
    return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"


def main():
    boletos = []
    for i, (fantasia, endereco, cnpj, razao, email, fone) in enumerate(CLIENTES):
        valor = VALORES[i]
        venc = date(2026, 10, DIA_VENC[i])
        cnpj_fmt = format_cnpj(cnpj)
        cnpj_num = cnpj_fmt.replace(".", "").replace("/", "").replace("-", "")
        nosso = f"{i + 1:03d}{cnpj_num[-5:]}{DIA_VENC[i]:02d}"  # 10 digitos
        linha, barras = linha_digitavel(valor, venc, nosso, cnpj_num[:8])
        boletos.append({
            "id": i + 1,
            "banco": BANCO["nome"],
            "banco_codigo": BANCO["codigo"],
            "agencia": BANCO["agencia"],
            "carteira": BANCO["carteira"],
            "beneficiario": "IMPORTADORA FICTICIA DISTRIBUIDORA LTDA",
            "beneficiario_cnpj": "10.562.739/0001-08",
            "pagador": {
                "loja": fantasia,
                "razao_social": razao,
                "cnpj": cnpj_fmt,
                "endereco": endereco,
                "email": email,
                "telefone": fone,
            },
            "nosso_numero": nosso,
            "documento": f"FAT-{2026}{DIA_VENC[i]:02d}{i + 1:03d}",
            "valor": valor,
            "valor_formatado": f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "vencimento": venc.isoformat(),
            "vencimento_formatado": venc.strftime("%d/%m/%Y"),
            "linha_digitavel": linha,
            "codigo_barras": barras,
            "status": "pendente",
        })

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump({"gerado_em": date.today().isoformat(), "banco_padrao": BANCO, "total": len(boletos), "boletos": boletos}, f, ensure_ascii=False, indent=2)
    print(f"OK: {len(boletos)} boletos em {os.path.relpath(OUTPUT)}")
    for b in boletos:
        print(f"  #{b['id']:02d} {b['pagador']['cnpj']}  {b['pagador']['loja']:<22} {b['valor_formatado']:>10}  venc {b['vencimento_formatado']}")


if __name__ == "__main__":
    main()
