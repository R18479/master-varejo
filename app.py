"""
MASTER VAREJO — Powered by AIA
App mobile-first em Streamlit para auditoria de giro de estoque e
capital imobilizado por loja/categoria, com entrada de dados via
texto colado (regex) ou banco de simulação interno de fallback.

Rodar com:
    streamlit run app.py
"""

import re
import hashlib
import unicodedata

import pandas as pd
import streamlit as st

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    page_icon="🔼",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# CONSTANTES DE NEGÓCIO
# =============================================================================

LOJAS = [
    "SOCORRO", "SÃO JOSÉ", "EMBU", "ELIANA",
    "JOÃO DIAS", "ARICANDUVA", "ALVARENGA", "SABARÁ",
]

CATEGORIAS = [
    "AÇOUGUE", "BAZAR", "CESTAS", "CONGELADOS", "FLV", "FRIOS E EMBUTIDOS",
    "IOGURTE", "LATICÍNIOS", "LATICÍNIOS COMMODITIES", "LEITE COMMODITIES",
    "LIMPEZA", "LÍQUIDA", "LÍQUIDA QUENTE", "PADARIA", "PEIXARIA",
    "PERFUMARIA", "SECA COMMODITIES", "SECA DOCE", "SECA SALGADA",
    "TABACARIA", "VESTCASA",
]

# Casos de homologação reais (loja, categoria) -> (giro_dias, valor_imobilizado)
CASOS_HOMOLOGACAO = {
    ("JOÃO DIAS", "BAZAR"): (205, 787171.0),
    ("ALVARENGA", "PERFUMARIA"): (148, 433521.0),
    ("SÃO JOSÉ", "LIMPEZA"): (91, 1899003.0),
    ("SOCORRO", "SECA SALGADA"): (95, 1401360.0),
    ("JOÃO DIAS", "PEIXARIA"): (117, 43769.0),
}

INDICADORES_ESCAPE_FIXO = {
    "media_quebra": -1.49,
    "media_perda": -0.05,
    "escape_total_tt": -1.55,
}


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalizar(texto: str) -> str:
    """Remove acentuação e converte para maiúsculas, para comparações estáveis."""
    sem_acento = unicodedata.normalize("NFD", texto.upper())
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")


@st.cache_data(show_spinner=False)
def montar_banco_simulacao() -> pd.DataFrame:
    """
    Constrói o DataFrame de fallback com todas as combinações Loja x Categoria.
    Usa os 5 casos de homologação reais e, para o restante, gera giro
    controlado padrão entre 15 e 40 dias (determinístico via hash).
    """
    registros = []
    for loja in LOJAS:
        for categoria in CATEGORIAS:
            chave = (loja, categoria)
            if chave in CASOS_HOMOLOGACAO:
                giro, valor = CASOS_HOMOLOGACAO[chave]
                real = True
            else:
                combinado = normalizar(loja) + normalizar(categoria)
                hash_val = int(hashlib.sha256(combinado.encode("utf-8")).hexdigest(), 16)
                giro = 15 + (hash_val % 26)  # intervalo controlado: 15 a 40 dias
                valor = 15000.0 + (hash_val % 78) * 12000.0
                real = False

            registros.append({
                "loja": loja,
                "categoria": categoria,
                "giro_dias": giro,
                "valor_imobilizado": valor,
                "homologado": real,
            })

    return pd.DataFrame(registros)


def buscar_no_texto_colado(texto: str, loja: str, categoria: str):
    """
    Tenta localizar giro (dias) e valor (R$) para a combinação loja/categoria
    dentro do texto colado pelo usuário, usando regex.
    Retorna (giro, valor, encontrado: bool).
    """
    if not texto or not texto.strip():
        return None, None, False

    texto_norm = normalizar(texto)
    loja_norm = normalizar(loja)
    cat_norm = normalizar(categoria)

    if loja_norm not in texto_norm or cat_norm not in texto_norm:
        return None, None, False

    giro_encontrado = None
    valor_encontrado = None

    match_giro = re.search(r"(\d+)\s*(?:DIAS|DIA)", texto_norm)
    if match_giro:
        giro_encontrado = int(match_giro.group(1))

    match_valor = re.search(r"(?:R\$|RS)\s*([\d.,\s]+)", texto, flags=re.IGNORECASE)
    if match_valor:
        bruto = match_valor.group(1).strip()
        limpo = bruto.replace(".", "").replace(",", ".").replace(" ", "")
        try:
            valor_encontrado = float(limpo)
        except ValueError:
            valor_encontrado = None

    encontrado = giro_encontrado is not None or valor_encontrado is not None
    return giro_encontrado, valor_encontrado, encontrado


def formatar_moeda(valor: float) -> str:
    """Formata número no padrão monetário brasileiro: R$ 1.234.567,89"""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def obter_dados(df_simulacao: pd.DataFrame, texto_colado: str, loja: str, categoria: str):
    """
    Resolve os dados finais (giro, valor, origem) para a loja/categoria
    selecionada, priorizando o texto colado e caindo para o banco de
    simulação interno se o texto estiver vazio ou não tiver correspondência.
    """
    giro_regex, valor_regex, encontrado = buscar_no_texto_colado(texto_colado, loja, categoria)

    linha = df_simulacao[
        (df_simulacao["loja"] == loja) & (df_simulacao["categoria"] == categoria)
    ].iloc[0]

    giro_final = giro_regex if giro_regex is not None else int(linha["giro_dias"])
    valor_final = valor_regex if valor_regex is not None else float(linha["valor_imobilizado"])

    if encontrado:
        origem = "Extraído via Expressão Regular (texto colado)"
    elif linha["homologado"]:
        origem = "Dados de Homologação da Rede"
    else:
        origem = "Simulação Interna (giro controlado padrão)"

    return giro_final, valor_final, origem


# =============================================================================
# ESTILO (CSS) — otimizado para toque em telas verticais de smartphone
# =============================================================================

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    .header-container {
        background-color: #0f172a;
        color: #ffffff;
        padding: 22px 16px;
        text-align: center;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        border: 2px solid #2563eb;
    }
    .header-logo {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 0.04em;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 11px;
        color: #93c5fd;
        font-weight: 800;
        letter-spacing: 0.3em;
        margin: 6px 0 0 0;
        text-transform: uppercase;
    }

    textarea {
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #f8fafc !important;
        font-size: 14px !important;
    }

    div.stButton > button {
        width: 100%;
        padding: 14px 12px;
        font-size: 13.5px;
        font-weight: 800;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
        border-bottom: 4px solid #cbd5e1;
        border-radius: 14px;
        transition: all 0.12s ease;
        text-align: left;
        margin-bottom: 6px;
    }
    div.stButton > button:active {
        transform: translateY(2px);
        border-bottom-width: 2px;
    }

    .insight-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 18px;
        margin-top: 14px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .card-title {
        font-size: 11px;
        font-weight: 900;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 10px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# CABEÇALHO
# =============================================================================

st.markdown("""
    <div class="header-container">
        <div class="header-logo">🔼 MASTER VAREJO</div>
        <div class="header-subtitle">Powered by AIA</div>
    </div>
""", unsafe_allow_html=True)

# =============================================================================
# ESTADO DA SESSÃO
# =============================================================================

if "categoria_selecionada" not in st.session_state:
    st.session_state.categoria_selecionada = None
if "loja_selecionada" not in st.session_state:
    st.session_state.loja_selecionada = LOJAS[0]

df_simulacao = montar_banco_simulacao()

# =============================================================================
# ENTRADA DE DADOS: TEXTO COLADO + SELEÇÃO DE LOJA
# =============================================================================

st.markdown("##### 📋 Cole os dados do dashboard (opcional)")
texto_colado = st.text_area(
    label="Texto colado",
    placeholder="Ex: O setor de LIMPEZA registrou 91 dias em São José no valor imobilizado de R$ 1.899.003.",
    height=90,
    label_visibility="collapsed",
    help="Se deixado em branco, o app usa automaticamente o banco de simulação interno.",
)

st.markdown("##### 🏬 Loja monitorada")
st.session_state.loja_selecionada = st.selectbox(
    label="Loja",
    options=LOJAS,
    index=LOJAS.index(st.session_state.loja_selecionada),
    label_visibility="collapsed",
)

# =============================================================================
# MENU TOUCH DE CATEGORIAS (BOTÕES VERTICAIS COMPACTOS)
# =============================================================================

st.markdown("##### 🗂️ Categorias operacionais")
st.caption("Toque em uma categoria para auditar o giro e capital imobilizado.")

for categoria in CATEGORIAS:
    if st.button(categoria, key=f"btn_cat_{categoria}"):
        st.session_state.categoria_selecionada = categoria

    # Exibe o resultado imediatamente abaixo do botão clicado
    if st.session_state.categoria_selecionada == categoria:
        loja_atual = st.session_state.loja_selecionada
        giro, valor, origem = obter_dados(df_simulacao, texto_colado, loja_atual, categoria)
        valor_fmt = formatar_moeda(valor)

        # --- Bloco de Escape Fixo -------------------------------------------------
        st.markdown(f"""
            <div class="insight-card">
                <div class="card-title">📉 Indicadores Globais de Escape Fixo</div>
                <div style="display:flex; justify-content:space-between; text-align:center;">
                    <div>
                        <div style="font-size:9px; color:#64748b; font-weight:700; text-transform:uppercase;">Média Quebra</div>
                        <div style="font-size:15px; font-weight:800; color:#ef4444;">{INDICADORES_ESCAPE_FIXO['media_quebra']}%</div>
                    </div>
                    <div>
                        <div style="font-size:9px; color:#64748b; font-weight:700; text-transform:uppercase;">Média Perda</div>
                        <div style="font-size:15px; font-weight:800; color:#f59e0b;">{INDICADORES_ESCAPE_FIXO['media_perda']}%</div>
                    </div>
                    <div>
                        <div style="font-size:9px; color:#64748b; font-weight:700; text-transform:uppercase;">Escape Total TT</div>
                        <div style="font-size:15px; font-weight:800; color:#dc2626;">{INDICADORES_ESCAPE_FIXO['escape_total_tt']}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- Bloco de Giro Parado ---------------------------------------------------
        if giro > 90:
            cor_status = "#ef4444"
        elif giro > 45:
            cor_status = "#f59e0b"
        else:
            cor_status = "#10b981"

        st.markdown(f"""
            <div class="insight-card">
                <div class="card-title">🎯 Giro Parado</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:11px; color:#64748b; font-weight:700;">{loja_atual}</div>
                        <div style="font-size:22px; font-weight:900; color:{cor_status};">{giro} dias</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:9px; color:#64748b; text-transform:uppercase;">Valor Imobilizado</div>
                        <div style="font-size:16px; font-weight:800; color:#0f172a;">{valor_fmt}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- Bloco de Ação Corretiva -------------------------------------------------
        if giro > 90:
            bg, borda, texto_cor = "#fee2e2", "#ef4444", "#991b1b"
            mensagem = f"🚨 Risco Crítico de Vencimento! Realizar saldão ou transferência urgente na loja {loja_atual}."
        elif giro > 45:
            bg, borda, texto_cor = "#fef3c7", "#f59e0b", "#92400e"
            mensagem = f"⚠️ Atenção! Frear novos pedidos para a loja {loja_atual}."
        else:
            bg, borda, texto_cor = "#d1fae5", "#10b981", "#065f46"
            mensagem = "✅ Operação estável e giro controlado na rede."

        st.markdown(f"""
            <div class="insight-card" style="background-color:{bg}; border-color:{borda};">
                <div class="card-title" style="color:{texto_cor};">🎯 Plano de Ação Corretiva</div>
                <p style="font-size:13px; color:{texto_cor}; font-weight:700; line-height:1.5; margin:0;">{mensagem}</p>
            </div>
        """, unsafe_allow_html=True)

        st.caption(f"Método de obtenção dos dados: {origem}")
