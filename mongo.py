from pymongo import MongoClient
import pandas as pd

def connect_to_mongo():
    """Estabelece conexão com o MongoDB."""
    client = MongoClient("mongodb://localhost:27017/")
    return client

def fetch_all_data():
    """Busca todos os dados da coleção SIA_ANALISE."""
    client = connect_to_mongo()
    collection = client["ANALISE"]["SIA_ANALISE"]
    data = list(collection.find({}, {"_id": 0}))
    client.close()
    return data

def fetch_filter_options():
    """Busca as opções de filtro para 'FANTASIA'."""
    client = connect_to_mongo()
    collection = client["ANALISE"]["SIA_ANALISE"]
    options = collection.distinct("FANTASIA")
    client.close()
    return options

def fetch_filtered_data_from_mongo(fantasia=None, ano=None):
    """Busca dados filtrados por 'FANTASIA' e 'ANO'."""
    client = connect_to_mongo()
    collection = client["ANALISE"]["SIA_ANALISE"]
    
    query_filter = {}
    if fantasia:
        query_filter["FANTASIA"] = fantasia
    if ano:
        query_filter["PA_MVMR"] = {"$regex": f"^{ano}"}
    
    data = list(collection.find(query_filter, {"_id": 0}))
    client.close()
    return data

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

def fetch_unidades_by_procedimento(cnes_list, procedure_code):
    """Busca unidades que realizam determinado procedimento."""
    client = MongoClient("mongodb://localhost:27017/")
    collection = client["ANALISE"]["SIA_ANALISE"]

    unidades = list(
        collection.find(
            {"PA_CODUNI": {"$in": cnes_list}, "PA_PROC_ID": procedure_code},
            {"PA_CODUNI": 1, "FANTASIA": 1, "_id": 0},
        )
    )
    client.close()
    return {(unit["PA_CODUNI"], unit["FANTASIA"]) for unit in unidades}

def fetch_total_valpro(pa_coduni, procedure_code):
    """Busca o valor total produzido para uma unidade e procedimento."""
    client = MongoClient("mongodb://localhost:27017/")
    collection = client["ANALISE"]["SIA_ANALISE"]
    result = collection.find_one(
        {"PA_CODUNI": pa_coduni, "PA_PROC_ID": procedure_code}, {"TOTAL_PA_VALPRO": 1, "_id": 0}
    )
    client.close()
    return result.get("TOTAL_PA_VALPRO", 0) if result else 0