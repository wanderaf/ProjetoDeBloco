import streamlit as st
import pandas as pd
from mongo import fetch_cnes_and_procedures_by_municipio, fetch_unidades_by_procedimento, fetch_total_valpro
from file_utils import load_excel_file

def search_municipality_procedure_page():
    st.title("Busca por Município e Procedimento")

    # Carregar o arquivo de municípios
    uploaded_file = st.file_uploader("Carregar arquivo de Excel com Municípios", type=["xlsx"])

    if uploaded_file:
        # Carregar o Excel com municípios
        municipios_df = load_excel_file(uploaded_file)
        st.write("Arquivo de municípios carregado com sucesso.")
        st.dataframe(municipios_df)

        # Selecionar município
        selected_municipio = st.selectbox("Selecionar Município", municipios_df["Municipio"].unique())
        cod_mun_selected = municipios_df.loc[municipios_df["Municipio"] == selected_municipio, "COD_MUN"].values[0]
        cod_mun_selected = str(cod_mun_selected)  # Garantir que COD_MUN seja string
        st.write(f"Município selecionado: {selected_municipio} (Código: {cod_mun_selected})")

        # Buscar CNES e procedimentos associados ao município
        cnes_list, unique_procedures = fetch_cnes_and_procedures_by_municipio(cod_mun_selected)

        if unique_procedures:
            # Selecionar procedimento
            procedures_list = [f"{proc_id} - {desc}" for proc_id, desc in unique_procedures]
            selected_procedure = st.selectbox("Selecionar Procedimento", procedures_list)
            procedure_code = selected_procedure.split(" - ")[0]

            # Botão para buscar unidades
            if st.button("Buscar Unidades que Realizam o Procedimento"):
                unidades = fetch_unidades_by_procedimento(cnes_list, procedure_code)

                if unidades:
                    unidades_df = pd.DataFrame(
                        [{"PA_CODUNI": unit[0], "FANTASIA": unit[1]} for unit in unidades]
                    )

                    # Ordenar por TOTAL_PA_VALPRO, adicionando informações adicionais
                    unidades_df["TOTAL_PA_VALPRO"] = unidades_df["PA_CODUNI"].apply(
                        lambda coduni: fetch_total_valpro(coduni, procedure_code)
                    )
                    unidades_df = unidades_df.sort_values(by="TOTAL_PA_VALPRO", ascending=False)

                    st.success("Unidades encontradas!")
                    st.write(f"Número de unidades encontradas: {len(unidades_df)}")
                    st.table(unidades_df)
                else:
                    st.warning("Nenhuma unidade encontrada que realize o procedimento selecionado.")
        else:
            st.warning("Nenhum procedimento encontrado para o município selecionado.")
