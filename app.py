import io
import re
import pandas as pd
import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# --- Configurações iniciais ---
st.set_page_config(page_title="Master Varejo — Powered by AIA", page_icon="🔼", layout="centered")

# --- Função para carregar a logo ---
def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except Exception:
        return None

logo_img = carregar_logo()

# --- CSS para o layout ---
st.markdown("""
<style>
/* ... seu CSS aqui ... */
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho fixo com logo ---
with st.container():
    st.markdown('<div class="header">', unsafe_allow_html=True)
    if logo_img:
        st.image(logo_img, width=48)
    st.markdown("""
        <div class="header-texts">
            <h1 class="header-title">🔼 MASTER VAREJO</h1>
            <div class="header-subtitle">POWERED BY AIA</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- Bloco de Upload Avançado e Armazenamento ---

def extrair_texto_pdf(uploaded_pdf):
    try:
        import pdfplumber
    except ImportError:
        st.error("Instale pdfplumber com 'pip install pdfplumber' para ler PDFs.")
        return ""
    texto = ""
    try:
        with pdfplumber.open(uploaded_pdf) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texto += text + "\n"
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
            df_excel = pd.read_excel(upload)
            texto = ""
            for _, row in df_excel.iterrows():
                texto += f"{row['Categoria']} com {int(row['Dias'])} dias em {row['Loja']} (R$ {row['Valor']})\n"
            return texto
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")
            return ""
    else:
        st.error("Formato de arquivo não suportado.")
        return ""

# Inicializa variáveis de sessão para armazenar dados e origem
if 'dados_rede' not in st.session_state:
    st.session_state['dados_rede'] = None
if 'origem_dados' not in st.session_state:
    st.session_state['origem_dados'] = None

st.header("Upload arquivo RETINA (PDF)")
uploaded_pdf = st.file_uploader("", type=["pdf"], key="pdf")
if uploaded_pdf:
    texto_pdf = ler_arquivo(uploaded_pdf)
    if texto_pdf:
        st.session_state['dados_rede'] = texto_pdf
        st.session_state['origem_dados'] = 'RETINA'
        st.success("Arquivo RETINA carregado e dados atualizados.")

st.header("Upload arquivo STREAMLING (CSV/XLS/XLSX)")
uploaded_stream = st.file_uploader("", type=["csv", "xls", "xlsx"], key="stream")
if uploaded_stream:
    texto_stream = ler_arquivo(uploaded_stream)
    if texto_stream:
        if st.session_state['origem_dados'] == 'RETINA':
            st.warning("⚠️ Dados RETINA já carregados, priorizados sobre STREAMLING.")
        else:
            st.session_state['dados_rede'] = texto_stream
            st.session_state['origem_dados'] = 'STREAMLING'
            st.success("Arquivo STREAMLING carregado e dados atualizados.")

# --- Mostra preview dos dados carregados ---
if st.session_state['dados_rede']:
    st.markdown(f"Fonte atual dos dados: **{st.session_state['origem_dados']}**")
    st.text_area("Preview dados brutos extraídos:", st.session_state['dados_rede'], height=150)
else:
    st.info("Aguardando upload dos arquivos para processamento.")

# --- Parsing dos dados ---
def parse_dashboard(texto):
    dados = []
    padrao = re.compile(
        r"(?P<categoria>[A-Za-zÀ-ú ]+?) com (?P<dias>\d+) dias em (?P<loja>[A-Za-zÀ-ú ]+?) \(R\$ ?(?P<valor>[\d\.,]+)\)",
        re.IGNORECASE
    )
    for linha in texto.splitlines():
        m = padrao.search(linha.strip())
        if m:
            try:
                dados.append({
                    'Categoria': m.group('categoria').strip().upper(),
                    'Loja': m.group('loja').strip().upper(),
                    'DiasGiro': int(m.group('dias')),
                    'ValorFinanceiro': float(m.group('valor').replace('.', '').replace(',', '.'))
                })
            except:
                continue
    return pd.DataFrame(dados) if dados else None

df = None
if st.session_state['dados_rede']:
    df = parse_dashboard(st.session_state['dados_rede'])

if df is None or df.empty:
    st.warning("Nenhum dado válido para análise.")
    st.stop()

# --- Lista lojas importantes ---
LOJAS = ["SOCORRO", "SÃO JOSÉ", "EMBU"]

# --- Interface em abas ---
tabs = st.tabs(["Todas as Lojas", "Detalhes por Loja", "Comandos Operacionais"])

# Aba Todas as Lojas
with tabs[0]:
    st.subheader("Comparativo Geral das Lojas")
    resumo = df.groupby('Loja').agg({'DiasGiro': 'mean', 'ValorFinanceiro': 'sum'}).reset_index()
    resumo = resumo.rename(columns={
        'DiasGiro': 'Média Dias de Giro',
        'ValorFinanceiro': 'Capital Imobilizado (R$)'
    })
    resumo["Média Dias de Giro"] = resumo["Média Dias de Giro"].round(1)
    resumo["Capital Imobilizado (R$)"] = resumo["Capital Imobilizado (R$)"].apply(
        lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    )
    st.dataframe(resumo.style.set_properties(**{'text-align': 'center'}))

    # KPI acumulado
    media_giro_geral = resumo["Média Dias de Giro"].mean().round(1)
    soma_valores = resumo["Capital Imobilizado (R$)"].apply(
        lambda x: float(x.replace('R$ ', '').replace('.', '').replace(',', '.'))
    ).sum()
    soma_valores_fmt = f"R$ {soma_valores:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    st.markdown(f"""
    <div style="padding:10px; max-width:350px; background:#e6f2ff; border-radius:10px; margin-top:15px;">
    <strong>Média Geral dos Dias de Giro:</strong> {media_giro_geral} dias<br/>
    <strong>Capital Imobilizado Total:</strong> {soma_valores_fmt}
    </div>
    """, unsafe_allow_html=True)

# Aba Detalhes por Loja
with tabs[1]:
    loja = st.selectbox("Selecione a loja", sorted(df['Loja'].unique()))
    if loja:
        df_loja = df[df['Loja'] == loja]
        st.markdown(f"### Dados detalhados da loja {loja.title()}")
        for _, row in df_loja.iterrows():
            valor_fmt = f"R$ {row['ValorFinanceiro']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            st.markdown(f"""
            <div class="category-card">
                <strong>Categoria:</strong> {row['Categoria'].title()}<br/>
                <strong>Dias de Giro:</strong> {row['DiasGiro']} dias<br/>
                <strong>Capital Imobilizado:</strong> {valor_fmt}
            </div>
            """, unsafe_allow_html=True)

        # Geração do PDF
        def gerar_pdf(loja, df_data):
            buffer = io.BytesIO()
            estilos = getSampleStyleSheet()
            titulo = ParagraphStyle("Titulo", parent=estilos["Heading1"], fontName="Helvetica-Bold",
                                   fontSize=20, alignment=1, textColor=colors.HexColor("#053c5e"), spaceAfter=12)
            subtitulo = ParagraphStyle("Subtitulo", parent=estilos["Normal"], fontName="Helvetica-Bold",
                                      fontSize=11, alignment=1, textColor=colors.HexColor("#666666"), spaceAfter=20)
            corpo = ParagraphStyle("Corpo", parent=estilos["Normal"], fontSize=11, leading=18)
            rodape = ParagraphStyle("Rodape", parent=estilos["Normal"], fontSize=8, alignment=1, textColor=colors.grey)

            doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)

            story = [Paragraph("🔺 MASTER VAREJO", titulo),
                     Paragraph(f"Laudo detalhado para a loja {loja.title()}", subtitulo),
                     Spacer(1, 20)]

            for _, row in df_data.iterrows():
                valor_fmt = f"R$ {row['ValorFinanceiro']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                texto = f"<b>Categoria:</b> {row['Categoria'].title()}<br/>" \
                        f"<b>Dias de Giro:</b> {row['DiasGiro']} dias<br/>" \
                        f"<b>Capital Imobilizado:</b> {valor_fmt}"
                story.append(Paragraph(texto, corpo))
                story.append(Spacer(1, 12))

            story.append(Spacer(1, 30))
            story.append(Paragraph("Documento gerado automaticamente pelo AIA.", rodape))

            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()

        pdf_bytes = gerar_pdf(loja, df_loja)
        st.download_button("📄 Baixar Laudo PDF", pdf_bytes, file_name=f"laudo_{loja.replace(' ', '_')}.pdf", mime="application/pdf")

# Aba Comandos Operacionais (exemplo de uso)
with tabs[2]:
    st.markdown("### Comandos disponíveis")
    st.markdown("""
    - **/PAINEL:** Exibe ranking de todas as lojas e os 3 alertas mais críticos.
    - **/CATEGORIAS:** Ranking detalhado de categorias.
    - **/LOJAS:** KPI das lojas.
    - **/VALIDAR:** Validation cross-check RETINA vs STREAMLING.
    - **/LAUDO:** Resumo executivo.
    - **/ATUALIZAR:** Reprocessa o último arquivo.
    """)

st.markdown('</div>', unsafe_allow_html=True)
