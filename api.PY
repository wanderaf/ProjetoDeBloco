from fastapi import FastAPI, HTTPException, Query, status
from pymongo import MongoClient
from typing import List, Dict
from pydantic import BaseModel, Field
import re
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM

# Função para configurar a conexão com o MongoDB
def fetch_all_data():
    """
    Configura a conexão com o MongoDB e retorna a coleção SIA_ANALISE.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db_analise = client["ANALISE"]
        return db_analise["SIA_ANALISE"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao conectar ao MongoDB: {e}"
        )

# Obter a coleção do MongoDB
try:
    collection_sia_analise = fetch_all_data()
except HTTPException as e:
    collection_sia_analise = None

class UnidadeData(BaseModel):
    """
    Modelo para validar os dados de entrada no método POST.
    """
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

# Inicializar o FastAPI
app = FastAPI()

@app.get("/")
async def root():
    """
    Endpoint raiz para testar se o servidor está ativo.
    """
    return {"message": "API FastAPI está funcionando!"}

@app.get("/unidades/", response_model=List[dict])
async def consultar_unidades(pa_coduni: str = Query(..., description="Texto para busca (PA_CODUNI ou parte de FANTASIA)")):
    """
    Consulta unidades de saúde na coleção SIA_ANALISE pelo PA_CODUNI ou parte do nome FANTASIA.
    - Se `pa_coduni` corresponder a parte do PA_CODUNI, retorna todos os registros correspondentes.
    - Se `pa_coduni` corresponder a parte do FANTASIA, retorna todos os registros correspondentes.
    """
    try:
        # Construir o filtro de busca dinâmico
        query_filter = {
            "$or": [
                {"PA_CODUNI": {"$regex": pa_coduni, "$options": "i"}},  # Busca parcial no PA_CODUNI
                {"FANTASIA": {"$regex": pa_coduni, "$options": "i"}}    # Busca parcial no FANTASIA
            ]
        }

        # Buscar dados no MongoDB
        resultados = collection_sia_analise.find(query_filter, {"_id": 0, "PA_CODUNI": 1, "FANTASIA": 1})

        # Garantir unicidade dos resultados
        dados_unicos = list({(res["PA_CODUNI"], res["FANTASIA"]) for res in resultados if "PA_CODUNI" in res and "FANTASIA" in res})

        # Verificar se há registros encontrados
        if not dados_unicos:
            return {"message": "Nenhum registro encontrado para a consulta."}

        # Formatar como lista de dicionários
        resposta_formatada = [{"PA_CODUNI": item[0], "FANTASIA": item[1]} for item in dados_unicos]

        return resposta_formatada

    except Exception as e:
        # Log detalhado do erro para depuração
        print(f"Erro ao consultar unidades: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")

@app.post("/unidades/")
async def adicionar_unidade(unidade: UnidadeData):
    """
    Endpoint para adicionar manualmente um registro na coleção SIA_ANALISE.
    """
    try:
        # Converter o objeto Pydantic para um dicionário
        unidade_dict = unidade.dict()

        # Inserir o registro no MongoDB
        resultado = collection_sia_analise.insert_one(unidade_dict)

        # Verificar se a inserção foi bem-sucedida
        if not resultado.inserted_id:
            raise HTTPException(status_code=500, detail="Erro ao inserir o registro no banco de dados.")

        return {"message": "Registro inserido com sucesso!", "id": str(resultado.inserted_id)}

    except Exception as e:
        print(f"Erro ao adicionar unidade: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor.")


# Carregar o modelo HuggingFace
model_name = "t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Modelos de entrada e saída
class ChatRequest(BaseModel):
    question: str = Field(..., example="Qual o total de procedimentos apresentados na unidade X?")

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

# Função para gerar respostas usando HuggingFace
def generate_response(input_text: str) -> str:
    if not model or not tokenizer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo LLM não está carregado. Tente novamente mais tarde."
        )
    try:
        inputs = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(inputs["input_ids"], max_length=512, num_beams=5, early_stopping=True)
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar texto com o modelo LLM: {e}"
        )

@app.post("/chat/converse", response_model=ChatResponse)
async def converse(chat_request: ChatRequest):
    """
    Endpoint para responder perguntas específicas com base nos dados do MongoDB.
    """
    try:
        # Processar a pergunta com o modelo HuggingFace
        try:
            pergunta = chat_request.question.lower()
            processed_question = generate_response(f"Interprete a pergunta: {pergunta}")
            print(f"Processed Question: {processed_question}")  # Log para depuração
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Erro ao processar a pergunta no modelo LLM: {e}"
            )

        # Mapear tipo de análise baseado na pergunta
        analysis_type = ""
        if "procedimentos apresentados" in pergunta or "total apresentados" in pergunta:
            analysis_type = "procedimentos_apresentados"
        elif "procedimentos aprovados" in pergunta or "total aprovados" in pergunta:
            analysis_type = "procedimentos_aprovados"
        else:
            return ChatResponse(
                question=chat_request.question,
                processed_question=ProcessedQuestionResponse(
                    processed_question=processed_question,
                    analysis_type="unknown"
                ),
                results=[]
            )

        # Extrair nome da unidade de saúde
        try:
            unidade_match = re.search(r"unidade\s(.+)", pergunta)
            unidade_nome = unidade_match.group(1).strip() if unidade_match else None
            if not unidade_nome:
                raise ValueError("Nome da unidade não encontrado na pergunta.")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao identificar a unidade de saúde: {e}"
            )

        # Buscar no MongoDB com base no tipo de análise
        try:
            query = {"FANTASIA": {"$regex": unidade_nome, "$options": "i"}}
            dados = list(collection_sia_analise.find(query, {"_id": 0}))
            if not dados:
                return ChatResponse(
                    question=chat_request.question,
                    processed_question=ProcessedQuestionResponse(
                        processed_question=processed_question,
                        analysis_type=analysis_type
                    ),
                    results=[]
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao consultar o banco de dados: {e}"
            )

        # Processar resultados com base no tipo de análise
        try:
            results = []
            if analysis_type == "procedimentos_apresentados":
                total_procedimentos = sum(item.get("TOTAL_PA_QTDPRO", 0) for item in dados)
                results.append(QueryResult(unidade=unidade_nome, total=total_procedimentos))
            elif analysis_type == "procedimentos_aprovados":
                total_aprovados = sum(item.get("TOTAL_PA_QTDAPR", 0) for item in dados)
                results.append(QueryResult(unidade=unidade_nome, total=total_aprovados))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar os resultados: {e}"
            )

        # Retornar resposta final
        return ChatResponse(
            question=chat_request.question,
            processed_question=ProcessedQuestionResponse(
                processed_question=processed_question,
                analysis_type=analysis_type
            ),
            results=results
        )

    except HTTPException as e:
        print(f"Erro HTTP: {e.detail}")  # Log para depuração
        raise e
    except Exception as e:
        print(f"Erro inesperado: {e}")  # Log para depuração
        raise HTTPException(
            status_code=500,
            detail="Erro interno no servidor."
        )