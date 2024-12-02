from fastapi import FastAPI, HTTPException, Query
from pymongo import MongoClient
from typing import List, Dict
from pydantic import BaseModel
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline

# Função para configurar a conexão com o MongoDB
def fetch_all_data():
    """
    Configura a conexão com o MongoDB e retorna a coleção SIA_ANALISE.
    """
    client = MongoClient("mongodb://localhost:27017/")
    db_analise = client["ANALISE"]
    return db_analise["SIA_ANALISE"]

# Obter a coleção do MongoDB
collection_sia_analise = fetch_all_data()

# Inicializar o FastAPI
app = FastAPI()

# Carregar o modelo T5
model_name = "t5-base"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

# Modelos de entrada e saída
class PerguntaRequest(BaseModel):
    pergunta: str

class Resposta(BaseModel):
    pergunta: str
    resposta: str
    detalhes: Dict

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