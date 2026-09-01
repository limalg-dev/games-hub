#!/usr/bin/env python3
"""
Gerador do Relatório de Auditoria de Segurança — GameHub Platform
Compila um documento A4 com gráficos, tabelas e issues formatadas para o GitHub.
"""

import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String, Circle
from reportlab.graphics.charts.piecharts import Pie

# ── Paleta de Cores ────────────────────────────────────────────────────────────
C_CRITICA = colors.HexColor("#B91C1C")
C_ALTA    = colors.HexColor("#EA580C")
C_MEDIA   = colors.HexColor("#D97706")
C_BAIXA   = colors.HexColor("#2563EB")
C_FORTE   = colors.HexColor("#059669")

C_PRIMARY = colors.HexColor("#1E293B")
C_SECONDARY = colors.HexColor("#0F172A")
C_ACCENT  = colors.HexColor("#0284C7")
C_BG_LIGHT = colors.HexColor("#F8FAFC")
C_BG_CARD  = colors.HexColor("#F1F5F9")
C_BORDER   = colors.HexColor("#CBD5E1")
C_TEXT_DARK = colors.HexColor("#0F172A")
C_TEXT_MUTED = colors.HexColor("#64748B")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(C_TEXT_MUTED)

        # Cabeçalho
        self.drawString(2 * cm, 28.3 * cm, "Relatório de Auditoria de Segurança — GameHub Platform")
        self.drawRightString(A4[0] - 2 * cm, 28.3 * cm, "Confidencial / Uso Interno")
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(2 * cm, 28.1 * cm, A4[0] - 2 * cm, 28.1 * cm)

        # Rodapé
        self.line(2 * cm, 1.8 * cm, A4[0] - 2 * cm, 1.8 * cm)
        self.drawString(2 * cm, 1.3 * cm, "GameHub Security Review • Setembro 2026")
        self.drawRightString(A4[0] - 2 * cm, 1.3 * cm, f"Página {self._pageNumber} de {page_count}")
        self.restoreState()


def create_donut_chart():
    """Gera o gráfico de rosca de severidade."""
    d = Drawing(220, 140)
    cx, cy, r_out, r_in = 70, 70, 55, 30
    
    pie = Pie()
    pie.x = cx - r_out
    pie.y = cy - r_out
    pie.width = r_out * 2
    pie.height = r_out * 2
    pie.data = [1, 2, 4, 3]
    pie.labels = []
    pie.slices[0].fillColor = C_CRITICA
    pie.slices[1].fillColor = C_ALTA
    pie.slices[2].fillColor = C_MEDIA
    pie.slices[3].fillColor = C_BAIXA
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1.5
    d.add(pie)
    
    donut_hole = Circle(cx, cy, r_in)
    donut_hole.fillColor = colors.white
    donut_hole.strokeColor = colors.white
    d.add(donut_hole)
    
    d.add(String(cx - 8, cy + 4, "10", fontName="Helvetica-Bold", fontSize=14, fillColor=C_TEXT_DARK))
    d.add(String(cx - 18, cy - 8, "ACHADOS", fontName="Helvetica", fontSize=6, fillColor=C_TEXT_MUTED))
    
    legend_items = [
        ("Crítica (1)", C_CRITICA, 105),
        ("Alta (2)", C_ALTA, 85),
        ("Média (4)", C_MEDIA, 65),
        ("Baixa (3)", C_BAIXA, 45),
    ]
    for label, col, y_pos in legend_items:
        d.add(Rect(140, y_pos, 10, 10, fillColor=col, strokeColor=None, rx=2, ry=2))
        d.add(String(155, y_pos + 2, label, fontName="Helvetica-Bold", fontSize=8, fillColor=C_TEXT_DARK))
        
    return d


def create_bar_chart():
    """Gera o gráfico de barras horizontais por categoria."""
    d = Drawing(250, 140)
    categories = [
        ("Inputs (XSS)", 4, C_CRITICA),
        ("Chaves Expostas", 2, C_ALTA),
        ("IDOR", 2, C_MEDIA),
        ("Banco / Isolamento", 1, C_MEDIA),
        ("Permissão Navegador", 1, C_BAIXA),
    ]
    y = 115
    for label, count, col in categories:
        d.add(String(0, y + 2, label, fontName="Helvetica", fontSize=7.5, fillColor=C_TEXT_DARK))
        d.add(Rect(95, y, 130, 10, fillColor=colors.HexColor("#E2E8F0"), strokeColor=None, rx=3, ry=3))
        bar_w = (count / 5.0) * 130
        d.add(Rect(95, y, bar_w, 10, fillColor=col, strokeColor=None, rx=3, ry=3))
        d.add(String(95 + bar_w + 5, y + 2, f"{count}", fontName="Helvetica-Bold", fontSize=7.5, fillColor=C_TEXT_DARK))
        y -= 24
        
    return d


def format_issue_for_pdf(text):
    """Escapa tags XML/HTML preservando quebras de linha formatadas."""
    safe = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return safe.replace('\n', '<br/>')


def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
    )

    styles = getSampleStyleSheet()

    style_cover_title = ParagraphStyle(
        'CoverTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, textColor=C_PRIMARY, spaceAfter=6
    )
    style_cover_sub = ParagraphStyle(
        'CoverSub', fontName='Helvetica', fontSize=11, leading=15, textColor=C_ACCENT, spaceAfter=14
    )
    style_h1 = ParagraphStyle(
        'Header1', fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=C_PRIMARY, spaceBefore=12, spaceAfter=6, keepWithNext=True
    )
    style_h2 = ParagraphStyle(
        'Header2', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=C_SECONDARY, spaceBefore=8, spaceAfter=3, keepWithNext=True
    )
    style_body = ParagraphStyle(
        'BodyDark', fontName='Helvetica', fontSize=8, leading=11.5, textColor=C_TEXT_DARK, spaceAfter=5
    )
    style_issue_code = ParagraphStyle(
        'IssueBlock', fontName='Courier', fontSize=6.8, leading=9, textColor=colors.HexColor("#1E293B"),
        backColor=colors.HexColor("#F8FAFC"), borderColor=colors.HexColor("#CBD5E1"), borderWidth=0.5,
        borderPadding=6, spaceBefore=3, spaceAfter=6
    )

    story = []

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. CAPA
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    
    story.append(Table(
        [[Paragraph("<font color='#0284C7'><b>RELATÓRIO TÉCNICO DE AUDITORIA DE SEGURANÇA DEFENSIVA</b></font>", style_body)]],
        colWidths=[17 * cm],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#E0F2FE")),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ])
    ))
    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph("Relatório de Auditoria de Segurança — GameHub Platform", style_cover_title))
    story.append(Paragraph("Revisão de Código-Fonte, Arquitetura e Modelagem de Ameaças", style_cover_sub))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=10))

    meta_data = [
        [
            Paragraph("<b>Data do Relatório:</b> Setembro de 2026", style_body),
            Paragraph("<b>Versão do Sistema:</b> 0.1.0-prod", style_body)
        ],
        [
            Paragraph("<b>Escopo Auditado:</b> Repositório Completo (app/, games/, static/, deploy)", style_body),
            Paragraph("<b>Classificação:</b> Confidencial / Uso Interno", style_body)
        ],
        [
            Paragraph("<b>Ambiente:</b> FastAPI, WebSockets, SQLite, HTML5 Canvas", style_body),
            Paragraph("<b>Status da Avaliação:</b> 10 Achados Identificados", style_body)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[8.5 * cm, 8.5 * cm])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_BG_CARD),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("Nota Metodológica & Detecção da Stack Tecnológica", style_h2))
    story.append(Paragraph(
        "A auditoria cobriu o código-fonte através de análise estática e mapeamento de fluxo de dados. "
        "Como o <b>GameHub</b> adota uma arquitetura intencional de <i>plataforma casual no-login</i> (sem contas persistentes corporativas), "
        "as categorias clássicas foram adaptadas à realidade técnica do projeto:",
        style_body
    ))

    stack_mapping = [
        [
            Paragraph("<b>1. Banco sem tranca</b>", style_body),
            Paragraph("Mapeado para isolamento de sessões (UUIDs) no SQLite/Memória e integridade do dicionário global compartilhado (Word Bank).", style_body)
        ],
        [
            Paragraph("<b>2. Permissão no navegador</b>", style_body),
            Paragraph("Mapeado para operações privilegiadas (endpoints de boletos, submissão de highscores e validação de jogadas em WebSocket).", style_body)
        ],
        [
            Paragraph("<b>3. IDOR</b>", style_body),
            Paragraph("Verificação exaustiva de todas as rotas que recebem identificadores para manipulação de sessões de jogos (Snake, TD, Hex, Damas).", style_body)
        ],
        [
            Paragraph("<b>4. Chaves expostas</b>", style_body),
            Paragraph("Inspeção de literais de senhas, defaults em variáveis de ambiente, configs Docker e varredura do histórico Git.", style_body)
        ],
        [
            Paragraph("<b>5. Inputs sem tratamento</b>", style_body),
            Paragraph("Varredura de <code>innerHTML</code> no frontend (Vanilla JS) e inserção de dados de usuário (hints, scores, headers HTTP).", style_body)
        ],
    ]
    t_stack = Table(stack_mapping, colWidths=[4.5 * cm, 12.5 * cm])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stack)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. RESUMO EXECUTIVO
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("2. Resumo Executivo", style_h1))
    story.append(Paragraph(
        "A auditoria identificou <b>10 achados de segurança</b> distribuídos entre 1 Crítica, 2 Altas, 4 Médias e 3 Baixas. "
        "A principal superfície de risco reside em <b>injeções Stored XSS via manipulação direta de <code>innerHTML</code></b> "
        "alimentadas por dados não sanitizados (cabeçalho <code>X-Forwarded-For</code> em logs, dicas de palavras cruzadas no banco e nomes em highscores). "
        "Em contrapartida, o projeto apresenta <b>sólida proteção contra SQL Injection</b> e <b>validação rigorosa de regras de jogo no backend</b>.",
        style_body
    ))
    story.append(Spacer(1, 3 * mm))

    chart_table = Table([
        [
            Paragraph("<b>Distribuição por Severidade</b>", style_body),
            Paragraph("<b>Achados por Categoria Técnica</b>", style_body)
        ],
        [
            create_donut_chart(),
            create_bar_chart()
        ]
    ], colWidths=[8.5 * cm, 8.5 * cm])
    chart_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(chart_table)
    story.append(Spacer(1, 5 * mm))

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. PONTOS FORTES E PONTOS FRACOS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("3. Pontos Fortes & Pontos Fracos", style_h1))

    col_fortes = [
        Paragraph("<b>🛡️ PONTOS FORTES (Controles Verificados)</b>", style_body),
        Paragraph("• <b>Zero SQL Injection:</b> 100% das consultas utilizam SQLModel com <code>select(Model).where(...)</code> parameterizado. Zero concatenação de strings SQL.", style_body),
        Paragraph("• <b>Validação de Jogadas no Servidor:</b> O WebSocket em <code>app/websocket.py</code> valida regras de damas e palavras cruzadas no backend, impedindo trapaças por clientes adulterados.", style_body),
        Paragraph("• <b>Entropia de Sessão:</b> IDs de jogos utilizam <code>uuid.uuid4()</code> (128 bits aleatórios), prevenindo adivinhação trivial de salas.", style_body),
        Paragraph("• <b>Autenticação em Módulos Sensíveis:</b> O router <code>boletos.py</code> exige <code>Depends(_authenticate)</code> no servidor para todos os endpoints restritos.", style_body),
    ]

    col_fracos = [
        Paragraph("<b>⚠️ PONTOS FRACOS (Riscos Centrais)</b>", style_body),
        Paragraph("• <b>Stored XSS em Vários Módulos:</b> Uso de <code>innerHTML</code> sem sanitização em <code>boletos.html</code> (logs), <code>crossword</code> (dicas) e tabelas de recordes.", style_body),
        Paragraph("• <b>Poluição Global de Dicionário:</b> <code>POST /api/words</code> permite que usuários anônimos insiram palavras/dicas no SQLite compartilhado.", style_body),
        Paragraph("• <b>Credencial Padrão sem Guard de Startup:</b> <code>BOLETOS_PASS</code> cai em default <code>change-me</code> se não configurado no ambiente.", style_body),
        Paragraph("• <b>IDOR / Negação de Serviço em Snake:</b> Endpoint <code>DELETE /snake/{id}</code> permite apagar partidas ativas sem autenticação de dono.", style_body),
    ]

    t_sw = Table([[col_fortes, col_fracos]], colWidths=[8.3 * cm, 8.7 * cm])
    t_sw.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#FEF2F2")),
        ('BOX', (0, 0), (0, 0), 1, C_FORTE),
        ('BOX', (1, 0), (1, 0), 1, C_CRITICA),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_sw)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. TABELA DETALHADA DE ACHADOS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("4. Tabela de Achados Detalhados por Categoria", style_h1))
    story.append(Paragraph("Todos os achados foram confirmados diretamente no código-fonte do repositório.", style_body))
    story.append(Spacer(1, 2 * mm))

    findings_data = [
        [
            Paragraph("<b>Sev.</b>", style_body),
            Paragraph("<b>Categoria</b>", style_body),
            Paragraph("<b>Arquivo : Linha</b>", style_body),
            Paragraph("<b>Descrição & Impacto</b>", style_body)
        ],
        # 1. Stored XSS Boletos Logs
        [
            Paragraph("<font color='#B91C1C'><b>CRÍTICA</b></font>", style_body),
            Paragraph("Inputs (XSS)", style_body),
            Paragraph("<code>app/boletos.py:168</code><br/><code>static/boletos.html:407</code>", style_body),
            Paragraph("<b>Stored XSS via X-Forwarded-For:</b> O cabeçalho HTTP é salvo em <code>_logs</code> sem filtro e renderizado em <code>innerHTML</code> no painel de logs. Permite roubo de token de sessão.", style_body)
        ],
        # 2. Stored XSS Crossword Hints
        [
            Paragraph("<font color='#EA580C'><b>ALTA</b></font>", style_body),
            Paragraph("Inputs (XSS)", style_body),
            Paragraph("<code>app/main.py:138</code><br/><code>crossword/board.js:117</code>", style_body),
            Paragraph("<b>Stored XSS via Dica de Palavra:</b> <code>POST /api/words</code> insere dicas arbitrárias no SQLite global. Ao gerar palavras cruzadas, a dica é injetada diretamente no <code>innerHTML</code>.", style_body)
        ],
        # 3. Credencial Default em Boletos
        [
            Paragraph("<font color='#EA580C'><b>ALTA</b></font>", style_body),
            Paragraph("Chaves / Segredos", style_body),
            Paragraph("<code>app/boletos.py:30-31</code>", style_body),
            Paragraph("<b>Credencial Padrão Previsível:</b> Fallback <code>BOLETOS_PASS = change-me</code> ativo sem validação de startup em produção, permitindo acesso não autorizado.", style_body)
        ],
        # 4. Poluição Global de Dicionário
        [
            Paragraph("<font color='#D97706'><b>MÉDIA</b></font>", style_body),
            Paragraph("Banco / Isolamento", style_body),
            Paragraph("<code>app/main.py:138-145</code>", style_body),
            Paragraph("<b>Poluição do Banco de Palavras:</b> Endpoint público sem autenticação permite que qualquer cliente insira palavras inadequadas no dicionário global.", style_body)
        ],
        # 5. IDOR Delete Snake Game
        [
            Paragraph("<font color='#D97706'><b>MÉDIA</b></font>", style_body),
            Paragraph("IDOR / DoS", style_body),
            Paragraph("<code>games/snake/routes.py:106</code>", style_body),
            Paragraph("<b>Deleção de Sessão Arbitrária:</b> <code>DELETE /snake/{id}</code> finaliza a partida de qualquer usuário sem validação de posse de sessão.", style_body)
        ],
        # 6. Stored XSS Highscores
        [
            Paragraph("<font color='#D97706'><b>MÉDIA</b></font>", style_body),
            Paragraph("Inputs (XSS)", style_body),
            Paragraph("<code>bomberman/game.js:2050</code><br/><code>tower_defense/index.html:2553</code>", style_body),
            Paragraph("<b>Stored XSS em Recordes:</b> Nomes enviados via API de highscores são inseridos via <code>innerHTML</code> sem sanitização nas tabelas de pontuação.", style_body)
        ],
        # 7. Senha em Histórico Git
        [
            Paragraph("<font color='#D97706'><b>MÉDIA</b></font>", style_body),
            Paragraph("Chaves / Segredos", style_body),
            Paragraph("<code>Git commit 4da1006</code>", style_body),
            Paragraph("<b>Senha no Histórico Git:</b> Credencial legada <code>123456secreta</code> permanece gravada nos commits históricos do repositório.", style_body)
        ],
        # 8. Submissão Arbitrária de Scores
        [
            Paragraph("<font color='#2563EB'><b>BAIXA</b></font>", style_body),
            Paragraph("Permissão / Integridade", style_body),
            Paragraph("<code>bomberman/routes.py:86</code><br/><code>tower_defense/routes.py:141</code>", style_body),
            Paragraph("<b>Falta de Game Proof em Scores:</b> Endpoints aceitam qualquer pontuação sem prova de conclusão válida de partida.", style_body)
        ],
        # 9. Raspagem Pública de Ratings
        [
            Paragraph("<font color='#2563EB'><b>BAIXA</b></font>", style_body),
            Paragraph("IDOR / Enumeração", style_body),
            Paragraph("<code>app/main.py:202-210</code>", style_body),
            Paragraph("<b>Consulta Irrestrita de Rating:</b> <code>GET /api/ratings/{player_id}</code> expõe histórico de qualquer identificador sem restrição.", style_body)
        ],
        # 10. Headers HTTP de Segurança Ausentes
        [
            Paragraph("<font color='#2563EB'><b>BAIXA</b></font>", style_body),
            Paragraph("Inputs (XSS) / Defesa", style_body),
            Paragraph("<code>app/main.py:72-79</code>", style_body),
            Paragraph("<b>Ausência de CSP e Headers de Proteção:</b> Falta de <code>Content-Security-Policy</code>, <code>X-Frame-Options</code> e <code>X-Content-Type-Options</code>.", style_body)
        ],
    ]

    t_findings = Table(findings_data, colWidths=[1.8 * cm, 3.2 * cm, 4.4 * cm, 7.6 * cm])
    t_findings.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_findings)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. RECOMENDAÇÕES PRIORIZADAS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("5. Recomendações Priorizadas (Roadmap de Correção)", style_h1))
    
    recs = [
        ("P1 — Correção Imediata de XSS (innerHTML → textContent)", C_CRITICA,
         "Substituir concatenações diretas de <code>innerHTML</code> por <code>textContent</code> ou criação segura de elementos DOM (<code>document.createElement</code>) em todos os painéis de logs, dicas de palavras cruzadas e murais de recordes."),
        ("P2 — Proteção e Sanitização do Endpoint /api/words", C_ALTA,
         "Exigir chave de API ou desabilitar o endpoint <code>POST /api/words</code> em ambientes públicos, além de sanitizar tags HTML e limitar o comprimento dos campos <code>word</code> e <code>hint</code>."),
        ("P3 — Validação de Startup para Segredos em Produção", C_ALTA,
         "Adicionar checagem no lifespan do FastAPI em <code>app/main.py</code> para lançar erro fatal se <code>BOLETOS_PASS</code> for igual a <code>'change-me'</code> ou <code>'123456secreta'</code> fora de ambiente de desenvolvimento."),
        ("P4 — Adição de Cabeçalhos de Segurança HTTP (CSP, X-Frame-Options)", C_MEDIA,
         "Configurar middleware HTTP adicionando <code>Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'</code>, <code>X-Frame-Options: DENY</code> e <code>X-Content-Type-Options: nosniff</code>."),
        ("P5 — Purga de Segredos do Histórico Git", C_BAIXA,
         "Utilizar ferramenta como <code>git-filter-repo</code> ou BFG Repo-Cleaner para expurgar commits legados contendo senhas literais caso o repositório seja tornado público.")
    ]

    for title, badge_col, desc in recs:
        p_card = [
            Paragraph(f"<b><font color='{badge_col.hexval()}'>{title}</font></b>", style_body),
            Paragraph(desc, style_body)
        ]
        t_card = Table([[p_card]], colWidths=[17 * cm])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 0.5, C_BORDER),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_card)
        story.append(Spacer(1, 2.5 * mm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # 6. ISSUES PRONTAS PARA O GITHUB
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("6. Issues Prontas para o GitHub", style_h1))
    story.append(Paragraph("Copie e cole diretamente os blocos abaixo para criar as issues no GitHub do projeto:", style_body))
    story.append(Spacer(1, 2 * mm))

    raw_issues = [
        # Issue 1
        """--- ISSUE 1 ---
[Segurança] Stored XSS no painel de logs de boletos via cabeçalho X-Forwarded-For

**Labels:** `security`, `severity: critical`, `bug`

### Descrição
O cabeçalho HTTP `X-Forwarded-For` é extraído em `app/boletos.py:168-171` sem sanitização e armazenado na lista de logs da aplicação. Ao acessar a interface de visualização de logs (`static/boletos.html:407-410`), o valor do IP é interpolado diretamente em `innerHTML`, permitindo a execução de JavaScript arbitrário no contexto de um usuário autenticado.

### Evidência
- `app/boletos.py:168`: `forwarded = request.headers.get("X-Forwarded-For")`
- `static/boletos.html:407`: `container.innerHTML = logs.map(l => '<span class="log-ip">${l.ip}</span>...').join('')`

### Impacto
Execução remota de JavaScript no navegador do operador/usuário autenticado, possibilitando roubo de tokens Bearer e ações não autorizadas.

### Sugestão de Correção
1. Validar formato IPv4/IPv6 no backend (`ipaddress.ip_address`).
2. Substituir `innerHTML` em `boletos.html` por manipulação segura com `document.createElement` e `textContent`.

### Critérios de Aceite
- [ ] Payload `<img src=x onerror=alert(1)>` em `X-Forwarded-For` é renderizado como texto puro.
- [ ] O painel de logs não utiliza `innerHTML` com variáveis dinâmicas.
--- FIM ISSUE 1 ---""",

        # Issue 2
        """--- ISSUE 2 ---
[Segurança] Stored XSS e poluição do banco de palavras cruzadas via POST /api/words

**Labels:** `security`, `severity: high`, `bug`

### Descrição
O endpoint `POST /api/words` é público e permite inserção irrestrita de palavras e dicas no banco de dados compartilhado. As dicas (`hint`) são posteriormente renderizadas no frontend de Palavras Cruzadas (`games/crossword/static/board.js:117,131`) diretamente via `innerHTML`, criando um vetor de Stored XSS que afeta outros jogadores.

### Evidência
- `app/main.py:138`: `POST /api/words` não exige autenticação ou moderação.
- `games/crossword/static/board.js:117`: `acrossList.innerHTML = across.map(clue => '<span class="clue-text">${clue.clue}</span>').join('')`

### Impacto
Qualquer visitante pode infectar o dicionário global com payloads XSS persistentes que serão executados por qualquer jogador que abrir uma partida de Palavras Cruzadas.

### Sugestão de Correção
1. Sanitizar tags HTML no backend com `html.escape()` antes de salvar ou escapar no frontend.
2. Trocar `innerHTML` por `textContent` no `board.js`.
3. Proteger `POST /api/words` com autenticação ou desabilitá-lo em produção.

### Critérios de Aceite
- [ ] Dicas contendo tags HTML não disparam execução de scripts.
- [ ] `board.js` utiliza `textContent` para renderizar `clue.clue`.
--- FIM ISSUE 2 ---""",

        # Issue 3
        """--- ISSUE 3 ---
[Segurança] Credencial padrão fraca e falta de validação de inicialização em app/boletos.py

**Labels:** `security`, `severity: high`, `configuration`

### Descrição
A configuração de autenticação em `app/boletos.py:30-31` utiliza o valor padrão `"change-me"` caso a variável de ambiente `BOLETOS_PASS` não seja informada. Em produção, se a variável for omitida, o sistema aceita credenciais padrão conhecidas publicamente.

### Evidência
- `app/boletos.py:30-31`: `TEST_PASS = os.getenv("BOLETOS_PASS", "change-me")`

### Impacto
Acesso não autorizado ao gerador de PDFs e ao painel de logs por invasores usando credenciais default.

### Sugestão de Correção
Adicionar verificação no `lifespan` da aplicação que impede a inicialização em modo de produção se `BOLETOS_PASS` for igual a `"change-me"` ou estiver ausente.

### Critérios de Aceite
- [ ] A aplicação recusa iniciar em produção sem `BOLETOS_PASS` forte e configurado.
--- FIM ISSUE 3 ---""",

        # Issue 4
        """--- ISSUE 4 ---
[Segurança] Stored XSS nos murais de recordes (Bomberman, Tower Defense, Colônia Hex)

**Labels:** `security`, `severity: medium`, `bug`

### Descrição
Os nomes dos jogadores submetidos nas tabelas de recordes (`POST /*/highscores`) são inseridos diretamente no DOM através de `innerHTML` nos clientes web dos jogos Bomberman (`game.js:2050`), Tower Defense (`index.html:2553`) e Colônia Hex (`index.html:830`).

### Evidência
- `games/bomberman/static/game.js:2050`: `listEl.innerHTML = scores.map(s => '<span class="rank">${s.name}</span>...').join('')`
- `games/tower_defense/static/index.html:2553`: `list.innerHTML = scores.map(s => '<span class="hs-name">${s.name}</span>...').join('')`

### Impacto
Execução de scripts XSS nos navegadores de todos os jogadores que visualizam os recordes.

### Sugestão de Correção
Escapar caracteres especiais de HTML (`<`, `>`, `&`, `"`, `'`) nos nomes ao receber no backend e utilizar `textContent` ao criar as linhas de score no frontend.

### Critérios de Aceite
- [ ] Nomes como `<script>` ou `<img src=x onerror=alert(1)>` são renderizados como texto puro.
--- FIM ISSUE 4 ---""",

        # Issue 5
        """--- ISSUE 5 ---
[Segurança] IDOR no gerenciamento de sessões de Snake (DELETE /snake/{id})

**Labels:** `security`, `severity: medium`, `bug`

### Descrição
O endpoint `DELETE /snake/{game_id}` em `games/snake/routes.py:106` permite a qualquer cliente encerrar e deletar a sessão de jogo ativa de outro usuário simplesmente informando o `game_id`, sem qualquer verificação de posse ou token de criador.

### Evidência
- `games/snake/routes.py:106-110`: `active_games.pop(game_id, None)` executado sem validação de dono.

### Impacto
Negação de serviço direcionada (DoS) contra partidas em andamento de outros jogadores.

### Sugestão de Correção
Exigir um token secreto de sessão (`session_token` gerado na criação) no cabeçalho ou body para autorizar a deleção ou controle da partida.

### Critérios de Aceite
- [ ] Apenas o cliente com o token de criação pode encerrar a partida via DELETE.
--- FIM ISSUE 5 ---""",

        # Issue 6
        """--- ISSUE 6 ---
[Segurança] Ausência de cabeçalhos HTTP de segurança (CSP, X-Frame-Options, X-Content-Type-Options)

**Labels:** `security`, `severity: low`, `enhancement`

### Descrição
O middleware HTTP da aplicação em `app/main.py:72-79` não adiciona cabeçalhos defensivos modernos como `Content-Security-Policy`, `X-Frame-Options` e `X-Content-Type-Options`.

### Evidência
- `app/main.py:72`: Apenas cabeçalhos de `Cache-Control` são injetados.

### Impacto
Aumento da superfície para ataques de Clickjacking (incorporação em iframes maliciosos) e menor mitigação em profundidade contra XSS.

### Sugestão de Correção
Adicionar no middleware HTTP:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com;`

### Critérios de Aceite
- [ ] Todas as respostas HTTP incluem os cabeçalhos de segurança recomendados.
--- FIM ISSUE 6 ---"""
    ]

    for raw_issue in raw_issues:
        story.append(Paragraph(format_issue_for_pdf(raw_issue), style_issue_code))
        story.append(Spacer(1, 2 * mm))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF gerado com sucesso em: {filename}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(out_dir, "relatorio-auditoria-seguranca.pdf")
    build_pdf(out_file)
