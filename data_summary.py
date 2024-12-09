import streamlit as st
import pandas as pd
from mongo import fetch_all_data

def data_summary_page():
    st.title("Data Summary Report")
    st.write("""
    Este relatório resume os dados coletados, integrados e analisados ao longo do projeto.
    O objetivo é fornecer uma visão detalhada do pipeline de dados desde a aquisição até
    a geração de insights utilizando técnicas de IA.
    """)

    # Dados do MongoDB
    st.header("1. Dados Coletados")
    st.write("""
    - **Fonte dos Dados**: FTP do SUS, APIs externas e web scraping.
    - **Estrutura de Dados**: Dados relacionados à produção de saúde, contendo informações como:
        - Unidade de Saúde (FANTASIA)
        - Procedimentos realizados (PA_PROC_ID e descrição)
        - Quantidade e valores apresentados e aprovados.
    """)

    data = fetch_all_data()
    df = pd.DataFrame(data)

    if not df.empty:
        st.header("2. Estatísticas dos Dados")
        st.write(f"- **Registros Totais**: {len(df)}")
        st.write(f"- **Número de Colunas**: {len(df.columns)}")
        st.write("**Estatísticas Descritivas:**")
        st.dataframe(df.describe())

        st.header("3. Valores Faltantes")
        missing_values = df.isnull().sum()
        st.write(missing_values[missing_values > 0])
    else:
        st.warning("Nenhum dado disponível no banco de dados para gerar o resumo.")
