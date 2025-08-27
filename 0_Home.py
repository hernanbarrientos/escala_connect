import streamlit as st
import style

# Aplica o estilo customizado da sidebar
style.apply_style()

st.set_page_config(
    page_title="Home - Escala CONNECT",
    layout="wide"
)

st.title("Bem-vindo ao Sistema de Escalas CONNECT! 👋")

st.markdown("Este é o seu portal para gerenciar e automatizar as escalas dos voluntários do ministério.")
st.divider()

st.header("Como Começar (Passo a Passo)")
st.info("Para gerar sua primeira escala, siga esta ordem de configuração para garantir que o algoritmo tenha todas as informações necessárias.")

st.markdown(
    """
    #### 1️⃣ **Cadastre as Funções**
    * No menu ao lado, vá para a página **`Gerenciar Funções`**.
    * Crie todos os cargos que os voluntários podem ocupar (ex: `Líder de Escala`, `Apoio`, `Store`, `Portão`).

    ---

    #### 2️⃣ **Cadastre os Serviços e as Vagas**
    * Acesse **`Gerenciar Serviços`**.
    * Adicione os cultos ou eventos que acontecem toda semana (ex: `Domingo Manhã`, `Quinta-Feira`).
    * Para cada serviço que você criar, **expanda-o** e defina o **número de vagas (`cotas`)** para cada função. *Este passo é crucial para o gerador saber quantas pessoas escalar!*

    ---

    #### 3️⃣ **Cadastre os Voluntários**
    * Vá para **`Gerenciar Voluntários`**.
    * Na aba "Cadastrar", adicione cada membro da equipe. Para cada um, você já pode definir:
        * As **funções que ele pode exercer**.
        * A **disponibilidade padrão** (para quais serviços ele está disponível).

    ---

    #### 4️⃣ **(Opcional) Crie Vínculos**
    * Se houver voluntários que precisam servir juntos (casais, famílias, etc.), vá para **`Gerenciar Vínculos`** para criar os grupos.
    * Lembre-se que o sistema só permite criar um grupo se os membros tiverem pelo menos um dia de disponibilidade em comum.

    ---

    #### 5️⃣ **Gere a Escala!**
    * Com tudo configurado, acesse **`Gerar Escala`**.
    * Selecione o mês e ano desejados.
    * Clique em **"Criar Eventos do Mês"** para montar o esqueleto da escala.
    * Em seguida, clique em **"Preencher Automaticamente"** para que o algoritmo faça a mágica!
    * Você pode então editar manualmente qualquer vaga, clicando duas vezes na célula desejada.

    """
)