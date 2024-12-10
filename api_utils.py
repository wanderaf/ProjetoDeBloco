from fastapi import FastAPI, HTTPException, Query, status
from pymongo import MongoClient
from typing import List
from pydantic import BaseModel, Field
import re
import streamlit as st


# Definir o objeto FastAPI
app = FastAPI()

@st.cache_data
def get_units(query: str = None):
    """
    Recupera as unidades de saúde (PA_CODUNI e FANTASIA) da coleção SIA_ANALISE, com resultados únicos.
    Args:
        query (str, optional): Filtro para buscar unidades pelo código ou nome fantasia.
    Returns:
        list: Lista única de unidades que correspondem ao filtro.
    """
    try:
        client = get_mongo_client()
        db = client["ANALISE"]
        collection = db["SIA_ANALISE"]

        # Aplicar filtro se `query` for fornecido
        query_filter = {}
        if query:
            query_filter = {
                "$or": [
                    {"PA_CODUNI": {"$regex": query, "$options": "i"}},  # Busca parcial no PA_CODUNI
                    {"FANTASIA": {"$regex": query, "$options": "i"}}    # Busca parcial no FANTASIA
                ]
            }

        # Recuperar dados com base no filtro
        data = list(collection.find(query_filter, {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0}))

        # Garantir unicidade dos resultados
        unique_data = {(item["PA_CODUNI"], item["FANTASIA"]) for item in data if "PA_CODUNI" in item and "FANTASIA" in item}

        # Retornar como lista de dicionários
        units = [{"Código da unidade": coduni, "Fantasia": fantasia} for coduni, fantasia in unique_data]

        return units
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar unidades: {e}")



# Configuração da conexão com o MongoDB
def get_mongo_client():
    """
    Configura a conexão com o MongoDB.
    """
    try:
        return MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao conectar ao MongoDB: {e}"
        )

# Obter a coleção do MongoDB
def get_collection():
    try:
        client = get_mongo_client()
        db_analise = client["ANALISE"]
        return db_analise["SIA_ANALISE"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao acessar a coleção MongoDB: {e}"
        )

collection_sia_analise = get_collection()

# Modelos de entrada e saída
class UnidadeData(BaseModel):
    PA_CODUNI: str
    FANTASIA: str
    TOTAL_PA_QTDPRO: int
    TOTAL_PA_QTDAPR: int
    TOTAL_PA_VALPRO: float
    TOTAL_PA_VALAPR: float
    PA_GESTAO: str
    PA_MVMR: str
    PA_CMPEF: str
    PA_PROC_ID: str
    PA_CBOCOD: str
    PA_NAT_JUR: str
    IP_DSCR: str

class ChatRequest(BaseModel):
    question: str

class ProcessedQuestionResponse(BaseModel):
    processed_question: str
    analysis_type: str

class QueryResult(BaseModel):
    unidade: str
    total: int

class ChatResponse(BaseModel):
    question: str
    processed_question: ProcessedQuestionResponse
    results: List[QueryResult]

# Rota de teste
@app.get("/")
async def root():
    """
    Endpoint raiz para testar se o servidor está ativo.
    """
    return {"message": "API FastAPI está funcionando!"}

def insert_unit(unit_data):
    """
    Insere um novo registro de unidade de saúde na coleção SIA_ANALISE.

    Args:
        unit_data (dict): Dados da unidade a ser inserida.
            Deve conter os seguintes campos obrigatórios:
            - PA_CODUNI
            - FANTASIA
            - TOTAL_PA_QTDPRO
            - TOTAL_PA_QTDAPR
            - TOTAL_PA_VALPRO
            - TOTAL_PA_VALAPR
            - PA_GESTAO
            - PA_MVMR
            - PA_CMPEF
            - PA_PROC_ID
            - PA_CBOCOD
            - PA_NAT_JUR
            - IP_DSCR

    Returns:
        dict: Mensagem de sucesso com o ID do documento inserido.
    """
    try:
        client = get_mongo_client()
        db = client["ANALISE"]
        collection = db["SIA_ANALISE"]

        # Inserir o documento na coleção
        result = collection.insert_one(unit_data)

        # Verificar se a inserção foi bem-sucedida
        if not result.inserted_id:
            raise Exception("Erro ao inserir o registro no banco de dados.")

        return {"message": "Registro inserido com sucesso!", "id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir unidade: {e}")


# Rota de consulta de unidades
@app.get("/unidades/", response_model=List[dict])
async def consultar_unidades(pa_coduni: str = Query(..., description="Texto para busca (PA_CODUNI ou parte de FANTASIA)")):
    """
    Consulta unidades de saúde na coleção SIA_ANALISE pelo PA_CODUNI ou parte do nome FANTASIA.
    """
    try:
        query_filter = {
            "$or": [
                {"PA_CODUNI": {"$regex": pa_coduni, "$options": "i"}},
                {"FANTASIA": {"$regex": pa_coduni, "$options": "i"}}
            ]
        }

        resultados = collection_sia_analise.find(query_filter, {"_id": 0, "PA_CODUNI": 1, "FANTASIA": 1})
        dados_unicos = list({(res["PA_CODUNI"], res["FANTASIA"]) for res in resultados if "PA_CODUNI" in res and "FANTASIA" in res})

        if not dados_unicos:
            return {"message": "Nenhum registro encontrado para a consulta."}

        return [{"PA_CODUNI": item[0], "FANTASIA": item[1]} for item in dados_unicos]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")

# Rota para adicionar unidade
@app.post("/unidades/")
async def adicionar_unidade(unidade: UnidadeData):
    """
    Adiciona manualmente um registro na coleção SIA_ANALISE.
    """
    try:
        unidade_dict = unidade.dict()
        resultado = collection_sia_analise.insert_one(unidade_dict)

        if not resultado.inserted_id:
            raise HTTPException(status_code=500, detail="Erro ao inserir o registro no banco de dados.")

        return {"message": "Registro inserido com sucesso!", "id": str(resultado.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")

# Rota para chat com LLM
@app.post("/chat/converse", response_model=ChatResponse)
async def converse(chat_request: ChatRequest):
    """
    Endpoint para responder perguntas específicas com base nos dados do MongoDB.
    """
    try:
        pergunta = chat_request.question.lower()

        # Processamento da pergunta
        if "procedimentos apresentados" in pergunta or "total apresentados" in pergunta:
            analysis_type = "procedimentos_apresentados"
        elif "procedimentos aprovados" in pergunta or "total aprovados" in pergunta:
            analysis_type = "procedimentos_aprovados"
        else:
            return ChatResponse(
                question=chat_request.question,
                processed_question=ProcessedQuestionResponse(
                    processed_question="Interpretação não definida.",
                    analysis_type="unknown"
                ),
                results=[]
            )

        unidade_match = re.search(r"unidade\s(.+)", pergunta)
        unidade_nome = unidade_match.group(1).strip() if unidade_match else None
        if not unidade_nome:
            raise HTTPException(status_code=400, detail="Nome da unidade não encontrado na pergunta.")

        query = {"FANTASIA": {"$regex": unidade_nome, "$options": "i"}}
        dados = list(collection_sia_analise.find(query, {"_id": 0}))

        if not dados:
            return ChatResponse(
                question=chat_request.question,
                processed_question=ProcessedQuestionResponse(
                    processed_question="Nenhum dado encontrado.",
                    analysis_type=analysis_type
                ),
                results=[]
            )

        results = []
        if analysis_type == "procedimentos_apresentados":
            total_procedimentos = sum(item.get("TOTAL_PA_QTDPRO", 0) for item in dados)
            results.append(QueryResult(unidade=unidade_nome, total=total_procedimentos))
        elif analysis_type == "procedimentos_aprovados":
            total_aprovados = sum(item.get("TOTAL_PA_QTDAPR", 0) for item in dados)
            results.append(QueryResult(unidade=unidade_nome, total=total_aprovados))

        return ChatResponse(
            question=chat_request.question,
            processed_question=ProcessedQuestionResponse(
                processed_question="Processado com sucesso.",
                analysis_type=analysis_type
            ),
            results=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a pergunta: {e}")
