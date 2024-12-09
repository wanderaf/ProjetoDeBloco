import pandas as pd
from bs4 import BeautifulSoup
import requests
import io
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
import streamlit as st
import sys
import io
import subprocess

def load_news_data(path="data/noticias.csv"):
    """Carrega dados de notícias de um arquivo CSV."""
    return pd.read_csv(path)

def extract_news_content(url):
    """Extrai o conteúdo de um artigo de notícias a partir de uma URL."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join([p.get_text() for p in paragraphs])
    except Exception as e:
        return f"Erro ao acessar a notícia: {e}"

def convert_df_to_csv(df):
    """Converte um DataFrame em um arquivo CSV no formato string."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

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

def load_excel_file(uploaded_file):
    """Carrega um arquivo Excel em um DataFrame."""
    df = pd.read_excel(uploaded_file)
    df["COD_MUN"] = df["COD_MUN"].astype(str)  # Garantir que COD_MUN seja string
    return df