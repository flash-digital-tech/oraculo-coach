import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import json
import xml.etree.ElementTree as ET
from docx import Document
import os
from fpdf import FPDF



# Função para ler arquivos XLSX e transformar em TXT
def read_xlsx(file):
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'

    # Abre o arquivo XLSX e lê todas as abas
    with pd.ExcelFile(file) as xls:
        with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # Escreve o nome da aba no arquivo TXT
                txt_file.write(f'--- Aba: {sheet_name} ---\n')
                # Salva o DataFrame como texto, usando tabulação como delimitador
                df.to_csv(txt_file, sep='\t', index=False, header=True)  # Inclui cabeçalho
                txt_file.write('\n')  # Adiciona uma nova linha após cada aba

    # Lê o arquivo TXT e retorna seu conteúdo
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        info = arquivo.read()
    return info

# Função para ler arquivos PDF e transformar em TXT
def read_pdf(file):
    text = ""
    # Lê o arquivo PDF
    pdf_reader = PdfReader(file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    # Salva o texto extraído como um arquivo TXT
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    # Retorna o texto extraído
    return text

# Função para ler arquivos JSON e transformar em TXT
def read_json(file):
    # Lê o arquivo JSON
    content = json.load(file)
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    # Salva o conteúdo JSON como um arquivo TXT
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(json.dumps(content, indent=4))  # Formata o conteúdo JSON com indentação
    # Retorna o conteúdo lido do JSON
    return content

# Função para ler arquivos XML e transformar em TXT
def read_xml(file):
    # Lê o arquivo XML
    tree = ET.parse(file)
    root = tree.getroot()
    # Converte o conteúdo XML em uma string
    xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    # Salva o conteúdo XML como um arquivo TXT
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(xml_str)
    # Retorna a string XML
    return xml_str

# Função para ler arquivos HTML e transformar em TXT
def read_html(file):
    # Lê o conteúdo do arquivo HTML e decodifica como UTF-8
    html_content = file.read().decode("utf-8")
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    # Salva o conteúdo HTML como um arquivo TXT
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(html_content)
    # Retorna o conteúdo HTML
    return html_content

# Função para ler arquivos DOCX e transformar em TXT
def read_docx(file):
    # Lê o arquivo DOCX
    doc = Document(file)
    text = ""
    # Extrai texto de cada parágrafo
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"  # Adiciona uma nova linha após cada parágrafo
    # Define o caminho para o arquivo TXT
    caminho_arquivo = f'./conhecimento/{os.path.splitext(os.path.basename(file.name))[0]}.txt'
    # Salva o texto extraído como um arquivo TXT
    with open(caminho_arquivo, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    # Retorna o texto extraído
    return text

# Função para ler arquivos TXT
def read_txt(file):
    return file.read().decode("utf-8")


def carregar_arquivos():
    # Sidebar para carregamento de arquivos
    st.sidebar.header("Carregar Documentos")
    # Apresentando o botão para carregar os documentos
    with st.sidebar:
        st.subheader('Clique no botão abaixo para carregar seus dados e fazer uma análise com o Doctor Med:')
        # Carregar múltiplos arquivos
        uploaded_files = st.sidebar.file_uploader("Coloque seu arquivo aqui:", type=["xlsx", "pdf", "xml", "json", "html", "htm", "doc", "docx", "txt", "xls"], accept_multiple_files=True)

        if st.button('CARREGAR'):
            conteudos = []  # Lista para armazenar o conteúdo dos arquivos
            for file in uploaded_files:
                with st.spinner("Processing"):
                    st.write(f"**Arquivo carregado :** {file.name}")

                    if file.type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel"]:
                        conteudo = read_xlsx(file)
                        conteudos.append(conteudo)

                    elif file.type == "application/pdf":
                        conteudo = read_pdf(file)
                        conteudos.append(conteudo)

                    elif file.type == "application/json":
                        conteudo = read_json(file)
                        conteudos.append(json.dumps(conteudo, indent=4))  # Formata o JSON

                    elif file.type in ["application/xml", "text/xml"]:
                        conteudo = read_xml(file)
                        conteudos.append(conteudo)

                    elif file.type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                        conteudo = read_docx(file)
                        conteudos.append(conteudo)

                    elif file.type == "text/plain":
                        # Lendo arquivos de texto (.txt)
                        caminho_arquivo = file.name  # Usando o nome do arquivo para leitura
                        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                            conteudo = arquivo.read()  # Lê o conteúdo do arquivo
                            conteudos.append(conteudo)

                    elif file.type in ["text/html", "text/htm"]:
                        conteudo = read_html(file)
                        conteudos.append(conteudo)

            return conteudos  # Retorna a lista de conteúdos


# Função para salvar a imagem no servidor
def save_uploaded_file(uploaded_file, user_type):
    """Salva um arquivo de imagem no diretório correspondente ao tipo de usuário.

    Args:
        uploaded_file: O arquivo de imagem carregado.
        user_type (str): O tipo de usuário (admin, parceiro, colaborador ou cliente).

    Returns:
        str: O caminho do arquivo salvo.
    """

    # Define o diretório base onde as imagens serão salvas
    base_dir = "MEDIA"

    # Mapeia o tipo de usuário para o diretório correspondente
    user_dirs = {
        "Admin": "admin",
        "Parceiro": "parceiro",
        "Colaborador": "colaborador",
        "Cliente": "cliente"
    }

    # Verifica se o tipo de usuário é válido
    if user_type not in user_dirs:
        raise ValueError(f"Tipo de usuário inválido: {user_type}")

    # Cria o caminho final onde a imagem será salva
    user_dir = os.path.join(base_dir, user_dirs[user_type])

    # Cria o diretório se não existir
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Salva o arquivo na pasta definida
    file_path = os.path.join(user_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


# Função para gerar o PDF
def create_pdf(messages):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    role = message["role"].capitalize()
    content = message["content"]
    pdf.cell(200, 10, txt=f"{role}: {content}", ln=True)
    pdf_bytes = create_pdf(st.session_state.messages)
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name="conversa.pdf",
        mime="application/pdf",
    )

    return pdf.output(dest='S').encode('latin1')


# Função para gerar o Excel
def create_excel(messages):
    df = pd.DataFrame(messages)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="Baixar Excel",
        data=excel_bytes,
        file_name="conversa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.stop()

    return buffer.getvalue()


