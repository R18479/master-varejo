import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

def gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=1,
        textColor=colors.HexColor("#053c5e"),
        spaceAfter=12,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=1,
        textColor=colors.HexColor("#666666"),
        spaceAfter=20,
    )

    corpo = ParagraphStyle(
        "Corpo",
        parent=styles["Normal"],
        fontSize=11,
        leading=18,
    )

    rodape = ParagraphStyle(
        "Rodape",
        parent=styles["Normal"],
        fontSize=8,
        alignment=1,
        textColor=colors.grey,
    )

    valor_formatado = (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    story = [
        Paragraph("🔺 MASTER VAREJO", titulo),
        Paragraph("LAUDO AUTOMÁTICO DE AUDITORIA", subtitulo),

        Spacer(1, 20),

        Paragraph(f"<b>Loja:</b> {loja}", corpo),
        Paragraph(f"<b>Categoria:</b> {categoria}", corpo),
        Paragraph(f"<b>Dias de Giro:</b> {giro}", corpo),
        Paragraph(f"<b>Capital Imobilizado:</b> {valor_formatado}", corpo),

        Spacer(1, 15),

        Paragraph("<b>Plano de Ação Recomendado</b>", corpo),
        Paragraph(plano_acao, corpo),

        Spacer(1, 30),

        Paragraph(
            "Documento gerado automaticamente pelo AIA.",
            rodape,
        ),
    ]

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
