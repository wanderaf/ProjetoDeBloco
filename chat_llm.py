import streamlit as st
import requests
from config import API_URL

def chat_with_llm_page():
    """
    Página de interação com o modelo LLM através da API.
    """
    st.title("Chat com o Modelo LLM")
    st.write("""
    Bem-vindo ao chat interativo! Envie suas perguntas sobre os dados disponíveis na aplicação 
    e receba respostas geradas pelo modelo de linguagem.
    """)

    # Entrada para a pergunta do usuário
    user_input = st.text_input("Digite sua pergunta:", placeholder="Ex.: Qual é o total aprovado para a unidade X?")

    if st.button("Enviar"):
        if user_input.strip():
            try:
                # Montar URL do endpoint
                endpoint = f"{API_URL}/chat/converse"
                
                # Enviar requisição POST para a API
                response = requests.post(endpoint, json={"question": user_input})

                if response.status_code == 200:
                    # Processar a resposta da API
                    data = response.json()
                    st.success("Resposta do modelo:")
                    
                    # Mostrar pergunta processada e tipo de análise
                    st.write("**Pergunta Processada:**", data.get("processed_question", {}).get("processed_question", "N/A"))
                    st.write("**Tipo de Análise:**", data.get("processed_question", {}).get("analysis_type", "N/A"))

                    # Mostrar resultados
                    results = data.get("results", [])
                    if results:
                        st.write("**Resultados:**")
                        for result in results:
                            st.write(f"- Unidade: {result.get('unidade', 'N/A')}, Total: {result.get('total', 'N/A')}")
                    else:
                        st.info("Nenhum resultado encontrado para a consulta.")
                else:
                    st.error(f"Erro na API. Código HTTP: {response.status_code}")
                    st.write("Detalhes:", response.text)

            except requests.exceptions.RequestException as e:
                st.error("Erro ao conectar com a API.")
                st.write(f"Detalhes do erro: {e}")
        else:
            st.warning("Por favor, insira uma pergunta antes de enviar.")
