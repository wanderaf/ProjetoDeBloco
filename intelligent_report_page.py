import streamlit as st
import pandas as pd
from pymongo import MongoClient
from gemini_model import generate_report
from config import MONGO_URI

def fetch_unit_data(unit_name):
    """
    Busca dados do MongoDB para uma unidade específica.
    Args:
        unit_name (str): Nome da unidade para consulta.
    Returns:
        pd.DataFrame: Dados da unidade em formato de DataFrame.
    """
    client = MongoClient(MONGO_URI)
    db = client["ANALISE"]
    collection = db["SIA_ANALISE"]

    query = {"FANTASIA": {"$regex": unit_name, "$options": "i"}}
    data = list(collection.find(query, {"_id": 0}))
    client.close()

    return pd.DataFrame(data) if data else pd.DataFrame()

def intelligent_report_page():
    """
    Página para geração de relatórios inteligentes com base nos dados do MongoDB.
    """
    st.title("Relatório Inteligente")
    st.write("Selecione uma unidade de saúde para gerar um relatório detalhado com insights inteligentes.")

    unit_name = st.text_input("Digite o nome da unidade de saúde:", placeholder="Ex.: Unidade Básica de Saúde XYZ")

    if st.button("Gerar Relatório"):
        if unit_name.strip():
            st.info("Buscando dados da unidade...")
            unit_data = fetch_unit_data(unit_name)

            if not unit_data.empty:
                st.success("Dados encontrados! Gerando relatório...")
                report = generate_report(unit_name, unit_data)

                st.subheader("Relatório Gerado")
                st.write(report)

                st.download_button(
                    label="Baixar Relatório",
                    data=report,
                    file_name=f"relatorio_{unit_name.replace(' ', '_')}.txt",
                    mime="text/plain",
                )
            else:
                st.warning("Nenhum dado encontrado para a unidade informada.")
        else:
            st.warning("Por favor, insira o nome da unidade.")
