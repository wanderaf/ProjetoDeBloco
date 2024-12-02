import streamlit as st
from pymongo import MongoClient
import pandas as pd
from wordcloud import WordCloud
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
import subprocess
import sys
import io
import requests
from fastapi import FastAPI, HTTPException, Query
from model_utils import fetch_units, predict_totals_by_procedure
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import os
import matplotlib.pyplot as plt

# Suprimir mensagens de depuração do PyTorch
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

# URL base da API FastAPI
API_URL = "http://127.0.0.1:8000"

# Função para conectar ao MongoDB e buscar os dados de análise
@st.cache_data(show_spinner=False)
def fetch_all_data():
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]
    
    # Obter todos os documentos da collection SIA_ANALISE
    data = list(collection_sia_analise.find({}, {"_id": 0}))
    
    client.close()
    
    return data

# Função para converter os dados em um DataFrame do pandas
def convert_to_dataframe(data):
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame()  # Retorna DataFrame vazio se não houver dados


# Página Data Summary Report
def data_summary_report_page():
    # Introdução
    st.title("Data Summary Report")
    st.write("""
    Este relatório resume os dados utilizados no projeto de visualização de dados de saúde baseado no FTP do SUS. O projeto visa 
    auxiliar gestores públicos na elaboração de políticas de saúde e ajudar os usuários a identificar onde buscar atendimento. 
    Os dados são oriundos do FTP do SUS, sendo visualizados e analisados por meio de uma aplicação desenvolvida em Streamlit.
    """)

    # Descrição dos Dados
    st.header("2. Descrição dos Dados")
    st.write("""
    - **Fonte dos Dados**: FTP do SUS – [ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/)
    - **Coleta de Dados**: A coleta dos dados foi feita a partir dos arquivos disponibilizados no FTP do SUS e incluídos em um banco de dados MongoDB, 
      contendo informações de procedimentos e serviços de saúde prestados.
    - **Objetivo dos Dados**: O conjunto de dados contém informações sobre a produção de serviços de saúde, tais como:
      - Unidade de Saúde (campo FANTASIA)
      - Período de Movimentação (campo PA_MVMR, no formato AAAAMM)
      - Procedimentos realizados (campo PA_PROC_ID)
      - Quantidade de produção apresentada e aprovada (campos PROD_APRESENTADA e PROD_APROVADA)
    """)

    # Carregar os dados do MongoDB
    data = fetch_all_data()
    df = convert_to_dataframe(data)

    if not df.empty:
        # Características dos Dados
        st.header("3. Características dos Dados")

        # Tamanho do conjunto de dados
        st.subheader("Tamanho do Conjunto de Dados")
        st.write(f"Número de registros: {len(df)}")
        st.write(f"Número de colunas: {len(df.columns)}")

        # Variáveis principais e tipos
        st.subheader("Variáveis Principais e Tipos")
        st.write("""
        - **FANTASIA**: Nome da unidade de saúde, utilizado como filtro principal. (Tipo: Texto)
        - **PA_MVMR**: Período de movimentação dos dados no formato AAAAMM, utilizado para busca por ano. (Tipo: Numérico)
        - **PA_PROC_ID**: Identificação dos procedimentos realizados na unidade de saúde. (Tipo: Texto ou Numérico)
        - **PROD_APRESENTADA**: Quantidade de produção apresentada por procedimento. (Tipo: Numérico)
        - **PROD_APROVADA**: Quantidade de produção aprovada por procedimento. (Tipo: Numérico)
        """)

        # Estatísticas descritivas
        st.header("Estatísticas Descritivas")
        st.write("Aqui estão as principais estatísticas dos dados numéricos:")
        st.write(df.describe())
        
        # Visualizar os dados de produção apresentada e aprovada
        if "PROD_APRESENTADA" in df.columns and "PROD_APROVADA" in df.columns:
            st.header("Produção Apresentada e Aprovada")
            st.write("Distribuição da produção apresentada e aprovada:")
            st.line_chart(df[["PROD_APRESENTADA", "PROD_APROVADA"]])
        
        # Verificar valores nulos
        st.header("Verificação de Valores Faltantes")
        missing_values = df.isnull().sum()
        st.write(missing_values[missing_values > 0])
        
    else:
        st.warning("Nenhum dado disponível no banco de dados para gerar o resumo.")

# Função para carregar opções de filtro
@st.cache_data(show_spinner=False)
def fetch_filter_options():
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]
    fantasia_options = collection_sia_analise.distinct("FANTASIA")
    client.close()
    return fantasia_options

# Função para conectar ao MongoDB e buscar dados filtrados
def fetch_filtered_data_from_mongo(fantasia=None, ano=None):
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]
    
    # Criar filtro dinâmico
    query_filter = {}
    if fantasia:
        query_filter["FANTASIA"] = fantasia
    if ano:
        query_filter["PA_MVMR"] = {"$regex": f"^{ano}"}
    
    # Obter os documentos da collection SIA_ANALISE aplicando o filtro
    data = list(collection_sia_analise.find(query_filter, {"_id": 0}))
    
    client.close()
    
    return data

# Função para converter os dados em um DataFrame do pandas
def convert_to_dataframe(data):
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame()  # Retorna DataFrame vazio se não houver dados

# Função para converter DataFrame em CSV
def convert_df_to_csv(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

# Página de visualização de dados
def data_visualization_page():
    st.title("Visualização de Dados")
    
    # Obter opções de filtro
    fantasia_options = fetch_filter_options()
    st.sidebar.header("Filtros de Dados")
    selected_fantasia = st.sidebar.selectbox("Unidade de Saúde", options=fantasia_options, index=0, key="selected_fantasia")
    selected_ano = st.sidebar.text_input("Ano", value="2024", key="selected_ano")

    if st.button('Carregar Dados Filtrados', key="load_data_button"):
        data = fetch_filtered_data_from_mongo(fantasia=selected_fantasia, ano=selected_ano)

        # Verificar o tipo dos dados e tratar adequadamente
        if isinstance(data, list) and len(data) > 0:
            # Converter lista para DataFrame
            data = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame) and not data.empty:
            pass  # Data já é um DataFrame não vazio
        else:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
            return  # Encerrar execução da função se não houver dados

        st.success("Dados carregados com sucesso!")
        
        # Processar dados
        if "PA_MVMR" in data.columns:
            data['MÊS'] = data['PA_MVMR'].astype(str).apply(lambda x: x[-2:])  # Extrair mês do campo PA_MVMR
        else:
            st.error("A coluna 'PA_MVMR' não está disponível nos dados.")
            return

        if "TOTAL_PA_VALPRO" in data.columns and "TOTAL_PA_VALAPR" in data.columns:
            data['GLOSAS'] = data['TOTAL_PA_VALPRO'] - data['TOTAL_PA_VALAPR']
        else:
            st.error("As colunas 'TOTAL_PA_VALPRO' ou 'TOTAL_PA_VALAPR' não estão disponíveis nos dados.")
            return

        # Tabela resumo
        st.write("Resumo Estatístico:")
        st.dataframe(data.describe())

        # Gráfico 1: Valor Aprovado ao longo dos meses
        if 'MÊS' in data.columns and 'TOTAL_PA_VALAPR' in data.columns:
            st.subheader("Evolução do Valor Aprovado por Mês")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby('MÊS')['TOTAL_PA_VALAPR'].sum().plot(kind='area', ax=ax, alpha=0.7)
            ax.set_title("Valor Total Aprovado por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Valor Aprovado")
            st.pyplot(fig)

        # Gráfico 2: Quantidade de Glosas por Mês
        if 'MÊS' in data.columns and 'GLOSAS' in data.columns:
            st.subheader("Quantidade de Glosas por Mês")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby('MÊS')['GLOSAS'].sum().plot(kind='line', ax=ax, marker='o', color='red')
            ax.set_title("Quantidade de Glosas por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Quantidade de Glosas")
            st.pyplot(fig)

        # Gráfico 3: Principais Procedimentos com Glosas
        if 'IP_DSCR' in data.columns and 'GLOSAS' in data.columns:
            st.subheader("Principais Procedimentos com Glosas")
            glosas_por_procedimento = data.groupby('IP_DSCR')['GLOSAS'].sum().nlargest(10)
            fig, ax = plt.subplots(figsize=(10, 5))
            glosas_por_procedimento.plot(kind='bar', ax=ax, color='orange')
            ax.set_title("Top 10 Procedimentos com Maior Quantidade de Glosas")
            ax.set_xlabel("Código do Procedimento")
            ax.set_ylabel("Quantidade de Glosas")
            st.pyplot(fig)

        # Gráfico 4: Comparação entre Valores Produzidos e Aprovados
        if 'MÊS' in data.columns and 'TOTAL_PA_VALPRO' in data.columns and 'TOTAL_PA_VALAPR' in data.columns:
            st.subheader("Comparação entre Valores Produzidos e Aprovados")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby('MÊS')[['TOTAL_PA_VALPRO', 'TOTAL_PA_VALAPR']].sum().plot(kind='bar', ax=ax)
            ax.set_title("Valores Produzidos vs Aprovados por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Valores")
            st.pyplot(fig)

        # Botão para download do CSV
        csv_data = convert_df_to_csv(data)
        st.download_button(
            label="Baixar dados como CSV",
            data=csv_data,
            file_name='dados_filtrados.csv',
            mime='text/csv',
            key="download_button"
        )

# Página de introdução
def introduction_page():
    # Carregar a imagem do SUS
    st.image("docs/img/sus.webp", use_column_width=True)
    
    # Texto introdutório
    st.title("Bem-vindo ao Projeto de Visualização de Dados do SUS")
    st.write("""
    Este projeto utiliza dados oriundos do FTP do SUS e tem como objetivo auxiliar os gestores públicos na elaboração 
    de políticas públicas de saúde, bem como ajudar os usuários a identificar onde buscar atendimento. 
    Através dessa plataforma, é possível visualizar e analisar dados de saúde de forma acessível e interativa.
    """)

    # Seção de links úteis
    st.header("Links Úteis")
    st.markdown("""
    - [FTP do SUS (Dados)](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/): Local para busca dos dados.
    - [FTP do SUS (Manual)](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/): Local com informações técnicas dos arquivos utilizados.
    - [DATASUS](https://datasus.saude.gov.br/transferencia-de-arquivos/): Local para pesquisa dos dados sem necessidade de utilização do FTP.
    """)

# Função para executar o script noticias.py
def run_news_scraper():
    try:
        # Obter o caminho do Python atualmente em uso
        python_path = sys.executable
        
        # Executar noticias.py usando o mesmo Python
        subprocess.run([python_path, "noticias.py"], check=True, capture_output=True, text=True)
        st.success("Notícias atualizadas com sucesso!")
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao executar o script noticias.py: {e}")
        st.write(e.stderr)  # Exibir o erro detalhado

@st.cache_data
def load_news_data():
    # Carregar o arquivo CSV
    path = r'C:\Users\wande\OneDrive\INFNET\7. 6º Semestre\Projeto de Bloco\data\noticias.csv'
    df = pd.read_csv(path)
    return df

# Função para extrair o conteúdo de uma página de notícias
def extract_news_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrair o conteúdo do artigo de acordo com a estrutura do site
        paragraphs = soup.find_all('p')
        full_text = " ".join([para.get_text() for para in paragraphs])

        return full_text
    except Exception as e:
        st.error(f"Erro ao acessar a notícia: {e}")
        return ""

# Função para gerar a nuvem de palavras
def generate_wordcloud(text):
    stop_words = set(stopwords.words('portuguese'))  # Stopwords em português

    # Gerar a nuvem de palavras
    wordcloud = WordCloud(stopwords=stop_words, background_color="white", width=800, height=400).generate(text)

    # Exibir a nuvem de palavras
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    st.pyplot(plt)

# Página Últimas Notícias
def latest_news_page():
    st.title("Últimas Notícias")

    # Executar o script noticias.py para atualizar o arquivo CSV
    st.write("Atualizando as notícias...")
    run_news_scraper()  # Atualiza o arquivo noticias.csv com novas notícias

    # Carregar os dados de notícias
    df_news = load_news_data()

    # Extrair o conteúdo completo de todas as notícias
    all_news_text = ""
    st.write("Extraindo o conteúdo das notícias, por favor aguarde...")
    for i, row in df_news.iterrows():
        full_text = extract_news_content(row['Link'])
        all_news_text += full_text

    # Gerar e exibir a nuvem de palavras
    if all_news_text:
        st.subheader("Nuvem de Palavras das Notícias")
        generate_wordcloud(all_news_text)

    # Exibir a tabela com os títulos e links
    st.subheader("Tabela de Notícias")
    st.dataframe(df_news[['Título', 'Link']])


# Função para conectar ao MongoDB e buscar todos os procedimentos
@st.cache_data(show_spinner=False)
def fetch_all_procedures():
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    # Buscar todos os procedimentos com PA_PROC_ID e IP_DSCR
    procedures = list(collection_sia_analise.find({}, {"PA_PROC_ID": 1, "IP_DSCR": 1, "_id": 0}))
    
    client.close()

    # Criar uma lista de concatenações no formato 'PA_PROC_ID - IP_DSCR'
    procedure_list = [f"{proc['PA_PROC_ID']} - {proc['IP_DSCR']}" for proc in procedures if 'PA_PROC_ID' in proc and 'IP_DSCR' in proc]
    
    return procedure_list

# Função para buscar valores únicos de PA_PROC_ID - IP_DSCR
@st.cache_data(show_spinner=False)
def fetch_unique_procedures():
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    # Buscar procedimentos únicos
    procedures = list(collection_sia_analise.distinct("PA_PROC_ID"))
    descriptions = list(collection_sia_analise.distinct("IP_DSCR"))

    # Fazer a concatenação dos valores
    procedure_list = [f"{proc} - {desc}" for proc, desc in zip(procedures, descriptions) if proc and desc]

    # Retornar uma lista única e ordenada
    return sorted(list(set(procedure_list)))

# Função para buscar as unidades de saúde (CNES - FANTASIA) que possuem o procedimento e estão no município selecionado
def fetch_unidades_by_municipio_procedimento(cod_mun_selected, procedure_search):
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    # Converter cod_mun_selected para inteiro regular
    cod_mun_selected = int(cod_mun_selected)

    # Criar filtro dinâmico para buscar apenas os registros do município e do procedimento
    query_filter = {
        "PA_CODUNI": cod_mun_selected,
        "$or": [
            {"PA_PROC_ID": {"$regex": procedure_search.split(" - ")[0]}},  # Procura pelo ID do procedimento
            {"IP_DSCR": {"$regex": procedure_search.split(" - ")[1]}}      # Procura pela descrição do procedimento
        ]
    }

    # Trazer apenas o CNES e FANTASIA
    data = list(collection_sia_analise.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))

    client.close()
    return data

# Função para converter os dados em um DataFrame do pandas
def convert_to_dataframe(data):
    if data:
        return pd.DataFrame(data)
    else:
        return pd.DataFrame()  # Retorna DataFrame vazio se não houver dados

# Função para carregar o arquivo Excel de municípios carregado pelo usuário
def load_municipios_excel(file):
    df = pd.read_excel(file)

    # Converter a coluna COD_MUN para string
    df['COD_MUN'] = df['COD_MUN'].astype(str)

    return df

# Função para buscar CNES baseado no COD_MUN selecionado na coleção SIA_cadgerma
def fetch_cnes_by_municipio(cod_mun_selected):
    client = MongoClient("mongodb://localhost:27017/")
    db_sus = client["SUS"]
    collection_sia_cadgerma = db_sus["SIA_cadgerma"]

    # Converter cod_mun_selected para string
    cod_mun_selected_str = str(cod_mun_selected)

    # Criar filtro para buscar todos os CNES relacionados ao COD_MUN (município)
    query_filter = {"CODUFMUN": cod_mun_selected_str}

    # Buscar CNES da coleção SIA_cadgerma
    data = list(collection_sia_cadgerma.find(query_filter, {"CNES": 1, "_id": 0}))

    client.close()

    # Exibir os dados para depuração
    st.write(f"CNES encontrados para o município {cod_mun_selected_str}: {data}")

    # Retornar uma lista de CNES
    cnes_list = [str(item["CNES"]) for item in data]
    return cnes_list


# Função para buscar todas as unidades em SIA_ANALISE baseadas na lista de CNES
def fetch_unidades_by_cnes_list(cnes_list):
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    # Garantir que os CNES na lista sejam strings
    cnes_list_str = [str(cnes) for cnes in cnes_list]

    # Criar filtro para buscar todas as unidades (CNES - FANTASIA) na lista de CNES
    query_filter = {"PA_CODUNI": {"$in": cnes_list_str}}

    # Buscar os dados da coleção SIA_ANALISE (PA_CODUNI e FANTASIA)
    data = list(collection_sia_analise.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))

    client.close()

    # Exibir os dados para depuração
    st.write(f"Unidades encontradas na coleção SIA_ANALISE com CNES: {data}")

    return data


# Função para buscar todas as unidades de um município (CNES - FANTASIA)
def fetch_unidades_by_municipio(cod_mun_selected):
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    # Converter cod_mun_selected para inteiro regular
    cod_mun_selected = int(cod_mun_selected)

    # Criar filtro para buscar todas as unidades no município selecionado
    query_filter = {"PA_CODUNI": cod_mun_selected}

    # Trazer apenas o CNES e FANTASIA
    data = list(collection_sia_analise.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))

    client.close()
    return data

# Página de busca por município (sem procedimento)
def search_municipality_page():
    st.title("Busca por Município")

    # Carregar o arquivo de municípios
    uploaded_file = st.file_uploader("Carregar arquivo de Excel com Municípios", type=["xlsx"])

    if uploaded_file:
        # Carregar o Excel com municípios
        municipios_df = load_municipios_excel(uploaded_file)
        st.write("Arquivo de municípios carregado com sucesso.")
        st.dataframe(municipios_df)

        # Permitir que o usuário selecione o município
        selected_municipio = st.selectbox("Selecionar Município", municipios_df["Municipio"].unique())

        # Filtrar pelo código do município selecionado
        cod_mun_selected = municipios_df.loc[municipios_df["Municipio"] == selected_municipio, "COD_MUN"].values[0]
        st.write(f"Município selecionado: {selected_municipio} (Código: {cod_mun_selected})")

        # Botão para buscar todas as unidades no município
        if st.button('Buscar Todas as Unidades no Município'):
            # Buscar CNES associados ao município selecionado diretamente da coleção SIA_cadgerma
            cnes_list = fetch_all_cadgerma_by_municipio(cod_mun_selected)

            if cnes_list:
                st.write(f"CNES encontrados: {cnes_list}")

                # Buscar unidades (CNES - FANTASIA) na coleção SIA_ANALISE usando a lista de CNES
                data = fetch_unidades_by_cnes_list(cnes_list)

                if data:
                    st.success("Unidades encontradas!")
                    st.write(f"Número de unidades encontradas: {len(data)}")
                    
                    # Exibir os dados em formato de tabela (CNES - FANTASIA)
                    df = pd.DataFrame(data)
                    st.table(df[["PA_CODUNI", "FANTASIA"]])
                else:
                    st.warning("Nenhuma unidade encontrada para o município selecionado.")
            else:
                st.warning("Nenhum CNES encontrado para o município selecionado.")


# Função para buscar todos os dados de CODUFMUN e CNES diretamente na coleção SIA_cadgerma
def fetch_all_cadgerma_by_municipio(cod_mun_selected):
    client = MongoClient("mongodb://localhost:27017/")
    db_sus = client["SUS"]
    collection_sia_cadgerma = db_sus["SIA_cadgerma"]

    # Criar filtro para buscar todos os registros do COD_MUN na coleção SIA_cadgerma
    query_filter = {"CODUFMUN": int(cod_mun_selected)}

    # Buscar todos os dados relacionados ao município
    data = list(collection_sia_cadgerma.find(query_filter))

    client.close()

    # Exibir os dados completos para análise
    st.write(f"Dados completos de SIA_cadgerma para COD_MUN {cod_mun_selected}:")
    st.write(data)

    # Retornar uma lista de CNES
    cnes_list = [item["CNES"] for item in data]
    return cnes_list


# Função para buscar todos os dados de CNES e procedimentos de um município
def fetch_cnes_and_procedures_by_municipio(cod_mun_selected):
    client = MongoClient("mongodb://localhost:27017/")
    db_sus = client["SUS"]
    collection_sia_cadgerma = db_sus["SIA_cadgerma"]
    
    # Criar filtro para buscar os registros relacionados ao município
    query_filter = {"CODUFMUN": cod_mun_selected}
    
    # Buscar CNES da collection SIA_cadgerma para o município
    cnes_data = list(collection_sia_cadgerma.find(query_filter, {"CNES": 1, "_id": 0}))
    cnes_list = [item["CNES"] for item in cnes_data]
    
    # Agora buscar os procedimentos na collection SIA_ANALISE com base na lista de CNES
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]
    
    # Filtrar pela lista de CNES e trazer os procedimentos únicos
    query_filter_procedures = {"PA_CODUNI": {"$in": cnes_list}}
    procedures_data = list(collection_sia_analise.find(query_filter_procedures, {"PA_PROC_ID": 1, "IP_DSCR": 1, "_id": 0}))
    
    # Remover procedimentos duplicados e tratar ausência de IP_DSCR
    unique_procedures = {(item["PA_PROC_ID"], item.get("IP_DSCR", "Descrição não disponível")) for item in procedures_data}
    
    client.close()
    
    # Retornar lista de CNES e procedimentos únicos
    return cnes_list, unique_procedures


def fetch_unidades_by_procedimento(cnes_list, selected_procedure):
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]
    
    # Criar filtro para buscar as unidades que realizam o procedimento
    query_filter = {
        "PA_CODUNI": {"$in": cnes_list},
        "PA_PROC_ID": selected_procedure
    }
    
    # Trazer unidades (CNES e FANTASIA) sem duplicatas
    data = list(collection_sia_analise.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))
    unique_unidades = {(item["PA_CODUNI"], item["FANTASIA"]) for item in data}
    
    client.close()
    
    return unique_unidades

# Página de busca por município e procedimento
def search_municipality_procedure_page():
    st.title("Busca por Município e Procedimento")

    # Carregar o arquivo de municípios
    uploaded_file = st.file_uploader("Carregar arquivo de Excel com Municípios", type=["xlsx"])

    if uploaded_file:
        # Carregar o Excel com municípios e converter COD_MUN para string
        municipios_df = load_municipios_excel(uploaded_file)
        st.write("Arquivo de municípios carregado com sucesso.")
        st.dataframe(municipios_df)

        # Permitir que o usuário selecione o município
        selected_municipio = st.selectbox("Selecionar Município", municipios_df["Municipio"].unique())

        # Filtrar pelo código do município selecionado e garantir que é string
        cod_mun_selected = municipios_df.loc[municipios_df["Municipio"] == selected_municipio, "COD_MUN"].values[0]
        cod_mun_selected = str(cod_mun_selected)  # Garantir que COD_MUN seja string
        st.write(f"Município selecionado: {selected_municipio} (Código: {cod_mun_selected})")

        # Buscar CNES e procedimentos associados ao município
        cnes_list, unique_procedures = fetch_cnes_and_procedures_by_municipio(cod_mun_selected)
        
        if unique_procedures:
            # Exibir uma lista suspensa com procedimentos disponíveis no município
            procedures_list = [f"{proc_id} - {desc}" for proc_id, desc in unique_procedures]
            selected_procedure = st.selectbox("Selecionar Procedimento", procedures_list)
            
            # Extrair o código do procedimento selecionado
            procedure_code = selected_procedure.split(" - ")[0]

            # Botão para buscar as unidades que realizam o procedimento
            if st.button('Buscar Unidades que Realizam o Procedimento'):
                unidades = fetch_unidades_by_procedimento(cnes_list, procedure_code)
                
                if unidades:
                    # Ordenar unidades por TOTAL_PA_VALPRO (experiência) em ordem decrescente
                    unidades_list = list(unidades)  # Converter para lista para manipulação
                    client = MongoClient("mongodb://localhost:27017/")
                    db_analise = client["ANALISE"]
                    collection_sia_analise = db_analise["SIA_ANALISE"]

                    # Criar um DataFrame com informações adicionais (experiência)
                    unidades_df = pd.DataFrame(
                        [{"PA_CODUNI": unit[0], "FANTASIA": unit[1]} for unit in unidades_list]
                    )

                    # Adicionar TOTAL_PA_VALPRO ao DataFrame
                    for i, row in unidades_df.iterrows():
                        valpro_data = collection_sia_analise.find_one(
                            {"PA_CODUNI": row["PA_CODUNI"], "PA_PROC_ID": procedure_code},
                            {"TOTAL_PA_VALPRO": 1, "_id": 0}
                        )
                        unidades_df.at[i, "TOTAL_PA_VALPRO"] = valpro_data.get("TOTAL_PA_VALPRO", 0)
                    
                    client.close()

                    # Ordenar por TOTAL_PA_VALPRO em ordem decrescente
                    unidades_df = unidades_df.sort_values(by="TOTAL_PA_VALPRO", ascending=False)

                    st.success("Unidades encontradas!")
                    st.write(f"Número de unidades encontradas: {len(unidades_df)}")
                    
                    # Exibir os dados em formato de tabela
                    st.table(unidades_df)

                else:
                    st.warning("Nenhuma unidade encontrada que realize o procedimento selecionado.")
        else:
            st.warning("Nenhum procedimento encontrado para o município selecionado.")


# Página API
def consulta_unidades_page():
    """
    Página para consultar e inserir unidades de saúde usando a API FastAPI com abas para GET e POST.
    """
    st.title("API - Mongo: Consulta e Inserção de Unidades de Saúde")

    # Criar abas
    aba = st.tabs(["Consulta (GET)", "Inserção (POST)"])

    # Aba de Consulta (GET)
    with aba[0]:
        st.subheader("Consulta de Unidades")
        query = st.text_input("Digite um texto para busca (PA_CODUNI ou parte de FANTASIA):")
        if st.button("Consultar", key="consulta"):
            if query.strip():
                try:
                    # Requisição GET para a API
                    response = requests.get(f"{API_URL}/unidades/", params={"pa_coduni": query})
                    if response.status_code == 200:
                        data = response.json()
                        if "message" in data:
                            st.warning(data["message"])
                        else:
                            st.success("Registros encontrados:")
                            st.json(data)
                    else:
                        st.error(f"Erro ao consultar a API. Código HTTP: {response.status_code}")
                except Exception as e:
                    st.error(f"Erro ao conectar com a API: {e}")
            else:
                st.warning("Por favor, digite um valor para consulta.")

    # Aba de Inserção (POST)
    with aba[1]:
        st.subheader("Inserção de Unidades")
        with st.form("inserir_dados"):
            PA_CODUNI = st.text_input("Código da Unidade (PA_CODUNI):")
            FANTASIA = st.text_input("Nome Fantasia:")
            TOTAL_PA_QTDPRO = st.number_input("Total da Quantidade Produzida (TOTAL_PA_QTDPRO):", min_value=0, step=1)
            TOTAL_PA_QTDAPR = st.number_input("Total da Quantidade Aprovada (TOTAL_PA_QTDAPR):", min_value=0, step=1)
            TOTAL_PA_VALPRO = st.number_input("Valor Produzido (TOTAL_PA_VALPRO):", min_value=0.0, step=0.01, format="%.2f")
            TOTAL_PA_VALAPR = st.number_input("Valor Aprovado (TOTAL_PA_VALAPR):", min_value=0.0, step=0.01, format="%.2f")
            PA_GESTAO = st.text_input("Código da Gestão (PA_GESTAO):")
            PA_MVMR = st.text_input("Ano/Mês da Realização (PA_MVMR):")
            PA_CMPEF = st.text_input("Ano/Mês da Apresentação (PA_CMPEF):")
            PA_PROC_ID = st.text_input("Código do Procedimento (PA_PROC_ID):")
            PA_CBOCOD = st.text_input("CBO do Profissional (PA_CBOCOD):")
            PA_NAT_JUR = st.text_input("Código da Natureza Jurídica (PA_NAT_JUR):")
            IP_DSCR = st.text_input("Descrição do Procedimento (IP_DSCR):")

            # Botão para enviar os dados
            submitted = st.form_submit_button("Inserir Registro")
            if submitted:
                if all([PA_CODUNI, FANTASIA, PA_GESTAO, PA_MVMR, PA_CMPEF, PA_PROC_ID, PA_CBOCOD, PA_NAT_JUR, IP_DSCR]):
                    try:
                        # Dados para o POST
                        payload = {
                            "PA_CODUNI": PA_CODUNI,
                            "FANTASIA": FANTASIA,
                            "TOTAL_PA_QTDPRO": TOTAL_PA_QTDPRO,
                            "TOTAL_PA_QTDAPR": TOTAL_PA_QTDAPR,
                            "TOTAL_PA_VALPRO": TOTAL_PA_VALPRO,
                            "TOTAL_PA_VALAPR": TOTAL_PA_VALAPR,
                            "PA_GESTAO": PA_GESTAO,
                            "PA_MVMR": PA_MVMR,
                            "PA_CMPEF": PA_CMPEF,
                            "PA_PROC_ID": PA_PROC_ID,
                            "PA_CBOCOD": PA_CBOCOD,
                            "PA_NAT_JUR": PA_NAT_JUR,
                            "IP_DSCR": IP_DSCR
                        }
                        response = requests.post(f"{API_URL}/unidades/", json=payload)
                        if response.status_code == 200:
                            st.success("Registro inserido com sucesso!")
                            st.json(response.json())
                        else:
                            st.error(f"Erro ao inserir o registro. Código HTTP: {response.status_code}")
                    except Exception as e:
                        st.error(f"Erro ao conectar com a API: {e}")
                else:
                    st.warning("Todos os campos devem ser preenchidos para inserir um registro.")


def previsao_procedimentos_page():
    """
    Página de previsão de quantidade e valor por procedimento.
    """
    st.title("Previsão de Quantidade e Valor por Unidade e Procedimento")

    # Consultar unidades disponíveis
    st.write("Selecione a unidade:")
    units = fetch_units()
    unit_options = [f"{unit['Código da unidade']} - {unit['Fantasia']}" for unit in units]
    unit_choice = st.selectbox("Unidade", unit_options)

    # Identificar o código da unidade escolhida
    selected_unit = unit_choice.split(" - ")[0]

    # Botão para realizar a previsão
    if st.button("Realizar Previsão"):
        # Executar a previsão
        predictions = predict_totals_by_procedure(selected_unit)

        # Converter resultados em DataFrame
        df = pd.DataFrame(predictions)

        # Exibir a planilha
        st.write("Resultados da Previsão:")
        st.dataframe(df)

        # Botão para download da planilha
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar Planilha",
            data=csv,
            file_name=f"previsao_unidade_{selected_unit}.csv",
            mime="text/csv",
        )

# Função principal para controle de páginas
def main():
    st.sidebar.title("Navegação")
    pages = {
        "Introdução": introduction_page,
        "Data Summary Report": data_summary_report_page,
        "Visualização de Dados": data_visualization_page,
        "Últimas Notícias": latest_news_page,
        "Busca por Município e Procedimento": search_municipality_procedure_page,
        "API - Mongo: Consulta Unidade": consulta_unidades_page,
        "Previsão por Procedimentos": previsao_procedimentos_page
        
    }
    
    choice = st.sidebar.radio("Escolha a página", list(pages.keys()))
    pages[choice]()

# Executar a aplicação
if __name__ == '__main__':
    main()
    