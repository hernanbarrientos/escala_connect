import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from database import *
import style
from pdf_generator import gerar_pdf_escala
from collections import defaultdict

# --- Verificação de Login no topo da página ---
if not st.session_state.get('logged_in'):
    st.error("Acesso negado. Por favor, faça o login primeiro.")
    st.stop()

# Aplica o estilo global e a configuração da página
style.apply_style()
st.set_page_config(page_title="Gerar Escala", layout="wide")

# Pega dados do usuário logado
id_ministerio_logado = st.session_state['id_ministerio_logado']
todos_ministerios_df = get_all_ministerios()
nome_ministerio = todos_ministerios_df[todos_ministerios_df['id_ministerio'] == id_ministerio_logado]['nome_ministerio'].iloc[0]

st.title(f"🗓️ Escalas do Ministério {nome_ministerio}")

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

# << ALTERADO: Busca a escala filtrando pelo ministério
escala_completa_df = get_escala_completa(ano_selecionado, mes_selecionado_num, id_ministerio_logado)

# --- BOTÕES DE AÇÃO ---
col3, col4, col5 = st.columns(3)
with col3:
    if st.button("Criar Eventos do Mês", use_container_width=True):
        # << ALTERADO: Passa o id_ministerio_logado
        create_events_for_month(ano_selecionado, mes_selecionado_num, id_ministerio_logado)
        st.rerun()
with col4:
    if st.button("Preencher Automaticamente", type="primary", use_container_width=True):
        with st.spinner('Montando a escala, por favor aguarde...'):
            # << ALTERADO: Passa o id_ministerio_logado
            gerar_escala_automatica(ano_selecionado, mes_selecionado_num, id_ministerio_logado)
        st.rerun()
with col5:
    if not escala_completa_df.empty:
        mes_ano_formatado = f"{meses_pt.get(mes_selecionado_num, '')} de {ano_selecionado}"
        # << ALTERADO: Passa o id_ministerio_logado
        pdf_bytes = gerar_pdf_escala(escala_completa_df, mes_ano_formatado, view_all_servicos_fixos(id_ministerio_logado))
        st.download_button(
            label="📄 Baixar Escala em PDF",
            data=pdf_bytes,
            file_name=f"escala_connect_{ano_selecionado}_{mes_selecionado_num:02d}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

st.divider()
st.header(f"Escala Editável de {meses_pt.get(mes_selecionado_num, '')}")

# << ALTERADO: Todas as buscas de dados agora filtram pelo ministério
voluntarios_info_unificado_df = get_all_voluntarios_com_detalhes(id_ministerio_logado)
eventos_do_mes = get_events_for_month(ano_selecionado, mes_selecionado_num, id_ministerio_logado)
todas_funcoes = view_all_funcoes(id_ministerio_logado)

if eventos_do_mes.empty:
    st.info("Nenhum evento para este mês. Clique em 'Criar Eventos do Mês' para começar.")
else:
    # --- Lógica de montagem da tabela (sem alterações na lógica interna, mas agora usa dados filtrados) ---
    todas_as_vagas = []
    todas_cotas = get_cotas_all_servicos()
    eventos_do_mes['Dia'] = pd.to_datetime(eventos_do_mes['data_evento']).dt.strftime('%d/%m') + " - " + eventos_do_mes['nome_servico']
    id_para_nome_funcao = todas_funcoes.set_index('id_funcao')['nome_funcao'].to_dict()
    for _, evento in eventos_do_mes.iterrows():
        cotas_do_servico = todas_cotas[todas_cotas['id_servico'] == evento['id_servico_fixo']]
        for _, cota in cotas_do_servico.iterrows():
            # Apenas cria vagas para funções que existem no ministério atual
            if cota['id_funcao'] in id_para_nome_funcao:
                for i in range(1, cota['quantidade_necessaria'] + 1):
                    nome_funcao = id_para_nome_funcao.get(cota['id_funcao'], '').replace('Líder de Escala', 'Líder')
                    vaga_nome = f"{nome_funcao} {i}"
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
                return f"{row['nome_funcao']} {row['funcao_instancia']}"
            df_preenchido['Vaga'] = df_preenchido.apply(criar_nome_vaga_preenchido, axis=1)
            df_preenchido['Dia'] = pd.to_datetime(df_preenchido['data_evento']).dt.strftime('%d/%m') + " - " + df_preenchido['nome_servico']
            tabela_dados_reais = df_preenchido.pivot_table(index='Vaga', columns='Dia', values='nome_voluntario', aggfunc='first')
            tabela_para_exibir.update(tabela_dados_reais)
        
        # O resto da montagem da tabela continua como antes, mas agora com dados já filtrados
        ordem_colunas = sorted(tabela_para_exibir.columns.tolist(), key=lambda d: datetime.strptime(d.split(' - ')[0], '%d/%m'))
        tabela_para_exibir = tabela_para_exibir.reindex(columns=ordem_colunas)
        ordem_prioridade_vagas = ["Líder", "Link", "Portão", "Store", "Igreja", "Apoio"]
        vagas_existentes = tabela_para_exibir.index.tolist()
        vagas_ordenadas = sorted(vagas_existentes, key=lambda v: (ordem_prioridade_vagas.index(v.split(' ')[0]) if v.split(' ')[0] in ordem_prioridade_vagas else 99, v))
        tabela_para_exibir = tabela_para_exibir.reindex(index=vagas_ordenadas)
        tabela_final = tabela_para_exibir.transpose()
        contagem_atual = escala_completa_df['nome_voluntario'].value_counts().to_dict()
        limites_por_nome = pd.Series(voluntarios_info_unificado_df.limite_escalas_mes.values, index=voluntarios_info_unificado_df.nome_voluntario).to_dict()
        opcoes_por_funcao = {"**VAGO**": ["**VAGO**", "N/A"]}
        nome_simples_para_formatado = {'**VAGO**': '**VAGO**', 'N/A': 'N/A'}
        for _, funcao in todas_funcoes.iterrows():
            nome_funcao_base = funcao['nome_funcao'].replace('Líder de Escala', 'Líder')
            id_funcao_atual = funcao['id_funcao']
            df_filtrado = voluntarios_info_unificado_df.dropna(subset=['funcoes'])
            voluntarios_aptos = df_filtrado[df_filtrado['funcoes'].apply(lambda funcoes_lista: id_funcao_atual in funcoes_lista)]
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

        with st.form(key="edit_escala_form"):
            st.info("Clique duas vezes em uma célula para editar. As alterações só serão salvas ao clicar no botão 'Salvar Alterações'.")
            escala_editada = st.data_editor(
                tabela_final_formatada, 
                column_config=configuracao_colunas, 
                use_container_width=True, 
                key="editor_escala"
            )
            submitted = st.form_submit_button("✅ Salvar Alterações")

        if submitted:
            try:
                diferencas = tabela_final_formatada.compare(escala_editada)
                if diferencas.empty:
                    st.toast("Nenhuma alteração foi feita.", icon="🤷")
                else:
                    changes_made = 0
                    for indice, linha in diferencas.iterrows():
                        data_str, servico_str = indice.split(' - ')
                        data_evento_obj = datetime.strptime(f"{data_str}/{ano_selecionado}", "%d/%m/%Y").date()
                        evento_filtrado = eventos_do_mes[(eventos_do_mes['data_evento'] == data_evento_obj) & (eventos_do_mes['nome_servico'] == servico_str)]
                        if evento_filtrado.empty: continue
                        id_evento = evento_filtrado['id_evento'].iloc[0]
                        for col_funcao in linha.dropna().index.get_level_values(0).unique():
                            changes_made += 1
                            valor_novo = escala_editada.loc[indice, col_funcao]
                            if valor_novo == "N/A": continue
                            nome_real_voluntario = valor_novo.split(' (')[0].strip()
                            funcao_base = ''.join(filter(lambda x: not x.isdigit(), col_funcao)).strip()
                            instancia = int(''.join(filter(str.isdigit, col_funcao)) or 1)
                            id_funcao = todas_funcoes[todas_funcoes['nome_funcao'].replace('Líder de Escala', 'Líder') == funcao_base]['id_funcao'].iloc[0]
                            id_novo_voluntario = get_voluntario_by_name(nome_real_voluntario)
                            update_escala_entry(
                                id_evento=int(id_evento), 
                                id_funcao=int(id_funcao), 
                                id_voluntario=id_novo_voluntario,
                                instancia=int(instancia)
                            )
                    st.toast(f"{changes_made} alteração(ões) salva(s)!", icon="✅")
                    st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao salvar: {e}")