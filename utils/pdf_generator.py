"""
Gerador de PDF — Ordem de Serviço de Manutenção
Usa reportlab com fonte Arial (Windows) para suporte completo a UTF-8/PT-BR.
Fallback para Helvetica em sistemas sem Arial.
"""
import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Registro de Fontes ──────────────────────────────────────────────────────
_WINDOWS_FONTS = "C:/Windows/Fonts/"
_FONT_REGISTERED = False

def _registrar_fontes():
    global _FONT_REGISTERED, FONT, FONT_BOLD
    if _FONT_REGISTERED:
        return
    try:
        pdfmetrics.registerFont(TTFont("OSFont",     _WINDOWS_FONTS + "arial.ttf"))
        pdfmetrics.registerFont(TTFont("OSFont-Bold", _WINDOWS_FONTS + "arialbd.ttf"))
        FONT      = "OSFont"
        FONT_BOLD = "OSFont-Bold"
    except Exception:
        FONT      = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"
    _FONT_REGISTERED = True

FONT      = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


# ── Formatadores ────────────────────────────────────────────────────────────
def _fmt_km(val) -> str:
    try:
        return f"{float(val):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "—"


def _fmt_brl(val) -> str:
    try:
        v = f"R$ {float(val):,.2f}"
        return v.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _safe(text) -> str:
    """Garante que o texto é string não-nulo."""
    return str(text) if text is not None else "—"


# ── Cores ───────────────────────────────────────────────────────────────────
C_PRIMARY  = colors.HexColor("#1D4ED8")
C_LIGHT    = colors.HexColor("#EFF6FF")
C_ROW_ALT  = colors.HexColor("#F8FAFC")
C_BORDER   = colors.HexColor("#CBD5E1")
C_TEXT     = colors.HexColor("#0F172A")
C_MUTED    = colors.HexColor("#64748B")
C_DIVIDER  = colors.HexColor("#E2E8F0")

W = 17.0 * cm  # largura útil (A4 - margens)


# ── Estilos ─────────────────────────────────────────────────────────────────
def _make_styles():
    _registrar_fontes()
    return {
        "title": ParagraphStyle(
            "OSTitle", fontName=FONT_BOLD, fontSize=20,
            alignment=TA_CENTER, textColor=C_PRIMARY, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "OSSubtitle", fontName=FONT, fontSize=10,
            alignment=TA_CENTER, textColor=C_MUTED, spaceAfter=0,
        ),
        "section": ParagraphStyle(
            "OSSection", fontName=FONT_BOLD, fontSize=10,
            textColor=C_PRIMARY, leading=18,
        ),
        "label": ParagraphStyle(
            "OSLabel", fontName=FONT_BOLD, fontSize=8, textColor=C_MUTED,
        ),
        "value": ParagraphStyle(
            "OSValue", fontName=FONT, fontSize=10, textColor=C_TEXT,
        ),
        "footer": ParagraphStyle(
            "OSFooter", fontName=FONT, fontSize=8,
            textColor=C_MUTED, alignment=TA_CENTER,
        ),
    }


def _cell_style(header_rows=1):
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, header_rows - 1), C_ROW_ALT),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])


def _section_table(label_text: str, st_: dict) -> Table:
    t = Table([[Paragraph(label_text, st_["section"])]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Função principal ────────────────────────────────────────────────────────
def gerar_pdf_manutencao(registro: dict) -> bytes:
    """
    Gera um PDF de Ordem de Serviço para um registro de manutenção.

    Args:
        registro: dict com campos do Supabase (veiculos{placa,modelo},
                  tipo, data, km_na_data, custo, proxima_km, descricao)

    Returns:
        bytes do PDF gerado.
    """
    _registrar_fontes()
    st_ = _make_styles()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2 * cm,
    )

    # Extrair campos
    veiculo    = registro.get("veiculos") or {}
    placa      = _safe(veiculo.get("placa", "—"))
    modelo     = _safe(veiculo.get("modelo", "—"))
    tipo       = _safe(registro.get("tipo", "—"))
    data_str   = _safe(registro.get("data", "—"))
    km_data    = _fmt_km(registro.get("km_na_data"))
    prox_km    = _fmt_km(registro.get("proxima_km")) if registro.get("proxima_km") else "—"
    descricao  = _safe(registro.get("descricao") or "—")
    num_os     = str(registro.get("id", "")).zfill(5) if registro.get("id") else "—"
    gerado_em  = datetime.now().strftime("%d/%m/%Y %H:%M")

    story = []

    # ── Cabeçalho ─────────────────────────────────────────────────
    story.append(Paragraph("ORDEM DE SERVIÇO", st_["title"]))
    story.append(Paragraph(
        f"Gestão de Frota — Manutenção de Veículos &nbsp;|&nbsp; OS #{num_os}",
        st_["subtitle"],
    ))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=C_PRIMARY, spaceAfter=20))

    # ── Dados do Veículo ───────────────────────────────────────────
    story.append(_section_table("DADOS DO VEÍCULO", st_))
    story.append(Table(
        [
            [Paragraph("PLACA",     st_["label"]),
             Paragraph("MODELO",    st_["label"]),
             Paragraph("KM NA DATA", st_["label"])],
            [Paragraph(placa,   st_["value"]),
             Paragraph(modelo,  st_["value"]),
             Paragraph(km_data, st_["value"])],
        ],
        colWidths=[4 * cm, 9 * cm, 4 * cm],
        style=_cell_style(),
    ))
    story.append(Spacer(1, 16))

    # ── Dados da Manutenção ────────────────────────────────────────
    story.append(_section_table("DADOS DA MANUTENÇÃO", st_))

    # Serviço
    story.append(Table(
        [
            [Paragraph("SERVIÇO REALIZADO", st_["label"])],
            [Paragraph(tipo, st_["value"])],
        ],
        colWidths=[W],
        style=_cell_style(),
    ))
    story.append(Spacer(1, 4))

    # Data / Próxima KM
    story.append(Table(
        [
            [Paragraph("DATA",       st_["label"]),
             Paragraph("PRÓXIMA KM", st_["label"])],
            [Paragraph(data_str, st_["value"]),
             Paragraph(prox_km,  st_["value"])],
        ],
        colWidths=[8.5 * cm, 8.5 * cm],
        style=_cell_style(),
    ))
    story.append(Spacer(1, 4))

    # Observações (altura mínima para impressão)
    obs_style = _cell_style()
    obs_style.add("MINROWHEIGHT", (0, 1), (-1, 1), 50)
    story.append(Table(
        [
            [Paragraph("OBSERVAÇÕES", st_["label"])],
            [Paragraph(descricao, st_["value"])],
        ],
        colWidths=[W],
        style=obs_style,
    ))

    # ── Assinatura ─────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=16))
    story.append(Table(
        [
            [Paragraph("_" * 40, st_["value"]),
             Paragraph("_" * 22, st_["value"])],
            [Paragraph("Assinatura do Responsável", st_["label"]),
             Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", st_["label"])],
        ],
        colWidths=[12 * cm, 5 * cm],
        style=TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]),
    ))

    # ── Rodapé ─────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_DIVIDER, spaceAfter=6))
    story.append(Paragraph(
        f"Documento gerado em {gerado_em} — Sistema de Gestão de Frota",
        st_["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
