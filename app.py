import streamlit as st
import pandas as pd
import re
from PIL import Image

st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🔼"
)

# Função para carregar a logo localmente
def carregar_logo():
    try:
        return Image.open("logo_master_varejo.png")
    except Exception:
        return None

logo_img = carregar_logo()

# CSS para cabeçalho fixo escuro e layout limpo mobile
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

# Cabeçalho fixo com logo e textos
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

dados_dashboard = st.text_area(
    "Cole o texto completo do dashboard (ex: Categoria com X dias em Loja (R$ Valor))",
    height=180,
    max_chars=20000,
    placeholder="Exemplo:\nBAZAR com 205 dias em João Dias (R$ 433.521)\nLIMPEZA com 91 dias em São José (R$ 1.401.360)\nPEIXARIA com 117 dias em João Dias (R$ 43.769)\n..."
)

def parse_dashboard(texto: str):
    import pandas as pd
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

if dados_dashboard.strip():
    with st.spinner("Processando dados..."):
        df = parse_dashboard(dados_dashboard)
else:
    df = None

if df is None:
    st.warning("Cole dados válidos do dashboard para análise.")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

lojas = sorted(df["Loja"].unique())
loja_escolhida = st.selectbox("Selecione a loja para visualizar dados", lojas)

if loja_escolhida:
    df_loja = df[df["Loja"] == loja_escolhida]
    st.markdown(f"### Dados para a loja **{loja_escolhida.title()}**")
    for _, row in df_loja.iterrows():
        valor_fmt = f"R$ {row['ValorFinanceiro']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"""
        <div class="category-card">
            <strong>Categoria:</strong> {row['Categoria'].title()}<br>
            <strong>Dias de Giro:</strong> {row['DiasGiro']} dias<br>
            <strong>Valor Financeiro:</strong> {valor_fmt}
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
