import io
import pandas as pd
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm

def gerar_pdf_escala(escala_df, mes_ano_str, servicos_df):
    """
    VERSÃO FINAL: Gera um PDF de PÁGINA ÚNICA com altura dinâmica e
    ordenação de serviços customizada (Domingo Manhã > Domingo Noite > Outros dias).
    """
    buffer = io.BytesIO()
    
    largura_pagina, _ = landscape(A4)

    if escala_df.empty:
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        c.setTitle(f"Escala Connect - {mes_ano_str}")
        c.setFont("Helvetica", 12)
        c.drawCentredString(largura_pagina / 2.0, 10*cm, "Nenhuma escala para gerar.")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer

    escala_df['nome_funcao'] = escala_df['nome_funcao'].replace('Líder de Escala', 'Líder')
    escala_df['data_obj'] = pd.to_datetime(escala_df['data_evento'])

    ordem_preferencial = ["Líder", "Store", "Portão", "Link", "Igreja"]
    funcoes_principais_em_uso = escala_df[escala_df['nome_funcao'] != 'Apoio']['nome_funcao'].unique().tolist()
    funcoes_a_exibir = [f for f in ordem_preferencial if f in funcoes_principais_em_uso]

    margem_x = 1.5 * cm
    margem_y_superior = 2.5 * cm
    margem_y_inferior = 1.5 * cm
    espacamento_entre_fileiras_y = 1 * cm
    altura_por_linha_funcao = 0.5 * cm
    altura_base_header = 1.5 * cm 

    # --- LÓGICA DE ORDENAÇÃO CUSTOMIZADA ---
    # Define a ordem de prioridade explícita que você pediu
    ordem_prioridade_servicos = ["Domingo Manhã", "Domingo Noite"]
    
    dia_da_semana_map = pd.Series(servicos_df.dia_da_semana.values, index=servicos_df.nome_servico).to_dict()
    servicos_na_escala = escala_df['nome_servico'].unique()
    
    # Nova chave de ordenação com dupla prioridade
    servicos_unicos_ordenados = sorted(servicos_na_escala, key=lambda s: (
        ordem_prioridade_servicos.index(s) if s in ordem_prioridade_servicos else 99,
        dia_da_semana_map.get(s, 99)
    ))

    # O resto do código continua exatamente o mesmo
    altura_total_necessaria = margem_y_superior + margem_y_inferior

    for i, nome_servico in enumerate(servicos_unicos_ordenados):
        escala_servico = escala_df[escala_df['nome_servico'] == nome_servico]
        eventos_do_servico = sorted(escala_servico['data_obj'].unique())
        
        if not eventos_do_servico:
            continue

        max_altura_nesta_fileira = 0
        for data_evento in eventos_do_servico:
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            num_apoios = len(escala_dia[escala_dia['nome_funcao'] == 'Apoio'])
            total_linhas_desenhadas = len(funcoes_a_exibir) + num_apoios
            altura_cartao_calculada = altura_base_header + (total_linhas_desenhadas * altura_por_linha_funcao)
            if altura_cartao_calculada > max_altura_nesta_fileira:
                max_altura_nesta_fileira = altura_cartao_calculada
        
        altura_total_necessaria += max_altura_nesta_fileira
        if i < len(servicos_unicos_ordenados) - 1:
            altura_total_necessaria += espacamento_entre_fileiras_y

    c = canvas.Canvas(buffer, pagesize=(largura_pagina, altura_total_necessaria))
    c.setTitle(f"Escala Connect - {mes_ano_str}")
    
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(largura_pagina / 2.0, altura_total_necessaria - 1.5 * cm, f"Escala Connect - {mes_ano_str}")
    
    y_cursor = altura_total_necessaria - margem_y_superior

    for nome_servico in servicos_unicos_ordenados:
        escala_servico = escala_df[escala_df['nome_servico'] == nome_servico]
        eventos_do_servico = sorted(escala_servico['data_obj'].unique())
        
        num_eventos = len(eventos_do_servico)
        if num_eventos == 0:
            continue

        espacamento_total_x = (num_eventos - 1) * 0.5 * cm
        largura_disponivel = largura_pagina - (2 * margem_x) - espacamento_total_x
        largura_cartao = largura_disponivel / num_eventos

        max_altura_nesta_fileira = 0
        for data_evento in eventos_do_servico:
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            num_apoios = len(escala_dia[escala_dia['nome_funcao'] == 'Apoio'])
            total_linhas_desenhadas = len(funcoes_a_exibir) + num_apoios
            altura_cartao_calculada = altura_base_header + (total_linhas_desenhadas * altura_por_linha_funcao)
            if altura_cartao_calculada > max_altura_nesta_fileira:
                max_altura_nesta_fileira = altura_cartao_calculada
        
        for i, data_evento in enumerate(eventos_do_servico):
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            
            linhas_card = []
            for funcao_nome in funcoes_a_exibir:
                voluntarios = escala_dia[escala_dia['nome_funcao'] == funcao_nome]['nome_voluntario'].tolist()
                nome = voluntarios[0] if voluntarios else "---"
                linhas_card.append((f"{funcao_nome.upper()}:", nome))
            
            apoios_escalados = sorted(escala_dia[escala_dia['nome_funcao'] == 'Apoio']['nome_voluntario'].tolist())
            for nome_apoio in apoios_escalados:
                linhas_card.append(("APOIO:", nome_apoio))

            x_atual = margem_x + i * (largura_cartao + 0.5 * cm)
            y_atual = y_cursor - max_altura_nesta_fileira
            
            c.roundRect(x_atual, y_atual, largura_cartao, max_altura_nesta_fileira, 5, stroke=1, fill=0)
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_atual + 0.3 * cm, y_atual + max_altura_nesta_fileira - 0.8 * cm, nome_servico)
            c.drawRightString(x_atual + largura_cartao - 0.3 * cm, y_atual + max_altura_nesta_fileira - 0.8 * cm, data_evento.strftime('%d'))
            c.line(x_atual, y_atual + max_altura_nesta_fileira - 1.1 * cm, x_atual + largura_cartao, y_atual + max_altura_nesta_fileira - 1.1 * cm)

            y_texto_inicial = y_atual + max_altura_nesta_fileira - 1.2 * cm
            for j, (funcao_label, nome_vol) in enumerate(linhas_card):
                y_pos = y_texto_inicial - ((j + 1) * altura_por_linha_funcao)
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x_atual + 0.3 * cm, y_pos, funcao_label)
                c.setFont("Helvetica", 9)
                c.drawString(x_atual + 1.8 * cm, y_pos, nome_vol)
        
        y_cursor -= (max_altura_nesta_fileira + espacamento_entre_fileiras_y)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer