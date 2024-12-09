import streamlit as st
from file_utils import load_news_data, extract_news_content, generate_wordcloud, run_news_scraper
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
