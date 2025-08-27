import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from database import * # Importa tudo para simplificar
import style
from pdf_generator import gerar_pdf_escala

# Aplica o estilo e a sidebar
style.apply_style()

st.set_page_config(page_title="Gerar Escala", layout="wide")
st.title("🗓️ Gerador e Editor de Escalas Mensais")

# --- SELEÇÃO DE MÊS E ANO E BOTÕES DE AÇÃO ---
hoje = datetime.now()
try:
    calendar.setlocale(calendar.LC_ALL, 'pt_BR.UTF-8')
    meses_pt = {m: calendar.month_name[m].capitalize() for m in range(1, 13)}
except:
    meses_pt = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
                7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

# --- Fileira 1: Seletores de Data ---
col1, col2, col_vazia = st.columns([1, 1, 4.1]) # 1 parte para o Mês, 4 partes de espaço vazio
with col1:
    mes_selecionado_num = st.selectbox(
        "Mês", 
        options=list(meses_pt.keys()), 
        format_func=lambda m: meses_pt[m], 
        index=hoje.month - 1
    )
with col2:
    ano_selecionado = st.number_input(
        "Ano", 
        min_value=hoje.year, 
        max_value=hoje.year + 5, 
        value=hoje.year
    )

# --- Fileira 2: Botões de Ação ---
col3, col4, col5 = st.columns(3)
with col3:
    if st.button("Criar Eventos do Mês", use_container_width=True):
        create_events_for_month(ano_selecionado, mes_selecionado_num)
        st.rerun()
with col4:
    if st.button("Preencher Automaticamente", type="primary", use_container_width=True):
        gerar_escala_automatica(ano_selecionado, mes_selecionado_num)
        st.rerun()
with col5:
    escala_completa_df_pdf = get_escala_completa(ano_selecionado, mes_selecionado_num)
    if not escala_completa_df_pdf.empty:
        mes_ano_formatado = f"{meses_pt.get(mes_selecionado_num, '')} de {ano_selecionado}"
        pdf_bytes = gerar_pdf_escala(escala_completa_df_pdf, mes_ano_formatado)
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
escala_df = get_escala_completa(ano_selecionado, mes_selecionado_num)
eventos_do_mes = get_events_for_month(ano_selecionado, mes_selecionado_num)
todas_funcoes = view_all_funcoes()

if eventos_do_mes.empty:
    st.info("Nenhum evento para este mês. Clique em 'Criar Eventos do Mês' para começar.")
else:
    # --- PREPARAÇÃO DA TABELA PARA EXIBIÇÃO ---
    tabela_para_exibir = pd.DataFrame() # Começa vazia
    
    if not escala_df.empty:
        escala_df['data_evento'] = pd.to_datetime(escala_df['data_evento'])
        
        todas_cotas = get_cotas_all_servicos()
        funcoes_com_cota_maior_que_um = todas_cotas[todas_cotas['quantidade_necessaria'] > 1]['id_funcao'].unique()
        
        def criar_nome_vaga(row):
            if row['id_funcao'] in funcoes_com_cota_maior_que_um:
                return f"{row['nome_funcao']} {row['funcao_instancia']}"
            return row['nome_funcao']
        
        escala_df['Vaga'] = escala_df.apply(criar_nome_vaga, axis=1)
        escala_df['Dia'] = escala_df['data_evento'].dt.strftime('%d/%m') + " - " + escala_df['nome_servico']
                
        tabela_para_exibir = escala_df.pivot_table(index='Vaga', columns='Dia', values='nome_voluntario', aggfunc='first').fillna("**VAGO**")
        
        ordem_colunas = sorted(escala_df['Dia'].unique(), key=lambda d: datetime.strptime(d.split(' - ')[0], '%d/%m'))
        tabela_para_exibir = tabela_para_exibir[ordem_colunas]
        
        ordem_prioridade = ["Líder de Escala", "Link", "Portão", "Store", "Igreja"]
        todas_vagas_ordenadas = []
        funcoes_unicas = escala_df[['nome_funcao']].drop_duplicates()
        
        for f in ordem_prioridade:
            if f in funcoes_unicas['nome_funcao'].values:
                max_cota = escala_df[escala_df['nome_funcao'] == f]['funcao_instancia'].max()
                if max_cota == 1:
                    todas_vagas_ordenadas.append(f)
                else:
                    for i in range(1, int(max_cota) + 1):
                        todas_vagas_ordenadas.append(f"{f} {i}")

        if 'Apoio' in funcoes_unicas['nome_funcao'].values:
            max_apoios = escala_df[escala_df['nome_funcao'] == 'Apoio']['funcao_instancia'].max()
            if pd.notna(max_apoios):
                for i in range(1, int(max_apoios) + 1):
                    todas_vagas_ordenadas.append(f"Apoio {i}")
                
        tabela_para_exibir = tabela_para_exibir.reindex(todas_vagas_ordenadas).dropna(how='all')

    # Transpõe a tabela para o layout final (Datas nas Linhas)
    tabela_final = tabela_para_exibir.transpose()

    # --- CONFIGURAÇÃO DO st.data_editor ---
    opcoes_por_funcao = {"**VAGO**": ["**VAGO**"]}
    for _, funcao in todas_funcoes.iterrows():
        voluntarios_aptos = get_voluntarios_for_funcao(funcao['id_funcao'])
        opcoes_por_funcao[funcao['nome_funcao']] = ["**VAGO**"] + sorted(voluntarios_aptos['nome_voluntario'].tolist())

    configuracao_colunas = {}
    for coluna in tabela_final.columns:
        funcao_base = ''.join(filter(lambda x: not x.isdigit(), coluna)).strip()
        if funcao_base in opcoes_por_funcao:
            configuracao_colunas[coluna] = st.column_config.SelectboxColumn(
                label=coluna, options=opcoes_por_funcao[funcao_base], required=True
            )
    
    st.info("Clique duas vezes em uma célula para editar o voluntário. As alterações são salvas automaticamente.")
    
    if 'escala_antiga' not in st.session_state or not st.session_state.escala_antiga.index.equals(tabela_final.index) or not st.session_state.escala_antiga.columns.equals(tabela_final.columns):
        st.session_state.escala_antiga = tabela_final.copy()
    
    escala_editada = st.data_editor(
        tabela_final, 
        column_config=configuracao_colunas, 
        use_container_width=True, 
        key="editor_escala"
    )

    # --- LÓGICA PARA DETECTAR E SALVAR MUDANÇAS ---
    if not escala_editada.equals(st.session_state.escala_antiga):
        try:
            diferencas = st.session_state.escala_antiga.compare(escala_editada)
            
            for indice, linha in diferencas.iterrows():
                data_str, servico_str = indice.split(' - ')
                data_evento_obj = datetime.strptime(f"{data_str}/{ano_selecionado}", "%d/%m/%Y").date()
                id_evento = eventos_do_mes[eventos_do_mes['data_evento'] == data_evento_obj]['id_evento'].iloc[0]

                for col_funcao in linha.dropna().index.get_level_values(0).unique():
                    valor_novo = escala_editada.loc[indice, col_funcao]
                    funcao_base = ''.join(filter(lambda x: not x.isdigit(), col_funcao)).strip()
                    instancia = int(''.join(filter(str.isdigit, col_funcao)) or 1)
                    id_funcao = todas_funcoes[todas_funcoes['nome_funcao'] == funcao_base]['id_funcao'].iloc[0]
                    id_novo_voluntario = get_voluntario_by_name(valor_novo)
                    update_escala_entry(id_evento, id_funcao, id_novo_voluntario, instancia)
            
            st.session_state.escala_antiga = escala_editada.copy()
            st.toast("Alteração salva!", icon="✅")
            st.rerun()
        except Exception as e:
            st.error(f"Ocorreu um erro ao salvar: {e}")

st.divider()
# st.header("📄 Exportar Escala")

# escala_completa_df = get_escala_completa(ano_selecionado, mes_selecionado_num)

# if not escala_completa_df.empty:
#     # O botão para GERAR o PDF fica dentro do form
#     with st.form("form_pdf"):
#         submitted = st.form_submit_button("Gerar PDF para Impressão", use_container_width=True, type="primary")
#         if submitted:
#             with st.spinner("Criando PDF..."):
#                 mes_ano_formatado = f"{meses_pt.get(mes_selecionado_num, '')} de {ano_selecionado}"
#                 # Guarda os bytes do PDF no session_state
#                 st.session_state.pdf_bytes = gerar_pdf_escala(escala_completa_df, mes_ano_formatado)
    
#     # O botão para BAIXAR o PDF fica FORA do form
#     if 'pdf_bytes' in st.session_state and st.session_state.pdf_bytes:
#         st.download_button(
#             label="✅ PDF Pronto! Clique aqui para baixar.",
#             data=st.session_state.pdf_bytes,
#             file_name=f"escala_connect_{ano_selecionado}_{mes_selecionado_num:02d}.pdf",
#             mime="application/pdf",
#             use_container_width=True
#         )
# else:
#     st.info("Gere e/ou preencha uma escala primeiro para poder exportar.")