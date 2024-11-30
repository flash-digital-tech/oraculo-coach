import asyncio

import streamlit as st
from transformers import AutoTokenizer
import base64
import pandas as pd
import io
from fastapi import FastAPI
import stripe
from util import carregar_arquivos
import os
import glob
from forms.contact import cadastrar_cliente, agendar_reuniao


import replicate
from langchain.llms import Replicate


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from key_config import API_KEY_STRIPE, URL_BASE
from decouple import config


app = FastAPI()



# --- Verifica se o token da API está nos segredos ---
if 'REPLICATE_API_TOKEN':
    replicate_api = config('REPLICATE_API_TOKEN')
else:
    # Se a chave não está nos segredos, define um valor padrão ou continua sem o token
    replicate_api = None

# Essa parte será executada se você precisar do token em algum lugar do seu código
if replicate_api is None:
    # Se você quiser fazer algo específico quando não há token, você pode gerenciar isso aqui
    # Por exemplo, configurar uma lógica padrão ou deixar o aplicativo continuar sem mostrar nenhuma mensagem:
    st.warning('Um token de API é necessário para determinados recursos.', icon='⚠️')


#######################################################################################################################

def showMembroAluno():

    is_in_registration = False
    is_in_scheduling = False

    # Função para verificar se a pergunta está relacionada a cadastro
    def is_health_question(prompt):
        keywords = ["cadastrar", "inscrição", "quero me cadastrar", "gostaria de me registrar",
                    "desejo me cadastrar", "quero fazer o cadastro", "quero me registrar", "quero me increver",
                    "desejo me registrar", "desejo me inscrever","eu quero me cadastrar", "eu desejo me cadastrar",
                    "eu desejo me registrar", "eu desejo me inscrever", "eu quero me registrar", "eu desejo me registrar",
                    "eu quero me inscrever"]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

    #Função que analisa desejo de agendar uma reunião
    def is_schedule_meeting_question(prompt):
        keywords = [
            "agendar reunião", "quero agendar uma reunião", "gostaria de agendar uma reunião",
            "desejo agendar uma reunião", "quero marcar uma reunião", "gostaria de marcar uma reunião",
            "desejo marcar uma reunião", "posso agendar uma reunião", "posso marcar uma reunião",
            "Eu gostaria de agendar uma reuniao", "eu quero agendar", "eu quero agendar uma reunião,",
            "quero reunião"
        ]
        return any(keyword.lower() in prompt.lower() for keyword in keywords)

    def obter_primeiro_nome():
        """Retorna o primeiro nome do aluno se disponível, caso contrário retorna 'Aluno'."""
        if 'name' in st.session_state and st.session_state.name:
            return st.session_state.name.split()[0]  # Retorna o primeiro nome
        else:
            return "Aluno"  # Retorna 'Aluno' se não houver nome

    # Carregar apenas a aba "Dados" do arquivo Excel
    #df_dados = pd.read_excel('./conhecimento/medicos_dados_e_links.xlsx', sheet_name='Dados')

    # Converter o DataFrame para um arquivo de texto, por exemplo, CSV
    #df_dados.to_csv('./conhecimento/medicos_dados_e_links.txt', sep=' ', index=False, header=True)

    # Se preferir usar tabulações como delimitador, substitua sep=' ' por sep='\t'
    # df_dados.to_csv('./conhecimento/CatalogoMed_Sudeste_Dados.txt', sep='\t', index=False, header=True)

    # Especifica o caminho para o arquivo .txt
    #caminho_arquivo = './conhecimento/medicos_dados_e_links.txt'

    # Abre o arquivo no modo de leitura ('r')
    #with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        # Lê todo o conteúdo do arquivo e armazena na variável conteudo
        #info = arquivo.read()

    # Exibe o conteúdo do arquivo
    #df_txt = info

    def ler_arquivos_txt(pasta):
        """
        Lê todos os arquivos .txt na pasta especificada e retorna uma lista com o conteúdo de cada arquivo.

        Args:
            pasta (str): O caminho da pasta onde os arquivos .txt estão localizados.

        Returns:
            list: Uma lista contendo o conteúdo de cada arquivo .txt.
        """
        conteudos = []  # Lista para armazenar o conteúdo dos arquivos

        # Cria o caminho para buscar arquivos .txt na pasta especificada
        caminho_arquivos = os.path.join(pasta, '*.txt')

        # Usa glob para encontrar todos os arquivos .txt na pasta
        arquivos_txt = glob.glob(caminho_arquivos)

        # Lê o conteúdo de cada arquivo .txt encontrado
        for arquivo in arquivos_txt:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()  # Lê o conteúdo do arquivo
                conteudos.append(conteudo)  # Adiciona o conteúdo à lista

        return conteudos  # Retorna a lista de conteúdos

    # Exemplo de uso da função
    pasta_conhecimento = './conhecimento'  # Caminho da pasta onde os arquivos .txt estão localizados
    conteudos_txt = ler_arquivos_txt(pasta_conhecimento)

    # Atualizando o system_prompt
    system_prompt = f'''
    Você é mentor e coach conhecido como Alan Coach, seu papel é ser aquele guia que caminha ao lado das pessoas. Não se trata só de 
    estratégias, mas de entender as histórias pessoasi, e as necessidades e o que faz o coração bater mais forte. Você 
    crio planos que fazem sentido para as pessoas, combinando sua experiência com uma abordagem prática e personalizada.
    Nos seus encontros de mentoria, trabalhará para:

    Trazer clareza: Ajudar você a entender onde está e para onde quer ir.
    Fortalecer sua confiança: Mostrando que o próximo passo está ao seu alcance.
    Transformar planos em ação: Sem complicações, com foco no que realmente importa.
    Meu objetivo é simples: te ajudar a conquistar seus sonhos e a se sentir no controle da sua vida, seja nos investimentos, nos negócios ou na sua própria evolução pessoal.
    
     **Cadastro e Agendamento:**
       - Se o usuário estiver com o status de cadastro {is_in_registration} ou agendamento {is_in_scheduling}, 
       informe que não enviará mais informações até que finalize o cadastro. Use uma resposta padrão que diga: 
       "Aguardo a finalização do seu cadastro para continuar."

    **Opção de Cadastro e Agendamento:**
       - Se o usuário enviar {is_health_question} ou {is_schedule_meeting_question}, responda que está aguardando o preenchimento completo do formulário. 
       - Mantenha a mesma resposta enquanto ele não finalizar o cadastro.
       - Se o status do cadastro estiver {is_in_scheduling} ou {is_in_registration} mantenha a mesma resposta enquanto
       ele não finalizar o cadastro.
    
    Você dará instrução através da FAC abaixo.
    
    FAC:
    Meus Serviços Oferecidos
    
    Mentoria Pessoal e Profissional
    Orientação para definição e alcance de metas.
    Desenvolvimento de habilidades e competências.
    Suporte em transições de carreira e projetos de vida.
    Coaching Individual e Grupal
    Coaching de performance (melhoria de resultados pessoais/profissionais).
    Coaching de vida (life coaching): equilíbrio entre vida pessoal e profissional.
    Planejamento estratégico para alcançar objetivos específicos.
    Psicanálise e Desenvolvimento Emocional
    Sessões para compreensão profunda de questões emocionais e padrões comportamentais.
    Análise de conflitos internos, traumas e relacionamentos interpessoais.
    Promoção de bem-estar mental e emocional.
    
    
    Problemas que Ajudo a Resolver
    
    Pessoal:
    Dificuldade em tomar decisões importantes.
    Sensação de estagnação ou insatisfação com a vida.
    Falta de clareza sobre propósito e direção.
    
    Profissional:
    Bloqueios em alcançar objetivos de carreira.
    Gestão de tempo e aumento de produtividade.
    Superação de desafios de liderança e comunicação.
    
    Emocional:
    Ansiedade, estresse ou sensação de sobrecarga emocional.
    Dificuldade em lidar com traumas ou padrões repetitivos.
    Problemas nos relacionamentos ou baixa autoestima.
    
    
    Como Eu Ajudo Meus Clientes:
    
    Ofereço um ambiente de escuta empática e sem julgamentos.
    Crio estratégias personalizadas com base em suas necessidades e objetivos.
    Combino técnicas de coaching prático e ferramentas de autoconhecimento profundo da psicanálise.
    Trabalho para desbloquear potenciais e promover mudanças transformadoras.
    
    
    Minha Promessa:
    
    "Ajudar você a alcançar equilíbrio, clareza e resultados concretos, transformando desafios em oportunidades para uma vida mais satisfatória e alinhada com seus valores e sonhos."
    
    
    
    1. Mentoria Individual
    Sessão única (1 hora): R$ 397,00
    Pacote mensal (4 sessões): R$ 1.370,00
    Programa de mentoria (3 meses): R$ 3.397,00
    
    
    2. Mentoria em Grupo
    
    Sessão única (por pessoa): R$ 150,00
    Programa mensal (4 encontros, por pessoa): R$ 450,00
    Turmas corporativas ou premium: R$ 6.000 a R$ 15.000 (valor total para o grupo, dependendo do tamanho e da proposta).
    
    
    3. Sessão de Coaching Individual
    
    Sessão única (1 a 1,5 hora): R$ 450,00
    Pacote de 10 sessões: R$ 4.000,00
    Programa intensivo (2 a 3 meses): R$ 5.500,00
    
    
    4. Treinamentos para Equipes de Alta Performance
    
    Treinamento curto (4 a 6 horas): R$ 5.000,00
    Treinamento completo (1 a 2 dias): R$ 12.000,00
    Programas contínuos (mensalidades): R$ 8.000 a R$ 14.000,00/mês (varia com a frequência e o escopo).
    
    
    5. Palestras de Inteligência Emocional
    
    Palestra de 1 hora: R$ 3.000,00
    Palestra de 2 horas: R$ 5.000,00
    Palestras corporativas para grandes eventos: R$ 9.000,00
    
    
    6. Workshops (Presencial ou Online)
    
    Workshop curto (3 a 4 horas): R$ 3.000 a R$ 7.000,00
    Workshop de dia inteiro: R$ 7.000 a R$ 15.000,00
    
    
    Workshops para empresas ou turmas específicas: R$ 10.000 a R$ 25.000
    
    Sugestões Adicionais
    Para mentoria e coaching premium, pode-se aplicar valores mais altos, como R$ 15.000,00 a R$ 25.000,00 para 
    programas completos, se for para oferecer resultados muito personalizados e comprovados.
    
    '''


    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-alan.jpg", "user": "./src/img/usuario.jpg"}


    st.markdown(
        """
        <style>
        .highlight-creme {
            background: linear-gradient(90deg, #f5f5dc, gold);  /* Gradiente do creme para dourado */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        .highlight-dourado {
            background: linear-gradient(90deg, gold, #f5f5dc);  /* Gradiente do dourado para creme */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Título da página
    st.markdown(
        f"<h1 class='title'>{st.session_state['name']} serei seu <span class='highlight-creme'>Coach</span> <span class='highlight-dourado'>de Inteligência Emocional!</span></h1>",
        unsafe_allow_html=True
    )

    st.markdown(
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

    st.sidebar.markdown("---")

    # Load and display sidebar image with glowing effect
    img_path = "./src/img/perfil.jpg"
    img_base64 = img_to_base64(img_path)
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
        unsafe_allow_html=True,
    )


    # Inicializar o modelo da Replicate
    llm = Replicate(
        model="meta/meta-llama-3.1-405b-instruct",
        api_token=replicate_api
    )

    # Store LLM-generated responses
    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{
            "role": "assistant", "content": '🌟 Bem-vindo ao Alan Coach! Estou aqui para te guiar na jornada de autodescoberta e transformação, rumo à sua melhor versão. Vamos juntos! 💪✨'}]

    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])


    def clear_chat_history():
        st.session_state.messages = [{
            "role": "assistant", "content": '🌟 Bem-vindo ao Alan Coach! Estou aqui para te guiar na jornada de autodescoberta e transformação, rumo à sua melhor versão. Vamos juntos! 💪✨'}]

    st.sidebar.markdown("---")

    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history, key='limpar_conversa')

    st.sidebar.markdown("Desenvolvido por [WILLIAM EUSTÁQUIO](https://www.instagram.com/flashdigital.tech/)")

    @st.cache_resource(show_spinner=False)
    def get_tokenizer():
        """Get a tokenizer to make sure we're not sending too much text
        text to the Model. Eventually we will replace this with ArcticTokenizer
        """
        return AutoTokenizer.from_pretrained("huggyllama/llama-7b")


    def get_num_tokens(prompt):
        """Get the number of tokens in a given prompt"""
        tokenizer = get_tokenizer()
        tokens = tokenizer.tokenize(prompt)
        return len(tokens)


    def check_safety(disable=False) -> bool:
        if disable:
            return True

        deployment = get_llamaguard_deployment()
        conversation_history = st.session_state.messages
        user_question = conversation_history[-1]  # pegar a última mensagem do usuário

        prediction = deployment.predictions.create(
            input=template)
        prediction.wait()
        output = prediction.output

        if output is not None and "unsafe" in output:
            return False
        else:
            return True

    # Function for generating Snowflake Arctic response
    def generate_arctic_response():

        prompt = []
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
            else:
                prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")

        prompt.append("<|im_start|>assistant")
        prompt.append("")
        prompt_str = "\n".join(prompt)


        for event in replicate.stream(
                "meta/meta-llama-3.1-405b-instruct",
                input={
                    "top_k": 0,
                    "top_p": 1,
                    "prompt": prompt_str,
                    "temperature": 0.1,
                    "system_prompt": system_prompt,
                    "length_penalty": 1,
                    "max_new_tokens": 8000,
                },
        ):
            yield str(event)


    # User-provided prompt
    if prompt := st.chat_input(disabled=not replicate_api):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="./src/img/usuario.JPG"):
            st.write(prompt)

    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-alan.jpg"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



