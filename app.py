import io
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, alignment=1, textColor=colors.HexColor("#053c5e"), spaceAfter=12)
    subtitulo = ParagraphStyle("Subtitulo", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, alignment=1, textColor=colors.HexColor("#666666"), spaceAfter=20)
    corpo = ParagraphStyle("Corpo", parent=styles["Normal"], fontSize=11, leading=18)
    rodape = ParagraphStyle("Rodape", parent=styles["Normal"], fontSize=8, alignment=1, textColor=colors.grey)

    # Corrige formatação de valor e quebras de linha
    try:
        valor_formatado = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        valor_formatado = f"R$ {valor}"
    
    plano_acao_html = (plano_acao or "").replace("\n", "<br/>")

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
        Paragraph(plano_acao_html, corpo),
        Spacer(1, 30),
        Paragraph("Documento gerado automaticamente pelo AIA.", rodape),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Interface Streamlit
st.set_page_config(page_title="Master Varejo - Laudo", page_icon="🔺")
st.title("🔺 MASTER VAREJO")
st.subheader("Gerador de Laudo Automático de Auditoria")

loja = st.text_input("Loja")
categoria = st.text_input("Categoria") 
giro = st.text_input("Dias de Giro")
valor = st.number_input("Capital Imobilizado (R$)", min_value=0.0, format="%.2f")
plano_acao = st.text_area("Plano de Ação Recomendado", height=150)

if st.button("Gerar PDF", type="primary"):
    if loja and categoria and giro and valor:
        pdf_bytes = gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao)
        st.download_button(
            label="📄 Baixar Laudo PDF",
            data=pdf_bytes,
            file_name=f"laudo_{loja.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.success("Laudo gerado com sucesso!")
    else:
        st.error("Preencha todos os campos obrigatórios
