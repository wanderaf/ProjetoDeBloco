import streamlit as st
from api_utils import get_units, insert_unit

def consulta_unidades_page():
    """
    Página para consultar e inserir unidades de saúde usando a API FastAPI.
    """
    st.title("API - Mongo: Consulta e Inserção de Unidades de Saúde")

    # Criar abas para organização
    aba = st.tabs(["Consulta (GET)", "Inserção (POST)"])

    # Aba de Consulta (GET)
    with aba[0]:
        st.subheader("Consulta de Unidades")
        query = st.text_input("Digite um texto para busca (PA_CODUNI ou parte de FANTASIA):")
        if st.button("Consultar", key="consulta"):
            if query.strip():
                data, error = get_units(query)
                if error:
                    st.error(error)
                elif data:
                    st.success("Registros encontrados:")
                    st.json(data)
                else:
                    st.warning("Nenhum registro encontrado.")
            else:
                st.warning("Por favor, digite um valor para consulta.")

    # Aba de Inserção (POST)
    with aba[1]:
        st.subheader("Inserção de Unidades")
        with st.form("inserir_dados"):
            PA_CODUNI = st.text_input("Código da Unidade (PA_CODUNI):")
            FANTASIA = st.text_input("Nome Fantasia:")
            TOTAL_PA_QTDPRO = st.number_input(
                "Total da Quantidade Produzida (TOTAL_PA_QTDPRO):", min_value=0, step=1
            )
            TOTAL_PA_QTDAPR = st.number_input(
                "Total da Quantidade Aprovada (TOTAL_PA_QTDAPR):", min_value=0, step=1
            )
            TOTAL_PA_VALPRO = st.number_input(
                "Valor Produzido (TOTAL_PA_VALPRO):", min_value=0.0, step=0.01, format="%.2f"
            )
            TOTAL_PA_VALAPR = st.number_input(
                "Valor Aprovado (TOTAL_PA_VALAPR):", min_value=0.0, step=0.01, format="%.2f"
            )
            PA_GESTAO = st.text_input("Código da Gestão (PA_GESTAO):")
            PA_MVMR = st.text_input("Ano/Mês da Realização (PA_MVMR):")
            PA_CMPEF = st.text_input("Ano/Mês da Apresentação (PA_CMPEF):")
            PA_PROC_ID = st.text_input("Código do Procedimento (PA_PROC_ID):")
            PA_CBOCOD = st.text_input("CBO do Profissional (PA_CBOCOD):")
            PA_NAT_JUR = st.text_input("Código da Natureza Jurídica (PA_NAT_JUR):")
            IP_DSCR = st.text_input("Descrição do Procedimento (IP_DSCR):")

            # Botão para enviar os dados
            submitted = st.form_submit_button("Inserir Registro")
            if submitted:
                if all(
                    [PA_CODUNI, FANTASIA, PA_GESTAO, PA_MVMR, PA_CMPEF, PA_PROC_ID, PA_CBOCOD, PA_NAT_JUR, IP_DSCR]
                ):
                    payload = {
                        "PA_CODUNI": PA_CODUNI,
                        "FANTASIA": FANTASIA,
                        "TOTAL_PA_QTDPRO": TOTAL_PA_QTDPRO,
                        "TOTAL_PA_QTDAPR": TOTAL_PA_QTDAPR,
                        "TOTAL_PA_VALPRO": TOTAL_PA_VALPRO,
                        "TOTAL_PA_VALAPR": TOTAL_PA_VALAPR,
                        "PA_GESTAO": PA_GESTAO,
                        "PA_MVMR": PA_MVMR,
                        "PA_CMPEF": PA_CMPEF,
                        "PA_PROC_ID": PA_PROC_ID,
                        "PA_CBOCOD": PA_CBOCOD,
                        "PA_NAT_JUR": PA_NAT_JUR,
                        "IP_DSCR": IP_DSCR,
                    }
                    success, error = insert_unit(payload)
                    if success:
                        st.success("Registro inserido com sucesso!")
                        st.json(success)
                    else:
                        st.error(error)
                else:
                    st.warning("Todos os campos obrigatórios devem ser preenchidos.")
