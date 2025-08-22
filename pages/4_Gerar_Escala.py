import streamlit as st
import pandas as pd
from datetime import datetime # LINHA ADICIONADA
from database import (
    create_events_for_month, get_events_for_month, 
    view_all_funcoes, get_escala_completa
)

st.set_page_config(page_title="Gerar Escala", layout="wide")
st.title("🗓️ Gerador de Escalas Mensais")

# --- SELEÇÃO DE MÊS E ANO ---
hoje = datetime.now()
# Nomes dos meses em português
meses_pt = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 
            7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

col1, col2, col3 = st.columns(3)
with col1:
    mes_selecionado_nome = st.selectbox("Mês", options=list(meses_pt.values()), index=hoje.month - 1)
    # Converte o nome do mês de volta para número
    mes_selecionado_num = list(meses_pt.keys())[list(meses_pt.values()).index(mes_selecionado_nome)]

with col2:
    ano_selecionado = st.number_input("Ano", min_value=hoje.year - 1, max_value=hoje.year + 5, value=hoje.year)

with col3:
    st.write("") # Espaçador
    st.write("") # Espaçador
    if st.button("Gerar Esqueleto da Escala para o Mês"):
        create_events_for_month(ano_selecionado, mes_selecionado_num)
        st.rerun()

st.divider()

# --- VISUALIZAÇÃO DA ESCALA ---
st.header(f"Escala de {mes_selecionado_nome} de {ano_selecionado}")

eventos_do_mes = get_events_for_month(ano_selecionado, mes_selecionado_num)
escala_do_mes = get_escala_completa(ano_selecionado, mes_selecionado_num)
todas_funcoes = view_all_funcoes()

if eventos_do_mes.empty:
    st.info("Nenhum evento encontrado para este mês. Clique no botão acima para gerar o esqueleto da escala.")
else:
    for _, evento in eventos_do_mes.iterrows():
        # Corrigindo a formatação do dia da semana para Português
        dias_semana_pt = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_semana_num = evento['data_evento'].weekday()
        dia_semana_nome = dias_semana_pt[dia_semana_num]
        data_formatada = evento['data_evento'].strftime('%d/%m/%Y')
        
        st.subheader(f"📅 {evento['nome_servico']} - {data_formatada} ({dia_semana_nome})")
        
        col_funcao, col_voluntario = st.columns(2)

        with col_funcao:
            st.markdown("**Função**")
        with col_voluntario:
            st.markdown("**Voluntário Escalado**")

        for _, funcao in todas_funcoes.iterrows():
            escala_especifica = escala_do_mes[
                (escala_do_mes['id_evento'] == evento['id_evento']) & 
                (escala_do_mes['id_funcao'] == funcao['id_funcao'])
            ]
            nome_voluntario = escala_especifica['nome_voluntario'].iloc[0] if not escala_especifica.empty else "---"
            
            with col_funcao:
                st.write(funcao['nome_funcao'])
            with col_voluntario:
                st.selectbox(
                    f"sel_{evento['id_evento']}_{funcao['id_funcao']}",
                    options=["---"] + ["Em breve..."],
                    label_visibility="collapsed"
                )
        st.write("---")