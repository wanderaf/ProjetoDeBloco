import streamlit as st
import introduction, data_summary, visualization, news, municipality_procedure, api_management, procedure_prediction, chat_llm, intelligent_report_page, tps_page

# Função principal para controle de páginas
def main():
    st.sidebar.title("Navegação")
    pages = {
        "Introdução": introduction.introduction_page,
        "Data Summary Report": data_summary.data_summary_page,
        "Visualização de Dados": visualization.data_visualization_page,
        "Últimas Notícias": news.latest_news_page,
        "Busca por Município e Procedimento": municipality_procedure.search_municipality_procedure_page,
        "Pesquisa e inclusão de dados": api_management.consulta_unidades_page,
        "Previsão por Procedimentos": procedure_prediction.previsao_procedimentos_page,
        "LLM Local": chat_llm.chat_with_llm_page,
        "Relatório com Gemini": intelligent_report_page.intelligent_report_page,
        "Acesso aos TP's":tps_page.tps_page
        
    }
    
    choice = st.sidebar.radio("Escolha a página", list(pages.keys()))
    pages[choice]()

# Executar a aplicação
if __name__ == '__main__':
    main()
    