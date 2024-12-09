import streamlit as st
import pandas as pd
from prediction_utils import fetch_units, predict_totals_by_procedure

def previsao_procedimentos_page():
    """
    Página para previsão de quantidade e valor por procedimento.
    """
    st.title("Previsão de Quantidade e Valor por Procedimento")
    st.write("""
    Esta página permite realizar previsões de quantidade e valor total de procedimentos
    realizados por uma unidade de saúde.
    """)

    # Carregar unidades disponíveis
    units = fetch_units()
    if not units:
        st.error("Erro ao carregar as unidades disponíveis. Verifique sua conexão.")
        return

    unit_options = [f"{unit['Código da unidade']} - {unit['Fantasia']}" for unit in units]
    selected_unit = st.selectbox("Selecione a unidade", options=unit_options)

    # Identificar o código da unidade selecionada
    if selected_unit:
        selected_unit_code = selected_unit.split(" - ")[0]

        if st.button("Realizar Previsão"):
            # Chamar função de previsão
            predictions = predict_totals_by_procedure(selected_unit_code)

            # Verificar se há dados retornados
            if isinstance(predictions, pd.DataFrame) and not predictions.empty:
                st.success("Previsão realizada com sucesso!")
                
                # Exibir tabela de resultados
                st.write("Resultados da Previsão:")
                st.dataframe(predictions)

                # Botão para download do CSV
                csv_data = predictions.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Baixar Previsão em CSV",
                    data=csv_data,
                    file_name=f"previsao_unidade_{selected_unit_code}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("Nenhum dado foi retornado para a previsão ou os dados estão vazios.")
