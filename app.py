import io
import re
import pandas as pd
import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import pdfplumber

st.set_page_config(page_title="Master Varejo — Powered by AIA", page_icon="🔼", layout="centered")

def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except:
        return None

logo_img = carregar_logo()

st.markdown("""
<style>
.header {
    position: fixed; top:0; left:0; width:100%; background-color:#111111; color: white;
    padding: 10px 15px; display: flex; align-items: center; gap: 15px; z-index: 1200;
    box-shadow: 0 2px 8px #0009;
}
.header-texts {
    display: flex; flex-direction: column;
}
.header-title {
    font-weight: 700; font-size: 22px; margin: 0; letter-spacing: 2px; user-select: none;
}
.header-subtitle {
    font-weight: 400; font-size: 10px; color: #888888;
    text-transform: uppercase; letter-spacing: 4px; user-select: none;
}
.main-content {
    margin-top: 70px; padding: 10px 15px 70px 15px;
}
.category-card {
    background: #f0f8ff; border-radius: 14px; padding: 15px 20px;
    margin-top: 12px; box-shadow: 0 1px 8px #aaa8;
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

def extrair_texto_pdf(uploaded_pdf):
    texto = ""
    try:
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + "\n"
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
    return texto

def ler_arquivo(upload):
    if not upload:
        return ""
    nome = upload.name.lower()
    if nome.endswith(".txt"):
        return upload.read().decode("utf-8")
    elif nome.endswith(".pdf"):
        return extrair_texto_pdf(upload)
    elif nome.endswith(".xls") or nome.endswith(".xlsx"):
        try:
            df_xls = pd.read_excel(upload)
            texto = ""
            for _, row in df_xls.iterrows():
                # Ajuste "Categoria", "Dias", "Loja", "Valor" conforme colunas do seu Excel
                texto += f"{row['Categoria']} com {int(row['Dias'])} dias em {row['Loja']} (R$ {row['Valor']})\n"
            return texto
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
            return ""
    else:
        return ""

uploaded_file = st.file_uploader("Faça upload do arquivo do dashboard (.txt, .pdf, .xls, .xlsx)", type=["txt", "pdf", "xls", "xlsx"])

dados_dashboard = ler_arquivo(uploaded_file)

if dados_dashboard.strip():
    st.success("Arquivo carregado com sucesso e processado.")
else:
    st.info("Aguardando upload do arquivo...")

def parse_dashboard(texto):
    dados = []
    regex = re.compile(
        r"(?P<categoria>[A-Za-zÀ-ú\s]+?)\s+com\s+(?P<dias>\d+)\s+dias\s+em\s+(?P<loja>[A-Za-zÀ-ú\s]+)\s*\(R\$?\s*(?P<valor>[\d\.\,]+)\)",
        re.IGNORECASE
    )
    for linha in texto.strip().split("\n"):
        m = regex.search(linha.strip())
        if m:
            try:
                dados.append({
                    "Loja": m.group("loja").strip().upper(),
                    "Categoria": m.group("categoria").strip().upper(),
                    "DiasGiro": int(m.group("dias")),
                    "ValorFinanceiro": float(m.group("valor").replace(".", "").replace(",", "."))
                })
            except Exception as e:
                st.warning(f"Erro ao processar linha: {linha} - {e}")
    return pd.DataFrame(dados) if dados else None

df = parse_dashboard(dados_dashboard) if dados_dashboard else None

if df is None or df.empty:
    st.warning("Nenhum dado válido encontrado no arquivo.")
    st.stop()

LOJAS = ["SOCORRO", "SÃO JOSÉ", "EMBU", "ELIANA", "JOÃO DIAS", "ARICANDUVA", "ALVARENGA", "SABARÁ"]

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

st.markdown('</div>', unsafe_allow_html=True)
