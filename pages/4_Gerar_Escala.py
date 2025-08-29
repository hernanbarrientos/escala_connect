import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from database import *
import style
from pdf_generator import gerar_pdf_escala

# --- CONFIGURAÇÃO DA PÁGINA E ESTILO ---
style.apply_style()
st.set_page_config(page_title="Gerar Escala", layout="wide")
st.title("🗓️ Gerador e Editor de Escalas Mensais")

try:
    calendar.setlocale(calendar.LC_ALL, 'pt_BR.UTF-8')
    meses_pt = {m: calendar.month_name[m].capitalize() for m in range(1, 13)}
except:
    meses_pt = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
                7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

hoje = datetime.now()
col1, col2, col_vazia = st.columns([1, 1, 4.1])
with col1:
    mes_selecionado_num = st.selectbox("Mês", options=list(meses_pt.keys()), format_func=lambda m: meses_pt[m], index=hoje.month - 1)
with col2:
    ano_selecionado = st.number_input("Ano", min_value=hoje.year, max_value=hoje.year + 5, value=hoje.year)

escala_completa_df = get_escala_completa(ano_selecionado, mes_selecionado_num)

# --- BOTÕES DE AÇÃO ---
col3, col4, col5 = st.columns(3)
with col3:
    if st.button("Criar Eventos do Mês", use_container_width=True):
        create_events_for_month(ano_selecionado, mes_selecionado_num)
        st.rerun()
with col4:
    if st.button("Preencher Automaticamente", type="primary", use_container_width=True):
        with st.spinner('Montando a escala, por favor aguarde...'):
            gerar_escala_automatica(ano_selecionado, mes_selecionado_num)
        st.rerun()
with col5:
    if not escala_completa_df.empty:
        mes_ano_formatado = f"{meses_pt.get(mes_selecionado_num, '')} de {ano_selecionado}"
        pdf_bytes = gerar_pdf_escala(escala_completa_df, mes_ano_formatado, view_all_servicos_fixos())
        st.download_button(
            label="📄 Baixar Escala em PDF",
            data=pdf_bytes,
            file_name=f"escala_connect_{ano_selecionado}_{mes_selecionado_num:02d}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

st.divider()
st.header(f"Escala Editável de {meses_pt.get(mes_selecionado_num, '')} de {ano_selecionado}")

# --- LÓGICA DE EXIBIÇÃO E EDIÇÃO ---
eventos_do_mes = get_events_for_month(ano_selecionado, mes_selecionado_num)
todas_funcoes = view_all_funcoes()

if eventos_do_mes.empty:
    st.info("Nenhum evento para este mês. Clique em 'Criar Eventos do Mês' para começar.")
else:
    todas_as_vagas = []
    todas_cotas = get_cotas_all_servicos()
    
    eventos_do_mes['Dia'] = pd.to_datetime(eventos_do_mes['data_evento']).dt.strftime('%d/%m') + " - " + eventos_do_mes['nome_servico']
    id_para_nome_funcao = todas_funcoes.set_index('id_funcao')['nome_funcao'].to_dict()

    for _, evento in eventos_do_mes.iterrows():
        cotas_do_servico = todas_cotas[todas_cotas['id_servico'] == evento['id_servico_fixo']]
        for _, cota in cotas_do_servico.iterrows():
            for i in range(1, cota['quantidade_necessaria'] + 1):
                nome_funcao = id_para_nome_funcao.get(cota['id_funcao'], '').replace('Líder de Escala', 'Líder')
                vaga_nome = f"{nome_funcao} {i}" if cota['quantidade_necessaria'] > 1 else nome_funcao
                todas_as_vagas.append({'Vaga': vaga_nome, 'Dia': evento['Dia']})
    
    if todas_as_vagas:
        grid_completo_df = pd.DataFrame(todas_as_vagas).drop_duplicates()
        tabela_para_exibir = grid_completo_df.pivot_table(index='Vaga', columns='Dia', aggfunc='size').notna()
        tabela_para_exibir[tabela_para_exibir == True] = '**VAGO**'
        tabela_para_exibir[tabela_para_exibir == False] = 'N/A'

        if not escala_completa_df.empty:
            df_preenchido = escala_completa_df.copy()
            df_preenchido['nome_funcao'] = df_preenchido['id_funcao'].map(id_para_nome_funcao).replace('Líder de Escala', 'Líder')
            
            def criar_nome_vaga_preenchido(row):
                cota_total = todas_cotas[todas_cotas['id_funcao'] == row['id_funcao']]['quantidade_necessaria'].max()
                if pd.notna(cota_total) and cota_total > 1:
                    return f"{row['nome_funcao']} {row['funcao_instancia']}"
                return str(row['nome_funcao'])
            
            df_preenchido['Vaga'] = df_preenchido.apply(criar_nome_vaga_preenchido, axis=1)
            df_preenchido['Dia'] = pd.to_datetime(df_preenchido['data_evento']).dt.strftime('%d/%m') + " - " + df_preenchido['nome_servico']
            
            tabela_dados_reais = df_preenchido.pivot_table(index='Vaga', columns='Dia', values='nome_voluntario', aggfunc='first')
            
            tabela_para_exibir.update(tabela_dados_reais)

        ordem_colunas = sorted(tabela_para_exibir.columns.tolist(), key=lambda d: datetime.strptime(d.split(' - ')[0], '%d/%m'))
        tabela_para_exibir = tabela_para_exibir.reindex(columns=ordem_colunas)
        ordem_prioridade_vagas = ["Líder", "Link", "Portão", "Store", "Igreja"]
        vagas_existentes = tabela_para_exibir.index.tolist()
        vagas_ordenadas = sorted(vagas_existentes, key=lambda v: (ordem_prioridade_vagas.index(v.split(' ')[0]) if v.split(' ')[0] in ordem_prioridade_vagas else 99, v))
        tabela_para_exibir = tabela_para_exibir.reindex(index=vagas_ordenadas)

        tabela_final = tabela_para_exibir.transpose()

        contagem_atual = escala_completa_df['nome_voluntario'].value_counts().to_dict()
        voluntarios_info_df = view_all_voluntarios(include_inactive=True)[['nome_voluntario', 'limite_escalas_mes']]
        limites_por_nome = pd.Series(voluntarios_info_df.limite_escalas_mes.values, index=voluntarios_info_df.nome_voluntario).to_dict()

        opcoes_por_funcao = {"**VAGO**": ["**VAGO**", "N/A"]}
        nome_simples_para_formatado = {'**VAGO**': '**VAGO**', 'N/A': 'N/A'}

        for _, funcao in todas_funcoes.iterrows():
            nome_funcao_base = funcao['nome_funcao'].replace('Líder de Escala', 'Líder')
            voluntarios_aptos = get_voluntarios_for_funcao(funcao['id_funcao'])
            
            opcoes_formatadas = ["**VAGO**", "N/A"]
            for _, voluntario in voluntarios_aptos.iterrows():
                nome = voluntario['nome_voluntario']
                contagem = contagem_atual.get(nome, 0)
                limite = limites_por_nome.get(nome, '?')
                nome_formatado = f"{nome} ({contagem}/{limite})"
                opcoes_formatadas.append(nome_formatado)
                nome_simples_para_formatado[nome] = nome_formatado
            
            opcoes_por_funcao[nome_funcao_base] = sorted(list(set(opcoes_formatadas)))

        tabela_final_formatada = tabela_final.replace(nome_simples_para_formatado)

        configuracao_colunas = {}
        for coluna in tabela_final_formatada.columns:
            funcao_base = ''.join(filter(lambda x: not x.isdigit(), coluna)).strip()
            if funcao_base in opcoes_por_funcao:
                configuracao_colunas[coluna] = st.column_config.SelectboxColumn(
                    label=coluna, options=opcoes_por_funcao[funcao_base], required=True
                )
        
        st.info("Clique duas vezes em uma célula para editar. As alterações são salvas automaticamente.")
        
        if 'escala_antiga' not in st.session_state or not st.session_state.escala_antiga.equals(tabela_final_formatada):
            st.session_state.escala_antiga = tabela_final_formatada.copy()
        
        escala_editada = st.data_editor(
            tabela_final_formatada, 
            column_config=configuracao_colunas, 
            use_container_width=True, 
            key="editor_escala"
        )

        if not escala_editada.equals(st.session_state.escala_antiga):
            try:
                diferencas = st.session_state.escala_antiga.compare(escala_editada)
                
                for indice, linha in diferencas.iterrows():
                    data_str, servico_str = indice.split(' - ')
                    data_evento_obj = datetime.strptime(f"{data_str}/{ano_selecionado}", "%d/%m/%Y").date()
                    id_evento = eventos_do_mes[(eventos_do_mes['data_evento'] == data_evento_obj) & (eventos_do_mes['nome_servico'] == servico_str)]['id_evento'].iloc[0]

                    for col_funcao in linha.dropna().index.get_level_values(0).unique():
                        valor_novo = escala_editada.loc[indice, col_funcao]
                        if valor_novo == "N/A": continue
                        
                        nome_real_voluntario = valor_novo.split(' (')[0].strip()
                        funcao_base = ''.join(filter(lambda x: not x.isdigit(), col_funcao)).strip()
                        instancia = int(''.join(filter(str.isdigit, col_funcao)) or 1)
                        
                        id_funcao = todas_funcoes[todas_funcoes['nome_funcao'].replace('Líder de Escala', 'Líder') == funcao_base]['id_funcao'].iloc[0]
                        id_novo_voluntario = get_voluntario_by_name(nome_real_voluntario)
                        update_escala_entry(id_evento, id_funcao, id_novo_voluntario, instancia)
                
                st.session_state.escala_antiga = escala_editada.copy()
                st.toast("Alteração salva!", icon="✅")
                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar: {e}")