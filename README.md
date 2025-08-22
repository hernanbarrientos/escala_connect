# 🚀 Gerador de Escalas - Ministério CONNECT

Aplicação web desenvolvida em Python com Streamlit para automatizar e gerenciar a criação de escalas mensais para os voluntários do ministério CONNECT.

## ✨ Visão Geral

Este projeto nasceu da necessidade de organizar de forma eficiente a escala de voluntários, levando em conta as habilidades individuais, a disponibilidade padrão e os limites de participação de cada membro da equipe. A aplicação permite um cadastro detalhado e, futuramente, a geração automática de uma sugestão de escala, otimizando o tempo dos líderes.

## 📋 Funcionalidades Implementadas

* **🏠 Interface Multi-Página:** Navegação clara e organizada com páginas dedicadas para cada funcionalidade.
* **👤 Gerenciamento de Voluntários:**
    * Cadastro e edição completos (CRUD) de voluntários.
    * Definição de limite de escalas por mês para cada voluntário.
    * Status de "Ativo" e "Inativo".
    * Opção para marcar um voluntário como indisponível para o mês atual (férias/folga).
* **🛠️ Gerenciamento de Funções:**
    * Cadastro e edição de todas as funções/cargos necessários na escala (ex: Líder, Apoio, Store).
* **🗓️ Gerenciamento de Serviços Fixos:**
    * Cadastro dos cultos e eventos que ocorrem semanalmente (ex: Culto de Domingo - Manhã).
* **🔗 Associações Inteligentes:**
    * Atribuição de múltiplas funções que cada voluntário está apto a exercer.
    * Definição da disponibilidade padrão de cada voluntário para os serviços fixos.
* **📅 Geração de Esqueleto da Escala:**
    * Seleção de mês/ano e geração automática de todos os eventos (datas e cultos) que necessitam de uma escala.
    * Visualização da escala do mês com as vagas a serem preenchidas.

## 💻 Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Framework Web:** Streamlit
* **Banco de Dados:** PostgreSQL
* **Bibliotecas Principais:**
    * `pandas`
    * `psycopg2-binary`

## ⚙️ Como Rodar o Projeto Localmente

Siga os passos abaixo para configurar e executar a aplicação no seu ambiente de desenvolvimento.

### Pré-requisitos

* [Python 3.9+](https://www.python.org/downloads/)
* [Git](https://git-scm.com/)
* Uma instância de banco de dados PostgreSQL acessível (local ou na nuvem, como o [Supabase](https://supabase.com/)).

### Passos para Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO_NO_GITHUB]
    ```

2.  **Acesse a pasta do projeto:**
    ```bash
    cd nome-da-pasta-do-projeto
    ```

3.  **Crie e ative um ambiente virtual (Recomendado):**
    ```bash
    # Criar o ambiente
    python -m venv venv

    # Ativar no Windows
    .\venv\Scripts\activate

    # Ativar no Mac/Linux
    source venv/bin/activate
    ```

4.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure suas credenciais de banco de dados:**
    * Na raiz do projeto, crie a pasta `.streamlit`.
    * Dentro dela, crie um arquivo chamado `secrets.toml`.
    * Copie e cole o conteúdo abaixo no arquivo, substituindo com suas credenciais reais:
        ```toml
        [postgres]
        host = "SEU_HOST_AQUI"
        port = 5432
        dbname = "SEU_DBNAME_AQUI"
        user = "SEU_USER_AQUI"
        password = "SUA_SENHA_AQUI"
        ```

6.  **Crie as tabelas no banco de dados:**
    * Execute os scripts SQL que desenvolvemos para criar todas as tabelas: `funcoes`, `voluntarios`, `servicos_fixos`, `voluntario_funcoes`, `voluntario_disponibilidade`, `voluntario_indisponibilidade`, `eventos` e `escala`.

7.  **Execute a aplicação:**
    ```bash
    streamlit run 0_Home.py
    ```

8.  Abra seu navegador no endereço `http://localhost:8501`.

## 🔮 Próximos Passos

O projeto está em desenvolvimento. As próximas grandes funcionalidades a serem implementadas são:
* [ ] Implementar o algoritmo de **preenchimento automático** da escala.
* [ ] Permitir a **edição manual** e trocas de voluntários na escala gerada.
* [ ] Implementar a funcionalidade de **exportar a escala em PDF**.

## 👤 Autor

* **Hernán Barrientos**
* **LinkedIn:** [[Hernán Barrientos]](https://www.linkedin.com/in/hernanesbarrientos/)
