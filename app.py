import io
import re
import pandas as pd
import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    page_icon="🔼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except:
        return None

logo_img = carregar_logo()

LOJAS = ["SOCORRO", "SÃO JOSÉ", "EMBU", "ELIANA", "JOÃO DIAS", "ARICANDUVA", "ALVARENGA", "SABARÁ"]

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

uploaded_file = st.file_uploader("Faça upload do arquivo de texto do dashboard (.txt)", type=["txt"])

dados_dashboard = ""
if uploaded_file:
    dados_dashboard = uploaded_file.read().decode('utf-8')

def parse_dashboard(texto: str):
    dados = []
    regex = re.compile(
        r"(?P<categoria>[A-Za-zÀ-ú\s]+?)\s+com\s+(?P<dias>\d+)\s+dias\s+em\s+(?P<loja>[A-Za-zÀ-ú\s]+)\s*\(R\$?\s*(?P<valor>[\d\.\,]+)\)",
        re.IGNORECASE
    )
    for linha in texto.strip().split("\n"):
        m = regex.search(linha.strip())
        if m:
            categoria = m.group("categoria").strip().upper()
            loja = m.group("loja").strip().upper()
            dias = int(m.group("dias"))
            valor_str = m.group("valor").replace(".", "").replace(",", ".")
            valor = float(valor_str)
            dados.append({
                "Loja": loja,
                "Categoria": categoria,
                "DiasGiro": dias,
                "ValorFinanceiro": valor
            })
    df = pd.DataFrame(dados)
    return df if not df.empty else None

df = None
if dados_dashboard.strip():
    with st.spinner("Processando dados do dashboard..."):
        df = parse_dashboard(dados_dashboard)

if df is None:
    st.warning("Por favor, faça upload de um arquivo válido com os dados do dashboard.")
    st.stop()

lojas_presentes = df["Loja"].unique()
if set(LOJAS).issubset(set(lojas_presentes)):
    st.markdown("## Comparativo entre as 8 Lojas Monitoradas")
    resumo = df.groupby("Loja").agg({"DiasGiro": "mean", "ValorFinanceiro": "sum"}).reset_index()
    resumo = resumo.rename(columns={
        "DiasGiro": "Média Dias de Giro",
        "ValorFinanceiro": "Total Capital Imobilizado (R$)"
    })
    resumo["Média Dias de Giro"] = resumo["Média Dias de Giro"].round(1)
    resumo["Total Capital Imobilizado (R$)"] = resumo["Total Capital Imobilizado (R$)"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    st.dataframe(resumo.style.set_properties(**{'text-align': 'center'}))
else:
    st.info("Os dados de todas as 8 lojas monitoradas ainda não foram completamente enviados para comparação.")

loja_escolhida = st.selectbox("Selecione a Loja para visualizar dados detalhados", sorted(lojas_presentes))

def gerar_laudo_pdf(loja, df_loja):
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

    story = [Paragraph("🔺 MASTER VAREJO", titulo),
             Paragraph(f"Laudo detalhado para a loja {loja.title()}", subtitulo),
             Spacer(1, 20)]

    for _, row in df_loja.iterrows():
        valor_fmt = f"R$ {row['ValorFinanceiro']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        texto = f"<b>Categoria:</b> {row['Categoria'].title()}<br/><b>Dias de Giro:</b> {row['DiasGiro']} dias<br/><b>Valor Financeiro:</b> {valor_fmt}"
        story.append(Paragraph(texto, corpo))
        story.append(Spacer(1, 12))

    story.append(Spacer(1, 30))
    story.append(Paragraph("Documento gerado automaticamente pelo AIA.", rodape))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

if loja_escolhida:
    df_loja = df[df["Loja"] == loja_escolhida]
    st.markdown(f"### Dados detalhados para a loja **{loja_escolhida.title()}**")
    for _, row in df_loja.iterrows():
        valor_fmt = f"R$ {row['ValorFinanceiro']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"""
        <div class="category-card">
            <strong>Categoria:</strong> {row['Categoria'].title()}<br>
            <strong>Dias de Giro:</strong> {row['DiasGiro']} dias<br>
            <strong>Valor Financeiro:</strong> {valor_fmt}
        </div>
        """, unsafe_allow_html=True)

    pdf_bytes = gerar_laudo_pdf(loja_escolhida, df_loja)

    st.download_button(
        label="📄 Baixar Laudo Detalhado em PDF",
        data=pdf_bytes,
        file_name=f"laudo_{loja_escolhida.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

st.markdown("</div>", unsafe_allow_html=True)
