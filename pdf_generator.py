import io
import pandas as pd
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def gerar_pdf_escala(escala_df, mes_ano_str):
    """
    VERSÃO CORRIGIDA: Gera um PDF da escala com layout de cartões, 
    garantindo que a altura do cartão seja sempre calculada corretamente 
    com base no número de linhas a serem desenhadas.
    """
    buffer = io.BytesIO()
    largura_pagina, altura_pagina_a4 = landscape(A4)
    largura_pagina_nova = largura_pagina + 0.6 * cm
    altura_pagina_total = 25 * cm 
    c = canvas.Canvas(buffer, pagesize=(largura_pagina_nova, altura_pagina_total))
    
    # Título Principal
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(largura_pagina / 2.0, altura_pagina_total - 1.5 * cm, f"Escala Connect - {mes_ano_str}")

    # Prepara os dados
    escala_df['nome_funcao'] = escala_df['nome_funcao'].replace('Líder de Escala', 'Líder')
    ordem_funcoes_principais = ["Líder", "Store", "Portão", "Link", "Igreja"]
    ordem_funcoes_completa = ordem_funcoes_principais + ["Apoio"]
    
    escala_df['data_obj'] = pd.to_datetime(escala_df['data_evento'])

    # --- LÓGICA DE LAYOUT DINÂMICO E CORRIGIDO ---
    
    # 1. Descobre e ordena os serviços únicos
    ordem_servicos = ["Domingo Manhã", "Domingo Noite", "Quinta-feira"]
    servicos_na_escala = escala_df['nome_servico'].unique()
    servicos_unicos_ordenados = sorted(
        servicos_na_escala,
        key=lambda s: ordem_servicos.index(s) if s in ordem_servicos else 99
    )

    y_cursor = altura_pagina_total - 2.5 * cm
    margem_entre_fileiras = 0.8 * cm

    # 3. Itera sobre cada serviço (cada fileira de cartões)
    for nome_servico in servicos_unicos_ordenados:
        escala_servico = escala_df[escala_df['nome_servico'] == nome_servico]
        if escala_servico.empty:
            continue

        eventos_unicos = sorted(escala_servico['data_obj'].unique())
        
        largura_cartao = 5.2 * cm
        margem_horizontal = 0.5 * cm
        
        # --- CORREÇÃO PRINCIPAL INICIA AQUI ---
        # Antes de desenhar, calcula a altura máxima da fileira com base no número de LINHAS, não de voluntários
        max_altura_na_fileira = 0
        for data_evento in eventos_unicos:
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            
            # Conta o número de voluntários de apoio para este dia
            num_apoios = len(escala_dia[escala_dia['nome_funcao'] == 'Apoio'])
            
            # O total de linhas a serem desenhadas é o número de funções principais + o número de apoios
            total_linhas_desenhadas = len(ordem_funcoes_principais) + num_apoios
            
            altura_base_header = 1.5 * cm 
            altura_por_linha = 0.5 * cm
            altura_cartao_calculada = altura_base_header + (total_linhas_desenhadas * altura_por_linha)
            
            if altura_cartao_calculada > max_altura_na_fileira:
                max_altura_na_fileira = altura_cartao_calculada
        # --- FIM DA CORREÇÃO PRINCIPAL ---

        # Agora desenha todos os cartões da fileira, todos com a mesma altura máxima calculada
        for i, data_evento in enumerate(eventos_unicos):
            escala_dia = escala_servico[escala_servico['data_obj'] == data_evento]
            
            # Prepara o conteúdo a ser desenhado
            linhas_para_desenhar = []
            
            # Primeiro, adiciona as funções principais, preenchendo com "---" se estiver vago
            for funcao in ordem_funcoes_principais:
                voluntario = escala_dia[escala_dia['nome_funcao'] == funcao]
                nome_voluntario = voluntario['nome_voluntario'].iloc[0] if not voluntario.empty else "---"
                linhas_para_desenhar.append((f"{funcao.upper()}:", nome_voluntario))
            
            # Depois, adiciona todos os voluntários de Apoio
            apoios_escalados = sorted(escala_dia[escala_dia['nome_funcao'] == 'Apoio']['nome_voluntario'].tolist())
            for nome_apoio in apoios_escalados:
                linhas_para_desenhar.append(("APOIO:", nome_apoio))
            
            x_cartao = 1.5 * cm + i * (largura_cartao + margem_horizontal)
            y_cartao = y_cursor - max_altura_na_fileira

            # Desenha o retângulo do cartão
            c.roundRect(x_cartao, y_cartao, largura_cartao, max_altura_na_fileira, 5, stroke=1, fill=0)
            
            # Cabeçalho do cartão
            y_topo_cartao = y_cartao + max_altura_na_fileira
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x_cartao + 0.3 * cm, y_topo_cartao - 0.8 * cm, nome_servico)
            c.drawRightString(x_cartao + largura_cartao - 0.3 * cm, y_topo_cartao - 0.8 * cm, data_evento.strftime('%d'))
            c.line(x_cartao, y_topo_cartao - 1.1 * cm, x_cartao + largura_cartao, y_topo_cartao - 1.1 * cm)

            # Desenha a lista de voluntários
            y_texto_inicial = y_topo_cartao - 1.2 * cm
            for j, (funcao_label, nome_vol) in enumerate(linhas_para_desenhar):
                y_pos = y_texto_inicial - ((j + 1) * altura_por_linha)
                
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x_cartao + 0.3 * cm, y_pos, funcao_label)
                c.setFont("Helvetica", 9)
                c.drawString(x_cartao + 1.8 * cm, y_pos, nome_vol)

        # Move o cursor para a próxima fileira de cartões
        y_cursor -= (max_altura_na_fileira + margem_entre_fileiras)

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer