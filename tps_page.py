import os
import streamlit as st
import fitz  # PyMuPDF

def render_pdf_as_images(pdf_path):
    """
    Renderiza as páginas do PDF como imagens para exibição no Streamlit.
    Args:
        pdf_path (str): Caminho para o arquivo PDF.
    Returns:
        list: Lista de objetos de imagem para exibição.
    """
    images = []
    try:
        with fitz.open(pdf_path) as pdf:
            for page_number in range(len(pdf)):
                page = pdf[page_number]
                pix = page.get_pixmap()
                images.append(pix.tobytes())
    except Exception as e:
        st.error(f"Erro ao renderizar o PDF: {e}")
    return images

def tps_page():
    """
    Página para listar e visualizar os TPs (arquivos em PDF).
    """
    st.title("Trabalhos Práticos (TPs)")
    st.write("Selecione um TP da lista para visualizá-lo diretamente na página e baixar, se necessário.")

    # Caminho da pasta onde estão os arquivos
    tp_folder = r"C:\Users\wande\OneDrive\INFNET\7. 6º Semestre\Projeto de Bloco\TPs"

    # Verificar se a pasta existe
    if not os.path.exists(tp_folder):
        st.error(f"A pasta '{tp_folder}' não existe. Verifique o caminho.")
        return

    # Listar arquivos PDF na pasta
    tp_files = [f for f in os.listdir(tp_folder) if f.endswith(".pdf")]

    if tp_files:
        # Layout: filtro acima e PDF abaixo
        selected_tp = st.selectbox("Selecione um TP:", tp_files, key="tp_selector")

        if selected_tp:
            # Caminho completo do arquivo selecionado
            file_path = os.path.join(tp_folder, selected_tp)

            # Botão para download do arquivo
            with open(file_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Baixar Documento",
                    data=pdf_bytes,
                    file_name=selected_tp,
                    mime="application/pdf",
                )

            # Renderizar e exibir o PDF como imagens
            st.write(f"**Visualizando:** {selected_tp}")
            pdf_images = render_pdf_as_images(file_path)
            if pdf_images:
                for img in pdf_images:
                    # Exibir a imagem em largura total
                    st.image(img, use_column_width=True)
            else:
                st.warning("O PDF não contém páginas ou não pôde ser processado.")
    else:
        st.warning("Nenhum arquivo PDF foi encontrado na pasta especificada.")
