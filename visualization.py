import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mongo import fetch_filter_options, fetch_filtered_data_from_mongo
from file_utils import convert_df_to_csv

def data_visualization_page():
    st.title("Visualização de Dados")

    # Obter opções de filtro
    fantasia_options = fetch_filter_options()
    st.sidebar.header("Filtros de Dados")
    selected_fantasia = st.sidebar.selectbox(
        "Unidade de Saúde", options=fantasia_options, index=0, key="selected_fantasia"
    )
    selected_ano = st.sidebar.text_input("Ano", value="2024", key="selected_ano")

    # Botão para carregar dados
    if st.button("Carregar Dados Filtrados", key="load_data_button"):
        data = fetch_filtered_data_from_mongo(fantasia=selected_fantasia, ano=selected_ano)

        # Verificar se os dados foram encontrados e convertê-los para DataFrame
        if isinstance(data, list) and len(data) > 0:
            data = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame) and not data.empty:
            pass
        else:
            st.warning("Nenhum dado encontrado com os filtros aplicados.")
            return  # Encerrar execução da função se não houver dados

        st.success("Dados carregados com sucesso!")

        # Processar os dados
        if "PA_MVMR" in data.columns:
            data["MÊS"] = data["PA_MVMR"].astype(str).apply(lambda x: x[-2:])  # Extrair mês
        else:
            st.error("A coluna 'PA_MVMR' não está disponível nos dados.")
            return

        if "TOTAL_PA_VALPRO" in data.columns and "TOTAL_PA_VALAPR" in data.columns:
            data["GLOSAS"] = data["TOTAL_PA_VALPRO"] - data["TOTAL_PA_VALAPR"]
        else:
            st.error("As colunas 'TOTAL_PA_VALPRO' ou 'TOTAL_PA_VALAPR' não estão disponíveis nos dados.")
            return

        # Exibir Resumo Estatístico
        st.write("Resumo Estatístico:")
        st.dataframe(data.describe())

        # Gráfico 1: Valor Aprovado ao longo dos meses
        if "MÊS" in data.columns and "TOTAL_PA_VALAPR" in data.columns:
            st.subheader("Evolução do Valor Aprovado por Mês")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby("MÊS")["TOTAL_PA_VALAPR"].sum().plot(kind="area", ax=ax, alpha=0.7)
            ax.set_title("Valor Total Aprovado por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Valor Aprovado")
            st.pyplot(fig)

        # Gráfico 2: Quantidade de Glosas por Mês
        if "MÊS" in data.columns and "GLOSAS" in data.columns:
            st.subheader("Quantidade de Glosas por Mês")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby("MÊS")["GLOSAS"].sum().plot(kind="line", ax=ax, marker="o", color="red")
            ax.set_title("Quantidade de Glosas por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Quantidade de Glosas")
            st.pyplot(fig)

        # Gráfico 3: Principais Procedimentos com Glosas
        if "IP_DSCR" in data.columns and "GLOSAS" in data.columns:
            st.subheader("Principais Procedimentos com Glosas")
            glosas_por_procedimento = data.groupby("IP_DSCR")["GLOSAS"].sum().nlargest(10)
            fig, ax = plt.subplots(figsize=(10, 5))
            glosas_por_procedimento.plot(kind="bar", ax=ax, color="orange")
            ax.set_title("Top 10 Procedimentos com Maior Quantidade de Glosas")
            ax.set_xlabel("Descrição do Procedimento")
            ax.set_ylabel("Quantidade de Glosas")
            st.pyplot(fig)

        # Gráfico 4: Comparação entre Valores Produzidos e Aprovados
        if "MÊS" in data.columns and {"TOTAL_PA_VALPRO", "TOTAL_PA_VALAPR"}.issubset(data.columns):
            st.subheader("Comparação entre Valores Produzidos e Aprovados")
            fig, ax = plt.subplots(figsize=(10, 5))
            data.groupby("MÊS")[["TOTAL_PA_VALPRO", "TOTAL_PA_VALAPR"]].sum().plot(kind="bar", ax=ax)
            ax.set_title("Valores Produzidos vs Aprovados por Mês")
            ax.set_xlabel("Mês")
            ax.set_ylabel("Valores")
            st.pyplot(fig)

        # Botão para download do CSV
        csv_data = convert_df_to_csv(data)
        st.download_button(
            label="Baixar dados como CSV",
            data=csv_data,
            file_name="dados_filtrados.csv",
            mime="text/csv",
            key="download_button"
        )
