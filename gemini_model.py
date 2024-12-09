import google.generativeai as genai
from config import IA_API_KEY

# Configurar o Gemini
genai.configure(api_key=IA_API_KEY)

def generate_report(unit_name, unit_data):
    """
    Gera um relatório inteligente com base nos dados de uma unidade.
    Args:
        unit_name (str): Nome da unidade.
        unit_data (pd.DataFrame): Dados da unidade.
    Returns:
        str: Relatório gerado pelo modelo Gemini.
    """
    # Preparar dados para o prompt
    historical_summary = ""
    top_glosas = ""
    recommendations = ""

    if not unit_data.empty:
        if "PA_MVMR" in unit_data.columns and "TOTAL_PA_VALAPR" in unit_data.columns:
            grouped = unit_data.groupby("PA_MVMR")["TOTAL_PA_VALAPR"].sum().sort_index()
            historical_summary = "\n".join(
                [f"Mês/Ano: {month}, Valor Aprovado: R$ {value:,.2f}" for month, value in grouped.items()]
            )
        else:
            historical_summary = "Dados insuficientes para gerar o histórico de valores aprovados."

        if "IP_DSCR" in unit_data.columns and "TOTAL_PA_VALPRO" in unit_data.columns and "TOTAL_PA_VALAPR" in unit_data.columns:
            unit_data["GLOSAS"] = unit_data["TOTAL_PA_VALPRO"] - unit_data["TOTAL_PA_VALAPR"]
            glosas = unit_data.groupby("IP_DSCR")["GLOSAS"].sum().nlargest(5)
            top_glosas = "\n".join([f"Procedimento: {proc}, Glosas: R$ {value:,.2f}" for proc, value in glosas.items()])
        else:
            top_glosas = "Dados insuficientes para identificar as maiores glosas."

        recommendations = (
            "Sugestões para reduzir glosas incluem revisar codificações, melhorar a conformidade documental "
            "e otimizar processos de aprovação."
        )
    else:
        historical_summary = "Nenhum dado encontrado para a unidade."
        top_glosas = "Nenhum dado encontrado para glosas."
        recommendations = "Sem recomendações devido à ausência de dados."

    # Criar o prompt
    prompt = f"""
    Gere um relatório detalhado para a unidade de saúde {unit_name}, baseado nos seguintes dados:

    1. Histórico de Valores Aprovados:
    {historical_summary}

    2. Procedimentos com Maiores Glosas:
    {top_glosas}

    3. Recomendações:
    {recommendations}

    O relatório deve ser claro, objetivo e incluir insights relevantes.
    """

    # Gerar conteúdo usando o modelo Gemini
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")  # Criar instância do modelo
        response = model.generate_content(prompt)  # Gerar conteúdo com o prompt
        
        # Verificar e retornar o texto gerado
        if hasattr(response, "text") and response.text:
            return response.text  # Retorna o texto gerado
        else:
            return "Erro: O modelo não retornou um texto válido."
    except AttributeError as e:
        return f"Erro na configuração do modelo Gemini: {e}"
    except Exception as e:
        return f"Erro ao gerar o relatório: {e}"
