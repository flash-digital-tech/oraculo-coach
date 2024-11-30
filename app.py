import streamlit as st
from streamlit_authenticator import Authenticate
import yaml
import time
import asyncio
from views.home import showHome
from views.mestre import showMestre
from views.membro_aluno import showMembroAluno
from views.financeiro import showFinanceiro
from views.cliente_criar import showCliente
from views.link_pagamento import show_pagamento_links
from views.webhook_stripe import showWebhook
from views.assinatura_stripe import showAssinatura
from views.parceiro_stripe import showParceiro
from views.split import showSplitPayment
import base64


# --- LOAD CONFIGURATION ---
try:
    with open("config.yaml") as file:
        config = yaml.safe_load(file)
except FileNotFoundError:
    st.error("Arquivo de configuração não encontrado.")
    st.stop()
except yaml.YAMLError as e:
    st.error(f"Erro ao carregar o arquivo de configuração: {e}")
    st.stop()


# --- AUTHENTICATION SETUP ---
credentials = {
    'usernames': {user['username']: {
        'name': user['name'],
        'password': user['password'],
        'email': user['email'],
        'role': user['role'],
        'whatsapp': user.get('whatsapp', ''),
        'endereco': user.get('endereco', ''),
        'cep': user.get('cep', ''),
        'bairro': user.get('bairro', ''),
        'cidade': user.get('cidade', ''),
        'cpf_cnpj': user.get('cpf_cnpj', ''),
        'created_at': user.get('created_at', '')
    } for user in config['credentials']['users']}
}

authenticator = Authenticate(
    credentials=credentials,
    cookie_name=config['cookie']['name'],
    key=config['cookie']['key'],
    cookie_expiry_days=config['cookie']['expiry_days']
)


# --- PAGE SETUP ---
authenticator.login()

if 'authentication_status' in st.session_state and st.session_state['authentication_status']:
    user_email = next(user['email'] for user in config['credentials']['users'] if user['username'] == st.session_state['username'])
    authenticator.logout('SAIR', 'sidebar')
    st.sidebar.markdown(
    f"<h1 style='color: #FFFFFF; font-size: 24px;'>🎉 Seja bem-vindo(a), <span style='font-weight: bold;'>{st.session_state['name']}</span>!!! 🎉</h1>",unsafe_allow_html=True
    )

    st.sidebar.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #002F6C,    /* Azul Profundo */
                0 0 10px #C0C0C0,   /* Prata Metálico */
                0 0 15px #D4AF37,   /* Ouro Suave */
                0 0 20px #4A4A4A,   /* Cinza Escuro */
                0 0 25px #FFFFFF,    /* Branco */
                0 0 30px #002F6C,   /* Azul Profundo */
                0 0 35px #C0C0C0;    /* Prata Metálico */
            position: relative;
            z-index: -1;
            border-radius: 30px;  /* Cantos arredondados */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to convert image to base64
    def img_to_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Load and display sidebar image with glowing effect
    img_path = "./src/img/logo-alan.jpg"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.title("MENU")
    st.sidebar.markdown("---")

    if 'username' in st.session_state:
        user_role = next((user['role'] for user in config['credentials']['users'] if user['username'] == st.session_state['username']), None)
        if user_role:
            with st.spinner('Acessando...'):
                time.sleep(2)  # Simula uma operação demorada

        if user_role is None:
            with st.spinner('Saindo...'):
                time.sleep(1)  # Simula uma operação demorada
    else:
        st.error("Usuário não está autenticado.")
        st.stop()

    permissao_usuario = {
        "admin": ["Home", "ALAN COACH", "Membro/Aluno", "Cadastrar Cliente","Criar Parceiro", "Financeiro", "Link de Pagamento", \
                  "Webhook","Assinaturas","Split de Pagamentos",],
        "parceiro": ["Home", "ALAN COACH", "Membro/Aluno", "Cadastrar Cliente","Assinaturas", "Link de Pagamento"],
        "cliente": ["Home", "ALAN COACH"],
    }

    paginas_permitidas = permissao_usuario.get(user_role, [])

    pages = {
        "Home": showHome,
        "ALAN COACH": showMestre,
        "Membro/Aluno": showMembroAluno,
        "Cadastrar Cliente": showCliente,
        "Criar Parceiro": showParceiro,
        "Assinaturas": showAssinatura,
        "Financeiro": showFinanceiro,
        "Split de Pagamentos": showSplitPayment,
        "Link de Pagamento": show_pagamento_links,
        "Webhook": showWebhook,
    }

    allowed_pages = {key: pages[key] for key in paginas_permitidas if key in pages}

    navigation_structure = {
        "MENU": list(allowed_pages.keys())
    }

    selected_page = st.sidebar.radio("PÁGINAS:", navigation_structure["MENU"])

    # Executando a função da página selecionada
    async def main():
        if selected_page in allowed_pages:
            allowed_pages[selected_page]()  # Chama a função correspondente

    if __name__ == '__main__':
        asyncio.run(main())

elif st.session_state["authentication_status"] is False:
    st.error("Usuário/Senha inválido")
elif st.session_state["authentication_status"] is None:
    st.warning("Por Favor, utilize seu usuário e senha!")
