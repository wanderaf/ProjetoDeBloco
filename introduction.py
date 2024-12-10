import streamlit as st

# Página de introdução
def introduction_page():
    # Carregar a imagem do SUS
    st.image("docs/img/sus.webp", use_column_width=True)
    
    # Texto introdutório
    st.title("Bem-vindo ao Projeto de Visualização de Dados do SUS")
    st.write("""
    Este projeto utiliza dados oriundos do FTP do SUS e tem como objetivo auxiliar os gestores públicos na elaboração 
    de políticas públicas de saúde, bem como ajudar a identificar onde buscar atendimento. 
    Através dessa plataforma, é possível visualizar e analisar dados de saúde de forma acessível e interativa.
    """)

    # Seção de links úteis
    st.header("Links Úteis")
    st.markdown("""
    - [FTP do SUS (Dados)](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados/): Local para busca dos dados.
    - [FTP do SUS (Manual)](ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/): Local com informações técnicas dos arquivos utilizados.
    - [DATASUS](https://datasus.saude.gov.br/transferencia-de-arquivos/): Local para pesquisa dos dados sem necessidade de utilização do FTP.
    """)