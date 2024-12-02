import streamlit as st
from pymongo import MongoClient
from transformers import pipeline
import os
import pandas as pd

os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"

# Configurar o cache do modelo
@st.cache_resource
def load_model():
    """
    Carrega o modelo Hugging Face e o cacheia para melhorar o desempenho.
    """
    return pipeline("text2text-generation", model="t5-small")

# Modelo global
llm = load_model()

@st.cache_data
def fetch_units():
    """
    Retorna as unidades únicas (PA_CODUNI e FANTASIA) concatenadas no formato dicionário.
    """
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    collection_sia_analise = db_analise["SIA_ANALISE"]

    query_filter = {"FANTASIA": {"$exists": True}}
    data = list(collection_sia_analise.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))
    client.close()

    unique_units = {f"{item['PA_CODUNI']} - {item['FANTASIA']}" for item in data}
    return [{"Código da unidade": unit.split(" - ")[0], "Fantasia": unit.split(" - ")[1]} for unit in unique_units]

@st.cache_data
def fetch_last_12_months_by_procedure(unit_id):
    """
    Consulta os últimos 12 registros por procedimento para uma unidade específica.
    """
    client = MongoClient("mongodb://localhost:27017/")
    db = client["ANALISE"]
    collection = db["SIA_ANALISE"]

    pipeline = [
        {"$match": {"PA_CODUNI": unit_id}},
        {"$sort": {"PA_MVMR": -1}},
        {"$group": {
            "_id": "$PA_PROC_ID",
            "records": {"$push": {
                "Quantidade Aprovado": "$TOTAL_PA_QTDAPR",
                "Valor Aprovado": "$TOTAL_PA_VALAPR",
                "Ano/mês": "$PA_MVMR"
            }},
        }},
        {"$project": {
            "_id": 1,
            "records": {"$slice": ["$records", 12]}
        }}
    ]

    data = list(collection.aggregate(pipeline))
    client.close()

    if not data:
        return []

    return data

def create_context_by_procedure(data):
    """
    Cria um contexto formatado para cada procedimento com os últimos 12 meses.
    """
    contexts = []
    for procedure in data:
        procedure_id = procedure["_id"]
        records = procedure["records"]
        context = f"Código do procedimento {procedure_id}:\n"
        for record in records:
            qtdapr = record.get("Quantidade Aprovado", "N/A")
            valapr = record.get("Valor Aprovado", "N/A")
            mvmr = record.get("Ano/mês", "N/A")
            context += f"Ano/mês: {mvmr}, Quantidade Aprovado: {qtdapr}, Valor Aprovado: R$ {valapr}\n"
        contexts.append({"procedure_id": procedure_id, "context": context})
    return contexts

def parse_prediction(prediction):
    """
    Extrai valores de Quantidade Aprovado e Valor Aprovado da previsão gerada.
    """
    try:
        qtdapr = int(prediction.split("Quantidade Aprovado:")[1].split(",")[0].strip())
    except (IndexError, ValueError):
        qtdapr = 0

    try:
        valapr = int(prediction.split("Valor Aprovado:")[1].split(",")[0].strip())
    except (IndexError, ValueError):
        valapr = 0

    return qtdapr, valapr

def predict_totals_by_procedure(unit_id):
    """
    Realiza previsões por procedimento para uma unidade específica e retorna os resultados em formato tabular.
    """
    data = fetch_last_12_months_by_procedure(unit_id)
    contexts = create_context_by_procedure(data)

    results = []
    total_qtdapr = 0
    total_valapr = 0

    for item in contexts:
        procedure_id = item["procedure_id"]
        context = item["context"]

        # Criar o prompt para o procedimento
        prompt = (
            f"{context}\n"
            "Com base nos dados históricos acima, preveja os seguintes valores para o próximo mês:\n"
            "- Quantidade Aprovado (TOTAL_PA_QTDAPR)\n"
            "- Valor Aprovado (TOTAL_PA_VALAPR).\n"
            "Responda no formato: 'Quantidade Aprovado: <valor>, Valor Aprovado: <valor>'"
        )

        # Gerar a resposta usando o modelo
        response = llm(prompt, max_length=100, do_sample=True, temperature=0.7)
        prediction = response[0]["generated_text"]

        # Extrair valores do texto gerado
        qtdapr, valapr = parse_prediction(prediction)

        total_qtdapr += qtdapr
        total_valapr += valapr

        results.append({
            "Código do procedimento": procedure_id,
            "Quantidade Aprovado": qtdapr,
            "Valor Aprovado": valapr
        })

    # Adicionar linha de totais
    results.append({
        "Código do procedimento": "TOTAL GERAL",
        "Quantidade Aprovado": total_qtdapr,
        "Valor Aprovado": total_valapr
    })

    # Converter resultados para DataFrame
    df_results = pd.DataFrame(results)
    return df_results