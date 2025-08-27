import io
import pandas as pd
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def gerar_pdf_escala(escala_df, mes_ano_str):
    """
    VERSÃO FINAL: Gera um arquivo PDF da escala com layout de cartões, 
    com o nome do serviço DENTRO de cada cartão e espaçamento vertical correto.
    """
    buffer = io.BytesIO()
    largura_pagina, altura_pagina_a4 = landscape(A4)
    # Aumentamos a altura da página para garantir que tudo caiba confortavelmente
    largura_pagina_nova = largura_pagina + 0.6*cm # Adiciona 0.5cm de largura
    altura_pagina_total = 23 * cm 
    c = canvas.Canvas(buffer, pagesize=(largura_pagina_nova, altura_pagina_total))
    
    # Título Principal do Documento
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(largura_pagina / 2.0, altura_pagina_total - 1.5*cm, f"Escala Connect - {mes_ano_str}")

    # Prepara os dados
    escala_df['nome_funcao'] = escala_df['nome_funcao'].replace('Líder de Escala', 'Líder')
    ordem_funcoes = ["Líder", "Store", "Portão", "Link", "Igreja", "Apoio"]
    escala_df['data_obj'] = pd.to_datetime(escala_df['data_evento'])

    # --- LÓGICA DE LAYOUT DINÂMICO E CORRIGIDO ---
    
    # 1. Descobre quais serviços únicos existem na escala deste mês e os ordena
    ordem_servicos = ["Domingo Manhã", "Domingo Noite", "Quinta-Feira"]
    servicos_na_escala = escala_df['nome_servico'].unique()
    servicos_unicos_ordenados = sorted(
        servicos_na_escala,
        key=lambda s: ordem_servicos.index(s) if s in ordem_servicos else 99
    )

    # 2. Inicia um "cursor" de desenho no topo da página
    y_cursor = altura_pagina_total - 2*cm
    margem_entre_fileiras = 0.8* cm

    # 3. Itera sobre os serviços que encontrou
    for nome_servico in servicos_unicos_ordenados:
        escala_servico = escala_df[escala_df['nome_servico'] == nome_servico]
        if escala_servico.empty:
            continue

        eventos_unicos = sorted(escala_servico['data_obj'].unique())
        
        largura_cartao = 5.2 * cm
        margem_horizontal = 0.5 * cm
        
        # Antes de desenhar, calcula a altura máxima que os cartões desta fileira terão
        max_altura_na_fileira = 0
        for data_evento in eventos_unicos:
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            num_voluntarios_no_dia = len(escala_dia)
            altura_base_header = 1.5 * cm 
            altura_por_linha = 0.5 * cm
            altura_cartao_calculada = altura_base_header + (num_voluntarios_no_dia * altura_por_linha)
            if altura_cartao_calculada > max_altura_na_fileira:
                max_altura_na_fileira = altura_cartao_calculada
        
        # Agora desenha todos os cartões da fileira
        for i, data_evento in enumerate(eventos_unicos):
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            
            linhas_para_desenhar = []
            apoios_escalados = sorted(escala_dia[escala_dia['nome_funcao'] == 'Apoio']['nome_voluntario'].tolist())
            
            for funcao in ordem_funcoes:
                if funcao == "Apoio":
                    for nome_apoio in apoios_escalados:
                        linhas_para_desenhar.append(("APOIO:", nome_apoio))
                else:
                    voluntario = escala_dia[escala_dia['nome_funcao'] == funcao]
                    nome_voluntario = voluntario['nome_voluntario'].iloc[0] if not voluntario.empty else "---"
                    linhas_para_desenhar.append((f"{funcao.upper()}:", nome_voluntario))
            
            x_cartao = 1.5*cm + i * (largura_cartao + margem_horizontal)
            y_cartao = y_cursor - max_altura_na_fileira

            c.roundRect(x_cartao, y_cartao, largura_cartao, max_altura_na_fileira, 5, stroke=1, fill=0)
            
            # --- CABEÇALHO CORRIGIDO, DENTRO DO CARTÃO ---
            y_topo_cartao = y_cartao + max_altura_na_fileira
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_cartao + 0.3*cm, y_topo_cartao - 0.8*cm, nome_servico)
            c.drawRightString(x_cartao + largura_cartao - 0.3*cm, y_topo_cartao - 0.8*cm, data_evento.strftime('%d'))
            c.line(x_cartao, y_topo_cartao - 1.1*cm, x_cartao + largura_cartao, y_topo_cartao - 1.1*cm)

            # Lista de voluntários
            y_texto_inicial = y_topo_cartao - 1.2*cm
            for j, (funcao_label, nome_vol) in enumerate(linhas_para_desenhar):
                y_pos = y_texto_inicial - ( (j + 1) * altura_por_linha )
                
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x_cartao + 0.3*cm, y_pos, funcao_label)
                c.setFont("Helvetica", 9)
                c.drawString(x_cartao + 1.8*cm, y_pos, nome_vol)

        # 4. Move o cursor para baixo para a próxima fileira, garantindo o espaçamento
        y_cursor -= (max_altura_na_fileira + margem_entre_fileiras)

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer