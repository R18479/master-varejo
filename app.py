import io
import os
import re
import csv
import hashlib
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

try:
    import pdfplumber
    PDF_SUPORTADO = True
except ImportError:
    PDF_SUPORTADO = False


# =============================================================================
# CONFIGURAÇÃO GERAL / CONSTANTES
# =============================================================================

LOG_AUDITORIA_PATH = os.path.join(os.path.dirname(__file__), "audit_log.csv")

# Credenciais simples de acesso (ideal: mover para variável de ambiente / st.secrets)
USUARIOS_VALIDOS = {
    "admin": hashlib.sha256("master2026".encode()).hexdigest(),
    "gestor": hashlib.sha256("varejo2026".encode()).hexdigest(),
}

# Lojas monitoradas com respectiva UF (necessário para cruzamento de dados por estado)
LOJAS_UF = {
    "SOCORRO": "SP",
    "SÃO JOSÉ": "SC",
    "EMBU": "SP",
    "ELIANA": "SP",
    "JOÃO DIAS": "SP",
    "ARICANDUVA": "SP",
    "ALVARENGA": "SP",
    "SABARÁ": "MG",
}
LOJAS_MONITORADAS = list(LOJAS_UF.keys())

CATEGORIAS_OPERACIONAIS = [
    "AÇOUGUE", "BAZAR", "CESTAS", "CONGELADOS", "FLV", "FRIOS E EMBUTIDOS", "IOGURTE",
    "LATICÍNIOS", "LATICÍNIOS COMMODITIES", "LEITE COMMODITIES", "LIMPEZA", "LÍQUIDA",
    "LÍQUIDA QUENTE", "PADARIA", "PEIXARIA", "PERFUMARIA", "SECA COMMODITIES",
    "SECA DOCE", "SECA SALGADA", "TABACARIA", "VESTCASA"
]


# =============================================================================
# FUNÇÕES DE NEGÓCIO
# =============================================================================

def gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao):
    """
    Gera um laudo de auditoria de máquina em PDF usando ReportLab.
    Retorna os bytes do PDF gerado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'LaudoTitle', parent=styles['Heading1'], fontSize=22, leading=26,
        textColor=colors.HexColor('#0f172a'), alignment=1, spaceAfter=10
    )
    subtitle_style = ParagraphStyle(
        'LaudoSubtitle', parent=styles['Normal'], fontSize=10, leading=14,
        textColor=colors.HexColor('#64748b'), alignment=1, spaceAfter=20
    )
    section_style = ParagraphStyle(
        'LaudoSection', parent=styles['Heading2'], fontSize=13, leading=16,
        textColor=colors.HexColor('#1e3a8a'), spaceBefore=12, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'LaudoBody', parent=styles['Normal'], fontSize=10, leading=14,
        textColor=colors.HexColor('#334155'), spaceAfter=6
    )
    body_bold_style = ParagraphStyle('LaudoBodyBold', parent=body_style, fontName='Helvetica-Bold')

    story.append(Paragraph("🔼 MASTER VAREJO - LAUDO DE AUDITORIA", title_style))
    story.append(Paragraph("Relatório gerencial gerado automaticamente pelo AIA Core Engine", subtitle_style))
    story.append(Spacer(1, 10))

    valor_fmt = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if isinstance(valor, (int, float)) else str(valor)
    uf_loja = LOJAS_UF.get(loja, "-")

    table_data = [
        [Paragraph("<b>Indicador de Controle</b>", body_bold_style), Paragraph("<b>Valor Registrado</b>", body_bold_style)],
        [Paragraph("Unidade Monitorada (Loja):", body_style), Paragraph(f"{loja} ({uf_loja})", body_style)],
        [Paragraph("Categoria Operacional:", body_style), Paragraph(str(categoria), body_style)],
        [Paragraph("Dias de Cobertura (Giro):", body_style), Paragraph(f"{giro} dias", body_style)],
        [Paragraph("Capital Imobilizado em Estoque:", body_style), Paragraph(valor_fmt, body_style)],
    ]

    t = Table(table_data, colWidths=[220, 280])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    story.append(Paragraph("🎯 Plano de Ação AIA Recomendado", section_style))

    if giro > 90:
        bg_color_hex, border_color_hex, text_color_hex = '#fee2e2', '#ef4444', '#991b1b'
    elif giro > 45:
        bg_color_hex, border_color_hex, text_color_hex = '#fef3c7', '#f59e0b', '#92400e'
    else:
        bg_color_hex, border_color_hex, text_color_hex = '#d1fae5', '#10b981', '#065f46'

    plano_text_style = ParagraphStyle(
        'PlanoTextStyle', parent=styles['Normal'], fontSize=10, leading=14,
        textColor=colors.HexColor(text_color_hex)
    )

    plano_data = [[Paragraph(str(plano_acao), plano_text_style)]]
    plano_table = Table(plano_data, colWidths=[500])
    plano_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color_hex)),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(border_color_hex)),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(plano_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("📉 Indicadores Globais de Escape Fixo", section_style))
    escape_data = [
        [Paragraph("<b>Média Quebra</b>", body_bold_style), Paragraph("<b>Média Perda</b>", body_bold_style), Paragraph("<b>Escape Total TT</b>", body_bold_style)],
        [Paragraph("<font color='#ef4444'>-1,49%</font>", body_bold_style), Paragraph("<font color='#f59e0b'>-0,05%</font>", body_bold_style), Paragraph("<font color='#dc2626'>-1,55%</font>", body_bold_style)]
    ]
    escape_table = Table(escape_data, colWidths=[166, 166, 168])
    escape_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(escape_table)
    story.append(Spacer(1, 25))

    footer_style = ParagraphStyle(
        'LaudoFooter', parent=styles['Normal'], fontSize=8, leading=11,
        textColor=colors.HexColor('#94a3b8'), alignment=1
    )
    story.append(Paragraph("Este documento é um relatório gerencial confidencial para monitoramento interno de giros de estoque.", footer_style))
    story.append(Paragraph("Gerado de acordo com as regras de negócios da Rede de Lojas do Master Varejo.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def normalizar(texto):
    """Remove acentuação e coloca em maiúsculas para comparação estável."""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.upper()) if unicodedata.category(c) != 'Mn')


@st.cache_data(show_spinner=False)
def obter_dados_loja_categoria(loja, categoria):
    """Função determinística estável para simular dados realistas por Loja + Categoria."""
    loja_norm = normalizar(loja)
    cat_norm = normalizar(categoria)

    if cat_norm == "BAZAR" and loja_norm == "JOAO DIAS":
        return 205, 787171.0, True
    if cat_norm == "PERFUMARIA" and loja_norm == "ALVARENGA":
        return 148, 433521.0, True
    if cat_norm == "LIMPEZA" and loja_norm == "SAO JOSE":
        return 91, 1899003.0, True
    if cat_norm == "SECA SALGADA" and loja_norm == "SOCORRO":
        return 95, 1401360.0, True
    if cat_norm == "PEIXARIA" and loja_norm == "JOAO DIAS":
        return 117, 43769.0, True

    combinado = loja_norm + cat_norm
    hash_val = 0
    for char in combinado:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
    hash_val = abs(hash_val)

    giro = 12 + (hash_val % 104)
    valor = 15000.0 + (hash_val % 78) * 12000.0

    return giro, valor, False


@st.cache_data(show_spinner=False)
def obter_venda_atual_loja(loja):
    """Simula a venda atual consolidada de uma loja (determinístico e estável)."""
    loja_norm = normalizar(loja)
    hash_val = 0
    for char in loja_norm:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
    hash_val = abs(hash_val)
    venda = 250000.0 + (hash_val % 120) * 15000.0
    return venda


def extrair_texto_pdf(arquivo_pdf):
    """Extrai texto de um PDF enviado via upload usando pdfplumber."""
    texto_total = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto_total.append(texto_pagina)
    return "
".join(texto_total)


def registrar_log_auditoria(usuario, loja, categoria, giro, valor):
    """Registra em CSV cada retirada/geração de laudo, para rastreabilidade."""
    novo_registro = {
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "usuario": usuario,
        "loja": loja,
        "uf": LOJAS_UF.get(loja, "-"),
        "categoria": categoria,
        "giro_dias": giro,
        "valor_imobilizado": valor,
    }
    arquivo_existe = os.path.isfile(LOG_AUDITORIA_PATH)
    with open(LOG_AUDITORIA_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(novo_registro.keys()))
        if not arquivo_existe:
            writer.writeheader()
        writer.writerow(novo_registro)


def carregar_log_auditoria():
    if not os.path.isfile(LOG_AUDITORIA_PATH):
        return pd.DataFrame(columns=["data_hora", "usuario", "loja", "uf", "categoria", "giro_dias", "valor_imobilizado"])
    return pd.read_csv(LOG_AUDITORIA_PATH)


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# =============================================================================

st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    page_icon="🔼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }

    .header-container {
        background-color: #0f172a;
        color: #ffffff;
        padding: 20px 14px;
        text-align: center;
        border-radius: 16px;
        margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        border: 2px solid #2563eb;
        position: relative;
    }
    .header-logo {
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 0.05em;
        margin: 0;
        color: #ffffff;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
    }
    .header-logo span { color: #3b82f6; }
    .header-subtitle {
        font-size: 10px;
        color: #94a3b8;
        font-weight: 700;
        letter-spacing: 0.25em;
        margin: 6px 0 0 0;
        text-transform: uppercase;
    }

    textarea {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #f8fafc !important;
        font-size: 14px !important;
    }

    div.stButton > button {
        width: 100%;
        padding: 12px 14px;
        font-size: 13px;
        font-weight: 700;
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #e2e8f0;
        border-bottom: 4px solid #cbd5e1;
        border-radius: 12px;
        transition: all 0.15s ease;
        text-align: center;
        margin-bottom: 2px;
    }
    div.stButton > button:hover {
        background-color: #e2e8f0;
        border-color: #cbd5e1;
        color: #0f172a;
    }
    div.stButton > button:active {
        transform: translateY(2px);
        border-bottom-width: 2px;
    }

    .active-btn {
        background-color: #2563eb !important;
        color: white !important;
        border-bottom-color: #1d4ed8 !important;
    }

    .insight-card {
        background-color: #FFFFFF;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
        margin-top: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .card-title {
        font-size: 12px;
        font-weight: 800;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 12px;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 8px;
    }

    .stAlert {
        border-radius: 14px !important;
        padding: 14px !important;
    }

    .login-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 24px;
        margin-top: 40px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    </style>
""", unsafe_allow_html=True)


# =============================================================================
# 0. AUTENTICAÇÃO (tela de origem / login)
# =============================================================================

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None

if not st.session_state.autenticado:
    st.markdown("""
        <div class="header-container">
            <div class="header-logo"><span>🔼</span> MASTER VAREJO</div>
            <div class="header-subtitle">Powered by AIA Core Engine</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("#### 🔐 Acesso ao Painel")
    usuario_input = st.text_input("Usuário")
    senha_input = st.text_input("Senha", type="password")
    entrar = st.button("Entrar", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if entrar:
        hash_digitado = hashlib.sha256(senha_input.encode()).hexdigest()
        if usuario_input in USUARIOS_VALIDOS and USUARIOS_VALIDOS[usuario_input] == hash_digitado:
            st.session_state.autenticado = True
            st.session_state.usuario_logado = usuario_input
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

    st.stop()


# =============================================================================
# 1. CABEÇALHO
# =============================================================================

col_header, col_logout = st.columns([4, 1])
with col_header:
    st.markdown("""
        <div class="header-container">
            <div class="header-logo"><span>🔼</span> MASTER VAREJO</div>
            <div class="header-subtitle">Powered by AIA Core Engine</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown(f"<p style='font-size:12px;color:#64748b;margin-top:-14px;'>Usuário: <b>{st.session_state.usuario_logado}</b></p>", unsafe_allow_html=True)
if st.button("Sair", key="btn_logout"):
    st.session_state.autenticado = False
    st.session_state.usuario_logado = None
    st.rerun()


# =============================================================================
# 2. NAVEGAÇÃO POR ABAS: Painel Individual | Visão Geral | Comparativo | Auditoria
# =============================================================================

aba_individual, aba_geral, aba_comparativo, aba_auditoria = st.tabs(
    ["🏬 Painel Individual", "🌐 Visão Geral", "⚖️ Comparativo", "📋 Auditoria"]
)


# -----------------------------------------------------------------------------
# ABA: PAINEL INDIVIDUAL (fluxo original, com entrada por PDF adicionada)
# -----------------------------------------------------------------------------
with aba_individual:

    st.markdown("### 📋 Entrada de Dados")
    modo_entrada = st.radio(
        "Como deseja inserir os dados?",
        ["Upload de PDF", "Colar texto"],
        horizontal=True,
        label_visibility="collapsed"
    )

    raw_data_input = ""

    if modo_entrada == "Upload de PDF":
        if not PDF_SUPORTADO:
            st.warning("Suporte a PDF indisponível no ambiente atual (pdfplumber não instalado).")
        else:
            arquivo_pdf = st.file_uploader("Envie o PDF do painel", type=["pdf"])
            if arquivo_pdf is not None:
                with st.spinner("Extraindo dados do PDF..."):
                    raw_data_input = extrair_texto_pdf(arquivo_pdf)
                st.success("PDF processado com sucesso. Dados extraídos automaticamente.")
                with st.expander("Ver texto extraído"):
                    st.text(raw_data_input[:3000])
    else:
        raw_data_input = st.text_area(
            label="Insira dados de texto bruto do seu painel aqui para análise regex instantânea:",
            placeholder="Exemplo de colar: O setor de LIMPEZA registrou 91 dias em São José no valor imobilizado de R$ 1.899.003.",
            height=90,
            help="O app usa expressões regulares para extrair Loja, Giro e Valor do texto e selecionar automaticamente!"
        )

    if "loja_ativa" not in st.session_state:
        st.session_state.loja_ativa = "JOÃO DIAS"
    if "categoria_ativa" not in st.session_state:
        st.session_state.categoria_ativa = "BAZAR"

    if raw_data_input.strip():
        texto_analise = raw_data_input.upper()

        for loja in LOJAS_MONITORADAS:
            loja_norm = normalizar(loja)
            loja_clean = re.sub(r'[ÃÕÁÉÍÓÚ]', '.', loja)
            if re.search(loja_clean, texto_analise) or loja_norm in texto_analise:
                st.session_state.loja_ativa = loja
                break

        for cat in CATEGORIAS_OPERACIONAIS:
            cat_norm = normalizar(cat)
            if cat in texto_analise or cat_norm in texto_analise:
                st.session_state.categoria_ativa = cat
                break

    st.markdown("### 🏬 Selecione a Loja Monitorada")
    st.markdown("<p style='font-size: 13px; color: #64748b; margin-top: -8px; margin-bottom: 12px;'>Escolha a unidade física para auditar suas respectivas categorias:</p>", unsafe_allow_html=True)

    cols_lojas = st.columns(4)
    for idx, loja in enumerate(LOJAS_MONITORADAS):
        col_idx = idx % 4
        criticas_count = 0
        atencao_count = 0
        for c in CATEGORIAS_OPERACIONAIS:
            g, _, _ = obter_dados_loja_categoria(loja, c)
            if g > 90:
                criticas_count += 1
            elif g > 45:
                atencao_count += 1

        marcador = "🔴" if criticas_count > 0 else ("🟡" if atencao_count > 0 else "🟢")
        label_loja = f"{marcador} {loja}"

        if st.session_state.loja_ativa == loja:
            label_loja = f"👉 {loja.upper()}"

        if cols_lojas[col_idx].button(label_loja, key=f"btn_loja_{loja}"):
            st.session_state.loja_ativa = loja
            st.rerun()

    loja_atual = st.session_state.loja_ativa
    st.markdown(f"### 🗂️ Categorias em **{loja_atual}** ({LOJAS_UF.get(loja_atual)})")
    st.markdown("<p style='font-size: 13px; color: #64748b; margin-top: -8px; margin-bottom: 12px;'>Toque em qualquer categoria para disparar o plano de ação correspondente:</p>", unsafe_allow_html=True)

    criticas_list, atencao_list, estaveis_list = [], [], []
    for cat in CATEGORIAS_OPERACIONAIS:
        giro, valor, _ = obter_dados_loja_categoria(loja_atual, cat)
        if giro > 90:
            criticas_list.append((cat, giro, valor))
        elif giro > 45:
            atencao_list.append((cat, giro, valor))
        else:
            estaveis_list.append((cat, giro, valor))

    def render_categoria_botoes(lista_categorias, emoji):
        if not lista_categorias:
            st.markdown("<p style='font-size: 12px; color: #94a3b8; font-style: italic;'>Nenhuma categoria encontrada.</p>", unsafe_allow_html=True)
            return
        cols = st.columns(2)
        for idx, (cat, giro, valor) in enumerate(lista_categorias):
            col_idx = idx % 2
            label = f"{emoji} {cat} ({giro}d)"
            if st.session_state.categoria_ativa == cat:
                label = f"🔥 {cat.upper()}"
            if cols[col_idx].button(label, key=f"btn_cat_{loja_atual}_{cat}"):
                st.session_state.categoria_ativa = cat
                st.rerun()

    with st.expander(f"🔴 GIRO CRÍTICO (>90 dias) — {len(criticas_list)} Categorias", expanded=True):
        render_categoria_botoes(criticas_list, "🚨")
    with st.expander(f"🟡 EM ATENÇÃO (45-90 dias) — {len(atencao_list)} Categorias", expanded=False):
        render_categoria_botoes(atencao_list, "⚠️")
    with st.expander(f"🟢 GIRO CONTROLADO (<45 dias) — {len(estaveis_list)} Categorias", expanded=False):
        render_categoria_botoes(estaveis_list, "✅")

    if st.session_state.categoria_ativa:
        cat_atual = st.session_state.categoria_ativa
        giro_det, valor_det, is_real = obter_dados_loja_categoria(loja_atual, cat_atual)

        metodo_obtencao = "Dados de Homologação da Rede" if is_real else "Dados Oficiais / Simulação Integrada"

        if raw_data_input.strip():
            texto_analise = raw_data_input.upper()
            if cat_atual in texto_analise or normalizar(cat_atual) in texto_analise:
                regex_giro = re.search(r'(d+)s*(?:DIAS|DIA|G)', texto_analise)
                if regex_giro:
                    giro_det = int(regex_giro.group(1))
                    metodo_obtencao = "Extraído via Expressão Regular (Regex)"

                regex_valor = re.search(r'(?:R$|RS)s*([d.,s]+)', texto_analise)
                if regex_valor:
                    val_str = regex_valor.group(1).replace('.', '').replace(',', '.').replace(' ', '').strip()
                    try:
                        valor_det = float(val_str)
                        metodo_obtencao = "Extraído via Expressão Regular (Regex)"
                    except ValueError:
                        pass

        valor_formatado = f"R$ {valor_det:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        st.markdown("---")
        st.markdown(f"### 📊 Painel de Auditoria: **{cat_atual}** em **{loja_atual}**")
        st.caption(f"Método de obtenção: {metodo_obtencao}")

        st.markdown(f"""
            <div class="insight-card">
                <div class="card-title">📉 Indicadores Globais de Escape Fixo</div>
                <div style="display: flex; justify-content: space-between; text-align: center; margin-top: 5px;">
                    <div>
                        <div style="font-size: 9px; color: #64748b; font-weight: 700; text-transform: uppercase;">Média Quebra</div>
                        <div style="font-size: 14px; font-weight: 800; color: #ef4444; margin-top: 2px;">-1,49%</div>
                    </div>
                    <div>
                        <div style="font-size: 9px; color: #64748b; font-weight: 700; text-transform: uppercase;">Média Perda</div>
                        <div style="font-size: 14px; font-weight: 800; color: #f59e0b; margin-top: 2px;">-0,05%</div>
                    </div>
                    <div>
                        <div style="font-size: 9px; color: #64748b; font-weight: 700; text-transform: uppercase;">Escape Total TT</div>
                        <div style="font-size: 14px; font-weight: 800; color: #dc2626; margin-top: 2px;">-1,55%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        if giro_det > 90:
            status_cor, status_label = "#ef4444", "CRÍTICO"
            plano_acao = (
                f"Giro de {giro_det} dias indica capital parado acima do aceitável. "
                f"Recomenda-se ação imediata: promoção agressiva, transferência de estoque entre lojas "
                f"e revisão do plano de compras para a categoria {cat_atual}."
            )
        elif giro_det > 45:
            status_cor, status_label = "#f59e0b", "ATENÇÃO"
            plano_acao = (
                f"Giro de {giro_det} dias está acima do ideal. "
                f"Sugerido monitoramento semanal e ações pontuais de giro (destaque em ponto de venda) "
                f"para a categoria {cat_atual}."
            )
        else:
            status_cor, status_label = "#10b981", "CONTROLADO"
            plano_acao = (
                f"Giro de {giro_det} dias dentro do padrão esperado para {cat_atual}. "
                f"Manter reposição regular e acompanhamento padrão."
            )

        st.markdown(f"""
            <div class="insight-card">
                <div class="card-title">🎯 Giro Detectado</div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size: 22px; font-weight: 900; color:{status_cor};">{giro_det} dias</div>
                        <div style="font-size: 11px; font-weight: 700; color:{status_cor}; text-transform:uppercase;">{status_label}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size: 9px; color:#64748b; text-transform:uppercase;">Valor Imobilizado</div>
                        <div style="font-size: 16px; font-weight:800; color:#0f172a;">{valor_formatado}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="insight-card">
                <div class="card-title">🎯 Plano de Ação AIA Recomendado</div>
                <p style="font-size: 13px; color:#334155; line-height:1.5;">{plano_acao}</p>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        pdf_bytes = gerar_laudo_maquina(loja_atual, cat_atual, giro_det, valor_det, plano_acao)

        if st.download_button(
            label="⬇️ Baixar Laudo de Auditoria (PDF)",
            data=pdf_bytes,
            file_name=f"laudo_{normalizar(loja_atual)}_{normalizar(cat_atual)}.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_laudo"
        ):
            registrar_log_auditoria(st.session_state.usuario_logado, loja_atual, cat_atual, giro_det, valor_det)


# -----------------------------------------------------------------------------
# ABA: VISÃO GERAL (todas as lojas)
# -----------------------------------------------------------------------------
with aba_geral:
    st.markdown("### 🌐 Visão Geral — Todas as Lojas")
    st.markdown("<p style='font-size:13px;color:#64748b;margin-top:-8px;'>Nome da loja e venda atual consolidada:</p>", unsafe_allow_html=True)

    linhas_geral = []
    for loja in LOJAS_MONITORADAS:
        venda = obter_venda_atual_loja(loja)
        criticas = sum(1 for c in CATEGORIAS_OPERACIONAIS if obter_dados_loja_categoria(loja, c)[0] > 90)
        linhas_geral.append({
            "Loja": loja,
            "UF": LOJAS_UF[loja],
            "Venda Atual": venda,
            "Categorias Críticas": criticas,
        })

    df_geral = pd.DataFrame(linhas_geral).sort_values("Venda Atual", ascending=False)
    df_geral_fmt = df_geral.copy()
    df_geral_fmt["Venda Atual"] = df_geral_fmt["Venda Atual"].apply(
        lambda v: f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    )

    st.dataframe(df_geral_fmt, use_container_width=True, hide_index=True)

    st.markdown("### 📊 Venda por Loja")
    st.bar_chart(df_geral.set_index("Loja")["Venda Atual"])

    st.markdown("### 🗺️ Cruzamento de Informações por UF")
    df_uf = df_geral.groupby("UF").agg(
        Total_Vendas=("Venda Atual", "sum"),
        Qtd_Lojas=("Loja", "count"),
        Total_Categorias_Criticas=("Categorias Críticas", "sum")
    ).reset_index()
    df_uf_fmt = df_uf.copy()
    df_uf_fmt["Total_Vendas"] = df_uf_fmt["Total_Vendas"].apply(
        lambda v: f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    )
    st.dataframe(df_uf_fmt, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# ABA: COMPARATIVO ENTRE LOJAS
# -----------------------------------------------------------------------------
with aba_comparativo:
    st.markdown("### ⚖️ Comparativo entre Lojas")

    lojas_selecionadas = st.multiselect(
        "Selecione 2 ou mais lojas para comparar",
        options=LOJAS_MONITORADAS,
        default=LOJAS_MONITORADAS[:2]
    )

    categoria_comparativo = st.selectbox("Categoria para comparação", options=CATEGORIAS_OPERACIONAIS)

    if len(lojas_selecionadas) >= 2:
        dados_comp = []
        for loja in lojas_selecionadas:
            giro, valor, _ = obter_dados_loja_categoria(loja, categoria_comparativo)
            dados_comp.append({"Loja": loja, "UF": LOJAS_UF[loja], "Giro (dias)": giro, "Valor Imobilizado": valor})

        df_comp = pd.DataFrame(dados_comp)
        df_comp_fmt = df_comp.copy()
        df_comp_fmt["Valor Imobilizado"] = df_comp_fmt["Valor Imobilizado"].apply(
            lambda v: f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        )

        st.dataframe(df_comp_fmt, use_container_width=True, hide_index=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Giro (dias)**")
            st.bar_chart(df_comp.set_index("Loja")["Giro (dias)"])
        with col_b:
            st.markdown("**Valor Imobilizado**")
            st.bar_chart(df_comp.set_index("Loja")["Valor Imobilizado"])
    else:
        st.info("Selecione ao menos 2 lojas para visualizar o comparativo.")


# -----------------------------------------------------------------------------
# ABA: AUDITORIA (histórico de laudos gerados)
# -----------------------------------------------------------------------------
with aba_auditoria:
    st.markdown("### 📋 Histórico de Auditoria")
    st.markdown("<p style='font-size:13px;color:#64748b;margin-top:-8px;'>Registro de laudos gerados/baixados pelos usuários:</p>", unsafe_allow_html=True)

    df_log = carregar_log_auditoria()

    if df_log.empty:
        st.info("Nenhum laudo gerado até o momento.")
    else:
        df_log_ord = df_log.sort_values("data_hora", ascending=False)
        st.dataframe(df_log_ord, use_container_width=True, hide_index=True)

        csv_bytes = df_log_ord.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Exportar histórico completo (CSV)",
            data=csv_bytes,
            file_name="historico_auditoria.csv",
            mime="text/csv",
            use_container_width=True
        )
