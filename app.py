import streamlit as st
import pandas as pd
import re
import io
from PIL import Image

# Configuração da página
st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🔼"
)

# --- Carrega a logo da empresa ---
def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except Exception:
        return None

logo_img = carregar_logo()

# --- Estilo CSS para cabeçalho fixo escuro, layout mobile e cartões ---
st.markdown("""
<style>
/* Cabeçalho fixo escuro */
.header {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: #111111;
    color: white;
    padding: 10px 15px;
    display: flex;
    align-items: center;
    z-index: 1200;
    gap: 15px;
    box-shadow: 0 2px 8px #0009;
}
.header-texts {
    display: flex;
    flex-direction: column;
}
/* Títulos no cabeçalho */
.header-title {
    font-weight: 700;
    font-size: 22px;
    margin: 0;
    letter-spacing: 2px;
    user-select: none;
}
.header-subtitle {
    font-weight: 400;
    font-size: 10px;
    color: #888888;
    text-transform: uppercase;
    letter-spacing: 4px;
    user-select: none;
}
/* Espaço abaixo do cabeçalho */
.main-content {
    margin-top: 70px;
    padding: 10px 15px 70px 15px;
}
/* Caixa de texto grande */
textarea.css-1cpxqw2 {
    font-family: monospace;
    font-size: 14px;
}
/* Botões grandes para toque */
.category-button > button, .loja-button > button {
    width: 100%;
    min-height: 48px;
    font-size: 18px;
    margin-bottom: 8px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
}
/* Cartões de categoria */
.card {
    border-radius: 14px;
    padding: 15px 20px;
    margin-top: 12px;
    box-shadow: 0 1px 8px #aaa8;
    background-color: #f0f8ff;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.card strong {
    font-size: 16px;
}
/* Layout flex vertical */
.flex-col {
    display: flex;
    flex-direction: column;
}
/* Loading spinner center */
.loading-container {
    display: flex;
    justify-content: center;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- Cabeçalho fixo com logo e textos ---
with st.container():
    st.markdown('<div class="header">', unsafe_allow_html=True)
    if logo_img:
        st.image(logo_img, width=48)
    st.markdown("""
    <div class="header-texts">
        <h1 class="header-title">🔼 MASTER VAREJO</h1>
        <div class="header-subtitle">POWERED BY AIA</div>
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# --- Entrada de dados: colar dashboard ---
dados_dashboard = st.text_area(
    label="Cole aqui o texto completo do dashboard (categoria, loja, dias de giro e valor financeiro)",
    height=180,
    max_chars=20000,
    placeholder="Exemplo:\nBAZAR com 205 dias em João Dias (R$ 433.521)\nLIMPEZA com 91 dias em São José (R$ 1.401.360)\n...",
    key="dados_dashboard"
)

# Função para extrair dados do texto, linha por linha, fielmente
def parse_dashboard(texto: str):
    """
    Parseia o texto do dashboard e retorna DataFrame com colunas:
    Loja, Categoria, DiasGiro (int), ValorFinanceiro (float)
    """
    dados = []
    # Regex flexível para linhas: categoria com dias dias em loja (R$ valor)
    padrao = re.compile(
        r"(?P<categoria>[A-Za-zÀ-ú\s]+?)\s+com\s+"  # Categoria (flexível)
        r"(?P<dias>\d+)\s+dias\s+em\s+"            # Dias
        r"(?P<loja>[A-Za-zÀ-ú\s]+)\s*"
        r"\(R\$?\s*(?P<valor>[\d\.\,]+)\)",        # Valor
        re.IGNORECASE
    )
    for linha in texto.strip().split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        m = padrao.search(linha)
        if m:
            categoria = m.group("categoria").strip().upper()
            loja = m.group("loja").strip().upper()
            try:
                dias = int(m.group("dias"))
            except:
                dias = 0
            valor_str = m.group("valor").replace(".", "").replace(",", ".")
            try:
                valor = float(valor_str)
            except:
                valor = 0.0
            dados.append({
                "Loja": loja,
                "Categoria": categoria,
                "DiasGiro": dias,
                "ValorFinanceiro": valor
            })
    df = pd.DataFrame(dados)
    if df.empty:
        return None
    return df

df_dashboard = None
if dados_dashboard.strip():
    with st.spinner("Processando dados do dashboard..."):
        df_dashboard = parse_dashboard(dados_dashboard)

# --- Seleção das lojas presentes ---
if df_dashboard is None or df_dashboard.empty:
    st.warning("Por favor, cole dados válidos do dashboard para análise.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

lojas_unicas = sorted(df_dashboard["Loja"].unique())

# Seleciona loja para exibir dados
loja_selecionada = st.selectbox("Selecione a Loja para análise", lojas_unicas)

# --- Exibe categorias e dados da loja selecionada ---
if loja_selecionada:
    dados_loja = df_dashboard[df_dashboard["Loja"] == loja_selecionada]
    if dados_loja.empty:
        st.info(f"Nenhum dado encontrado para a loja {loja_selecionada}.")
    else:
        st.markdown(f"### Dados para a loja **{loja_selecionada.title()}**")
        for _, row in dados_loja.iterrows():
            valor_format = f"R$ {row['ValorFinanceiro']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.markdown(f"""
            <div class="card">
                <strong>Categoria:</strong> {row['Categoria'].title()}<br/>
                <strong>Dias de Giro:</strong> {row['DiasGiro']} dias<br/>
                <strong>Valor Financeiro:</strong> {valor_format}
            </div>
            """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
