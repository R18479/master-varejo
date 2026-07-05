import io
import re
import unicodedata
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def gerar_laudo_maquina(loja, categoria, giro, valor, plano_acao):
    """
    Gera um laudo de auditoria de maquina em PDF usando ReportLab.
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
    
    # Custom styles to avoid conflicts
    title_style = ParagraphStyle(
        'LaudoTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#0f172a'),
        alignment=1, # Center
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'LaudoSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1, # Center
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'LaudoSection',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=12,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'LaudoBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )
    
    body_bold_style = ParagraphStyle(
        'LaudoBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    # 1. Header
    story.append(Paragraph("🔼 MASTER VAREJO - LAUDO DE AUDITORIA", title_style))
    story.append(Paragraph("Relatório gerencial gerado automaticamente pelo AIA Core Engine", subtitle_style))
    story.append(Spacer(1, 10))
    
    # 2. Table of details
    valor_fmt = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if isinstance(valor, (int, float)) else str(valor)
    
    table_data = [
        [Paragraph("<b>Indicador de Controle</b>", body_bold_style), Paragraph("<b>Valor Registrado</b>", body_bold_style)],
        [Paragraph("Unidade Monitorada (Loja):", body_style), Paragraph(str(loja), body_style)],
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
    
    # 3. Action Plan section
    story.append(Paragraph("🎯 Plano de Ação AIA Recomendado", section_style))
    
    if giro > 90:
        bg_color_hex = '#fee2e2'      # Light Red
        border_color_hex = '#ef4444'  # Red
        text_color_hex = '#991b1b'    # Dark Red
    elif giro > 45:
        bg_color_hex = '#fef3c7'      # Light Amber
        border_color_hex = '#f59e0b'  # Amber
        text_color_hex = '#92400e'    # Dark Amber
    else:
        bg_color_hex = '#d1fae5'      # Light Green
        border_color_hex = '#10b981'  # Green
        text_color_hex = '#065f46'    # Dark Green
        
    plano_text_style = ParagraphStyle(
        'PlanoTextStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
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
    
    # 4. Global Fixed Escape Block
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
    
    # 5. Footer notes
    footer_style = ParagraphStyle(
        'LaudoFooter',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1
    )
    story.append(Paragraph("Este documento é um relatório gerencial confidencial para monitoramento interno de giros de estoque.", footer_style))
    story.append(Paragraph("Gerado de acordo com as regras de negócios da Rede de Lojas do Master Varejo.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# Configuração da página otimizada para dispositivos móveis
st.set_page_config(
    page_title="Master Varejo — Powered by AIA",
    page_icon="🔼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para emular visual mobile premium e botões grandes de fácil toque
st.markdown("""
    <style>
    /* Remove controles padrão do Streamlit para manter visual clean */
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Configuração geral de container mobile */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 480px !important;
        margin: 0 auto !important;
    }
    
    /* Cabeçalho Fixo Escuro com Logo e Borda de Destaque */
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
    .header-logo span {
        color: #3b82f6;
    }
    .header-subtitle {
        font-size: 10px;
        color: #94a3b8;
        font-weight: 700;
        letter-spacing: 0.25em;
        margin: 6px 0 0 0;
        text-transform: uppercase;
    }
    
    /* Estilização para st.text_area */
    textarea {
        border-radius: 12px !important;
        border: 1px solid #cbd5e1 !important;
        background-color: #f8fafc !important;
        font-size: 14px !important;
    }
    
    /* Botões de Categorias (Grade Touch) */
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
    
    /* Estilo para categoria ativa */
    .active-btn {
        background-color: #2563eb !important;
        color: white !important;
        border-bottom-color: #1d4ed8 !important;
    }
    
    /* Cartões de Insights */
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
    
    /* Alertas e Banners compactos */
    .stAlert {
        border-radius: 14px !important;
        padding: 14px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Cabeçalho Fixo com Logo do Master
st.markdown("""
    <div class="header-container">
        <div class="header-logo"><span>🔼</span> MASTER VAREJO</div>
        <div class="header-subtitle">Powered by AIA Core Engine</div>
    </div>
""", unsafe_allow_html=True)

# Definições de Domínio do Varejo
LOJAS_MONITORADAS = ["SOCORRO", "SÃO JOSÉ", "EMBU", "ELIANA", "JOÃO DIAS", "ARICANDUVA", "ALVARENGA", "SABARÁ"]

CATEGORIAS_OPERACIONAIS = [
    "AÇOUGUE", "BAZAR", "CESTAS", "CONGELADOS", "FLV", "FRIOS E EMBUTIDOS", "IOGURTE",
    "LATICÍNIOS", "LATICÍNIOS COMMODITIES", "LEITE COMMODITIES", "LIMPEZA", "LÍQUIDA",
    "LÍQUIDA QUENTE", "PADARIA", "PEIXARIA", "PERFUMARIA", "SECA COMMODITIES",
    "SECA DOCE", "SECA SALGADA", "TABACARIA", "VESTCASA"
]

# Função determinística estável para simular dados realistas por Loja + Categoria
def obter_dados_loja_categoria(loja, categoria):
    # Remover acentuação e padronizar
    loja_norm = ''.join(c for c in unicodedata.normalize('NFD', loja.upper()) if unicodedata.category(c) != 'Mn')
    cat_norm = ''.join(c for c in unicodedata.normalize('NFD', categoria.upper()) if unicodedata.category(c) != 'Mn')
    
    # 1. Casos de homologação reais da rede
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
        
    # 2. Hash determinístico para outras combinações de forma a manter dados estáveis
    combinado = loja_norm + cat_norm
    hash_val = 0
    for char in combinado:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
    hash_val = abs(hash_val)
    
    # Giro simulado entre 12 e 115 dias
    giro = 12 + (hash_val % 104)
    # Valor imobilizado realista entre R$ 15.000 e R$ 950.000
    valor = 15000.0 + (hash_val % 78) * 12000.0
    
    return giro, valor, False

# Input principal de dados colados pelo usuário (Regex)
st.markdown("### 📋 Copiar e Colar do Dashboard")
raw_data_input = st.text_area(
    label="Insira dados de texto bruto do seu painel aqui para análise regex instantânea:",
    placeholder="Exemplo de colar: O setor de LIMPEZA registrou 91 dias em São José no valor imobilizado de R$ 1.899.003.",
    height=90,
    help="O app usa expressões regulares para extrair Loja, Giro e Valor do texto e selecionar automaticamente!"
)

# Inicializar estados de sessão para Loja e Categoria ativa se não existirem
if "loja_ativa" not in st.session_state:
    st.session_state.loja_ativa = "JOÃO DIAS"
if "categoria_ativa" not in st.session_state:
    st.session_state.categoria_ativa = "BAZAR"

# 1. Processar texto colado se houver conteúdo e atualizar estados dinamicamente
if raw_data_input.strip():
    texto_analise = raw_data_input.upper()
    
    # Procurar loja no texto
    for loja in LOJAS_MONITORADAS:
        loja_norm = ''.join(c for c in unicodedata.normalize('NFD', loja.upper()) if unicodedata.category(c) != 'Mn')
        # Limpa acentuação comum
        loja_clean = re.sub(r'[ÃÕÁÉÍÓÚ]', '.', loja)
        if re.search(loja_clean, texto_analise) or loja_norm in texto_analise:
            st.session_state.loja_ativa = loja
            break
            
    # Procurar categoria no texto
    for cat in CATEGORIAS_OPERACIONAIS:
        cat_norm = ''.join(c for c in unicodedata.normalize('NFD', cat.upper()) if unicodedata.category(c) != 'Mn')
        if cat in texto_analise or cat_norm in texto_analise:
            st.session_state.categoria_ativa = cat
            break

# Seletor de Loja Monitorada
st.markdown("### 🏬 Selecione a Loja Monitorada")
st.markdown("<p style='font-size: 13px; color: #64748b; margin-top: -8px; margin-bottom: 12px;'>Escolha a unidade física para auditar suas respectivas categorias:</p>", unsafe_allow_html=True)

cols_lojas = st.columns(4)
for idx, loja in enumerate(LOJAS_MONITORADAS):
    col_idx = idx % 4
    # Contar categorias críticas dessa loja para colocar um indicador numérico
    criticas_count = 0
    atencao_count = 0
    for c in CATEGORIAS_OPERACIONAIS:
        g, _, _ = obter_dados_loja_categoria(loja, c)
        if g > 90:
            criticas_count += 1
        elif g > 45:
            atencao_count += 1
            
    # Rótulo do botão com indicador de criticidade
    marcador = "🔴" if criticas_count > 0 else ("🟡" if atencao_count > 0 else "🟢")
    label_loja = f"{marcador} {loja}"
    
    # Destacar se estiver ativa
    if st.session_state.loja_ativa == loja:
        label_loja = f"👉 {loja.upper()}"
        
    if cols_lojas[col_idx].button(label_loja, key=f"btn_loja_{loja}"):
        st.session_state.loja_ativa = loja
        st.rerun()

# 2. Categorias da Loja Selecionada separadas por criticidade de Giro
loja_atual = st.session_state.loja_ativa
st.markdown(f"### 🗂️ Categorias em **{loja_atual}**")
st.markdown("<p style='font-size: 13px; color: #64748b; margin-top: -8px; margin-bottom: 12px;'>Toque em qualquer categoria para disparar o plano de ação correspondente:</p>", unsafe_allow_html=True)

# Agrupar categorias por status de giro para a loja atual
criticas_list = []
atencao_list = []
estaveis_list = []

for cat in CATEGORIAS_OPERACIONAIS:
    giro, valor, _ = obter_dados_loja_categoria(loja_atual, cat)
    if giro > 90:
        criticas_list.append((cat, giro, valor))
    elif giro > 45:
        atencao_list.append((cat, giro, valor))
    else:
        estaveis_list.append((cat, giro, valor))

# Renderizar seções organizadas
def render_categoria_botoes(lista_categorias, tag_cor, emoji):
    if not lista_categorias:
        st.markdown(f"<p style='font-size: 12px; color: #94a3b8; font-style: italic;'>Nenhuma categoria encontrada.</p>", unsafe_allow_html=True)
        return
        
    cols = st.columns(2)
    for idx, (cat, giro, valor) in enumerate(lista_categorias):
        col_idx = idx % 2
        # Formatar indicador compacto
        label = f"{emoji} {cat} ({giro}d)"
        if st.session_state.categoria_ativa == cat:
            label = f"🔥 {cat.upper()}"
            
        if cols[col_idx].button(label, key=f"btn_cat_{loja_atual}_{cat}"):
            st.session_state.categoria_ativa = cat
            st.rerun()

# Expanders de status para facilitar navegação em tela mobile
with st.expander(f"🔴 GIRO CRÍTICO (>90 dias) — {len(criticas_list)} Categorias", expanded=True):
    render_categoria_botoes(criticas_list, "red", "🚨")

with st.expander(f"🟡 EM ATENÇÃO (45-90 dias) — {len(atencao_list)} Categorias", expanded=False):
    render_categoria_botoes(atencao_list, "amber", "⚠️")

with st.expander(f"🟢 GIRO CONTROLADO (<45 dias) — {len(estaveis_list)} Categorias", expanded=False):
    render_categoria_botoes(estaveis_list, "emerald", "✅")


# Exibir o Painel de Auditoria se houver uma categoria ativa
if st.session_state.categoria_ativa:
    cat_atual = st.session_state.categoria_ativa
    giro_det, valor_det, is_real = obter_dados_loja_categoria(loja_atual, cat_atual)
    
    # Sobrescrever caso o Regex tenha extraído dados customizados do texto
    metodo_obtencao = "Dados Oficiais / Simulação Integrada"
    if is_real:
        metodo_obtencao = "Dados de Homologação da Rede"
        
    if raw_data_input.strip():
        # Se houver texto e a categoria ativa for mencionada no texto, usar os dados do Regex
        texto_analise = raw_data_input.upper()
        if cat_atual in texto_analise or ''.join(c for c in unicodedata.normalize('NFD', cat_atual.upper()) if unicodedata.category(c) != 'Mn') in texto_analise:
            regex_giro = re.search(r'(\d+)\s*(?:DIAS|DIA|G)', texto_analise)
            if regex_giro:
                giro_det = int(regex_giro.group(1))
                metodo_obtencao = "Extraído via Expressão Regular (Regex)"
            
            regex_valor = re.search(r'(?:R\$|RS)\s*([\d\.,\s]+)', texto_analise)
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
    
    # A. Bloco de Escape Fixo (Métricas permanentes do painel de controle)
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
    
    # B. Bloco de Giro Parado (Métricas dinâmicas do gargalo detectado)
    st.markdown(f"""
        <div class="insight-card">
            <div class="card-title">⏳ Gargalo de Giro Parado</div>
            <div style="margin-top: 4px;">
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #e2e8f0;">
                    <span style="font-size: 13px; color: #475569;">Unidade Crítica:</span>
                    <strong style="font-size: 13px; color: #0f172a;">{loja_atual}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px dashed #e2e8f0;">
                    <span style="font-size: 13px; color: #475569;">Dias de Cobertura:</span>
                    <strong style="font-size: 13px; color: #0f172a;">{giro_det} dias</strong>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 6px 0;">
                    <span style="font-size: 13px; color: #475569;">Valor Imobilizado:</span>
                    <strong style="font-size: 14px; color: #10b981;">{valor_formatado}</strong>
                </div>
            </div>
            <div style="font-size: 9px; color: #94a3b8; text-align: right; margin-top: 10px; font-style: italic;">
                Método: {metodo_obtencao}
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # C. Bloco de Ação Corretiva Dinâmica (Decisão baseada nos dias de giro do gargalo)
    st.markdown("<p style='font-size: 12px; font-weight: 800; color: #334155; margin-top: 16px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em;'>🎯 Plano de Ação AIA Recomendado</p>", unsafe_allow_html=True)
    
    if giro_det > 90:
        recomendacao_texto = f"🚨 Risco Crítico de Vencimento! Realizar saldão ou transferência urgente da categoria {cat_atual} na unidade {loja_atual} para conter perdas financeiras."
        st.error(recomendacao_texto)
    elif giro_det > 45:
        recomendacao_texto = f"⚠️ Atenção na Cobertura! Frear novos pedidos automáticos da categoria {cat_atual} para a unidade {loja_atual} para estabilização do giro."
        st.warning(recomendacao_texto)
    else:
        recomendacao_texto = f"✅ Operação estável e cobertura controlada para {cat_atual} na loja {loja_atual}."
        st.success(recomendacao_texto)

    # Geração do laudo em PDF usando ReportLab
    try:
        pdf_laudo = gerar_laudo_maquina(loja_atual, cat_atual, giro_det, valor_det, recomendacao_texto)
        st.download_button(
            label="📥 Baixar Laudo de Auditoria (PDF)",
            data=pdf_laudo,
            file_name=f"Laudo_Auditoria_{loja_atual.replace(' ', '_')}_{cat_atual.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="btn_download_pdf"
        )
    except Exception as e:
        st.error(f"Erro ao gerar o PDF: {e}")


    # Exibir banco de dados de homologação num expansor legal
    with st.expander("📊 Ver Dados de Homologação de Referência"):
        dados_referencia = pd.DataFrame([
            {"Categoria": "BAZAR", "Loja": "JOÃO DIAS", "Giro (Dias)": "205 d", "Capital Imobilizado": "R$ 787.171"},
            {"Categoria": "PERFUMARIA", "Loja": "ALVARENGA", "Giro (Dias)": "148 d", "Capital Imobilizado": "R$ 433.521"},
            {"Categoria": "LIMPEZA", "Loja": "SÃO JOSÉ", "Giro (Dias)": "91 d", "Capital Imobilizado": "R$ 1.899.003"},
            {"Categoria": "SECA SALGADA", "Loja": "SOCORRO", "Giro (Dias)": "95 d", "Capital Imobilizado": "R$ 1.401.360"},
            {"Categoria": "PEIXARIA", "Loja": "JOÃO DIAS", "Giro (Dias)": "117 d", "Capital Imobilizado": "R$ 43.769"}
        ])
        st.dataframe(dados_referencia, hide_index=True, use_container_width=True)
