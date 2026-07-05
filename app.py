import io
import re
import pandas as pd
import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# Configuração da página
st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    page_icon="🔼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Função para carregar a logo
def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except:
        return None

logo_img = carregar_logo()

# CSS Customizado
st.markdown("""
<style>
.header {
    position: fixed;
    top: 0; left: 0; width: 100%;
    background-color: #111111;
    color: white;
    padding: 10px 15px;
    display: flex; align-items: center; gap: 15px;
    z-index: 1200;
    box-shadow: 0 2px 8px #0009;
}
.header-texts {
    display: flex; flex-direction: column;
}
.header-title {
    font-weight: 700; font-size: 22px; margin: 0;
    letter-spacing: 2px; user-select: none;
}
.header-subtitle {
    font-weight: 400; font-size: 10px;
    color: #888888; text-transform: uppercase;
    letter-spacing: 4px; user-select: none;
}
.main-content {
    margin-top: 70px;
    padding: 10px 15px 70px 15px;
}
.category-card {
    background: #f0f8ff;
    border-radius: 14px;
    padding: 15px 20px;
    margin-top: 12px;
    box-shadow: 0 1px 8px #aaa8;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# Cabeçalho fixo com logo e texto
with st.container():
    st.markdown('<div class="header">', unsafe_allow_html=True)
    if logo_img:
        st.image(logo_img, width=48)
    st.markdown('''
        <div class="header-texts">
            <h1 class="header-title">🔼 MASTER VAREJO</h1>
            <div class="header-subtitle">POWERED BY AIA</div>
        </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Entrada de dados pelo usuário
loja = st.text_input("Loja")
categoria = st.text_input("Categoria")
giro = st.number_input("Dias de Giro", min_value=0, step=1)
valor = st.number_input("Capital Imobilizado (R$)", min_value=0.0, format="%.2f")
plano_acao = st.text_area("Plano de Ação Recomendado", height=150)

# Função para gerar PDF com ReportLab
def gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)

    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], fontName="Helvetica-Bold",
                            fontSize=20, alignment=1, textColor=colors.HexColor("#053c5e"), spaceAfter=12)
    subtitulo = ParagraphStyle("Subtitulo", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=11, alignment=1, textColor=colors.HexColor("#666666"), spaceAfter=20)
    corpo = ParagraphStyle("Corpo", parent=styles["Normal"], fontSize=11, leading=18)
    rodape = ParagraphStyle("Rodape", parent=styles["Normal"], fontSize=8, alignment=1,
                           textColor=colors.grey)

    try:
        valor_formatado = f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        valor_formatado = f"R$ {valor}"

    plano_acao_texto = plano_acao or ""

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
        Paragraph(plano_acao_texto.replace('\n', '<br />'), corpo),
        Spacer(1, 30),
        Paragraph("Documento gerado automaticamente pelo AIA.", rodape),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Botão para gerar e baixar PDF
if st.button("Gerar PDF", type="primary"):
    if loja.strip() and categoria.strip() and giro > 0 and valor > 0:
        pdf_bytes = gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao)
        st.download_button(
            label="📄 Baixar Laudo PDF",
            data=pdf_bytes,
            file_name=f"laudo_{loja.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
        st.success("Laudo gerado com sucesso!")
    else:
        st.error("Preencha todos os campos obrigatórios corretamente.")

st.markdown('</div>', unsafe_allow_html=True)
