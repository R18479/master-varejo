# 📄 LAUDO COMPARTILHÁVEL AUTOMÁTICO EM PDF (CORRIGIDO)
def gerar_laudo_maquina():
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            
            # Ajuste correto do alinhamento usando alignment=1 (Centralizado) no ParagraphStyle
            estilo_t = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=22, textColor=colors.HexColor('#053c5e'), spaceAfter=12, alignment=1)
            estilo_s = ParagraphStyle('S', fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#666666'), spaceAfter=20, alignment=1)
            estilo_c = ParagraphStyle('C', fontName='Helvetica', fontSize=11, leading=16, spaceAfter=8)
            estilo_r = ParagraphStyle('R', fontName='Helvetica', fontSize=8, textColor=colors.HexColor('#888888'), alignment=1)
            
            story = [
                Paragraph("🔼 MASTER VAREJO", estilo_t),
                Paragraph("LAUDO AUTOMÁTICO DE AUDITORIA DE REDE", estilo_s),
                Spacer(1, 15),
                Paragraph(f"<b>Setor Mapeado por Varredura:</b> {categoria_detectada}", estilo_c),
                Paragraph(f"<b>Ponto Crítico de Redução de Perdas:</b> {pior_giro_geral} dias na filial {loja_gargalo_geral.title()}", estilo_c),
                Spacer(1, 10),
                Paragraph(f"<b>Plano de Ação Corretiva Gerado pela Máquina:</b>", estilo_c),
                Paragraph(f"<i>{acao_direta}</i>", estilo_c),
                Spacer(1, 40),
                Paragraph("Documento gerado 100% via processamento de máquina Master Varejo Ecosystem.", estilo_r)
    ]
    doc.build(story)  
    buffer.seek(0)
    return buffer.getvalue()

pdf_data = gerar_laudo_maquina()

st.download_button(
    label="📥 Baixar Laudo Oficial em PDF",
    data=pdf_data,
    file_name=f"Laudo_Automatico_{categoria_detectada}.pdf",
    mime="application/pdf"
