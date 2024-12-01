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
from decouple import config


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




################################################# ENVIO DE E-MAIL ####################################################
############################################# PARA CONFIRMAÇÃO DE DADOS ##############################################

# Função para enviar o e-mail
def enviar_email(destinatario, assunto, corpo):
    remetente = "mensagem@flashdigital.tech"  # Insira seu endereço de e-mail
    senha = "sua_senha"  # Insira sua senha de e-mail

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('mail.flashdigital.tech', 587)
        server.starttls()
        server.login(remetente, senha)
        server.sendmail(remetente, destinatario, msg.as_string())
        server.quit()
        st.success("E-mail enviado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao enviar e-mail: {e}")

    # Enviando o e-mail ao pressionar o botão de confirmação
    if st.button("DADOS CONFIRMADO"):
        # Obter os dados salvos em st.session_state
        nome = st.session_state.user_data["name"]
        whatsapp = st.session_state.user_data["whatsapp"]
        email = st.session_state.user_data["email"]

        # Construindo o corpo do e-mail
        corpo_email = f"""
        Olá {nome},

        Segue a confirmação dos dados:
        - Nome: {nome}
        - WhatsApp: {whatsapp}
        - E-mail: {email}
        - Agendamento : {dias} e {turnos}

        Obrigado pela confirmação!
        """

        # Enviando o e-mail
        enviar_email(email, "Confirmação de dados", corpo_email)


#######################################################################################################################

def showMestre():

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

    processar_docs = carregar_arquivos()

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

    system_prompt = f'''
    Você é um mentor, coach, psicanalista e terapeuta. Sua missão é responder de forma humanizada, clara e empática, utilizando conceitos e uma linguagem pertinentes ao universo do desenvolvimento pessoal, ressignificação emocional, congruência, autoconhecimento, inteligência emocional, e superação de traumas.

    Sempre priorize uma comunicação acolhedora, com termos acessíveis que facilitem a compreensão, mas que ao mesmo tempo reflitam a profundidade e o profissionalismo que essas áreas exigem. Suas respostas devem ser voltadas para auxiliar as pessoas a:
    
    Resgatar sua autoestima e confiança.
    Superar bloqueios emocionais como traumas, ansiedade, depressão e sentimento de culpa.
    Adotar práticas de autocompaixão, autocuidado e autorresponsabilidade.
    Encontrar equilíbrio emocional e clareza mental para tomar decisões congruentes com seus valores e objetivos.
    Ressignificar experiências negativas para que tragam aprendizado e crescimento.

    Trazer clareza: Ajudar você a entender onde está e para onde quer ir.
    Fortalecer sua confiança: Mostrando que o próximo passo está ao seu alcance.
    Transformar planos em ação: Sem complicações, com foco no que realmente importa.
    Meu objetivo é simples: te ajudar a conquistar seus sonhos e a se sentir no controle da sua vida, seja nos 
    investimentos, nos negócios ou na sua própria evolução pessoal.
    
    **Status de Cadastro e Agendamento:**
       - Se o usuário estiver com o status de cadastro {is_in_registration} ou agendamento {is_in_scheduling}, 
       informe que não enviará mais informações até que finalize o cadastro. Use uma resposta padrão que diga: 
       "Aguardo a finalização do seu cadastro para continuar."

    **Opção de Cadastro e Agendamento:**
       - Se o usuário enviar {is_health_question} ou {is_schedule_meeting_question}, responda que está 
       aguardando o preenchimento completo do formulário. 
       - Mantenha a mesma resposta enquanto ele não finalizar o cadastro.
       - Se o status do cadastro estiver {is_in_scheduling} ou {is_in_registration} mantenha a mesma resposta enquanto
       ele não finalizar o cadastro.
       - Não envie nenhuma resposta se o usuário estiver em {is_in_scheduling} ou {is_in_registration}.
       
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

    # Função para gerar o PDF
    def create_pdf(messages):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for message in messages:
            role = message["role"].capitalize()
            content = message["content"]
            pdf.cell(200, 10, txt=f"{role}: {content}", ln=True)

        return pdf.output(dest='S').encode('latin1')


    # Função para gerar o Excel
    def create_excel(messages):
        df = pd.DataFrame(messages)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer.getvalue()


    # Set assistant icon to Snowflake logo
    icons = {"assistant": "./src/img/perfil-alan.jpg", "user": "./src/img/usuario.jpg"}


    # Replicate Credentials
    with st.sidebar:
        st.markdown(
            """
            <h1 style='text-align: center;'>ALAN COACH</h1>
            """,
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
        st.session_state.messages = [{"role": "assistant", "content": '🌟 Bem-vindo ao Alan Coach! Estou aqui para te guiar na jornada de autodescoberta e transformação, rumo à sua melhor versão. Vamos juntos! 💪✨'}]

    st.sidebar.markdown("---")
    st.sidebar.button('LIMPAR CONVERSA', on_click=clear_chat_history)

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
        if is_in_registration or is_in_scheduling:
            return "Por favor, complete o formulário de cadastro antes de continuar."

        prompt = []
        for dict_message in st.session_state.messages:
            if dict_message["role"] == "user":
                prompt.append("<|im_start|>user\n" + dict_message["content"] + "<|im_end|>")
            else:
                prompt.append("<|im_start|>assistant\n" + dict_message["content"] + "<|im_end|>")

        prompt.append("<|im_start|>assistant")
        prompt.append("")
        prompt_str = "\n".join(prompt)



        # Verifica se o usuário deseja se cadastrar
        if "quero ser parceiro" in prompt_str.lower() or "desejo criar uma conta de parceiro" in prompt_str.lower() or "conta de parceiro" in prompt_str.lower() or "quero me tornar parceiro" in prompt_str.lower() or "como faço para ser parceiro" in prompt_str.lower() or "quero ter uma conta de parceiro" in prompt_str.lower() or "quero ser um parceiro" in prompt_str.lower():
            st.write("Para se tornar um parceiro na ORÁCULO IA e começar a ter ganhos extraordinários clique no botão abaixo.")
            if st.button("QUERO SER PARCEIRO"):
                showSbconta()
                st.stop()


        elif get_num_tokens(prompt_str) >= 8000:  # padrão3072
            st.error(
                "Poxa, você já atingiu seu limite de demostração, mas pode ficar tranquilo. Clique no botão abaixo para "
                "pedir seu acesso.")
            st.button('PEDIR ACESSO', on_click=clear_chat_history, key="clear_chat_history")
            excel_bytes = create_excel(st.session_state.messages)
            pdf_bytes = create_pdf(st.session_state.messages)
            formato_arquivo = st.selectbox("Escolha como deseja baixar sua conversa:", ["PDF", "Excel"])
            if formato_arquivo == "PDF":
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name="conversa.pdf",
                    mime="application/pdf",
                )
            else:
                st.download_button(
                    label="Baixar Excel",
                    data=excel_bytes,
                    file_name="conversa.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            st.stop()


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
        with st.chat_message("user", avatar="./src/img/usuario.jpg"):
            st.write(prompt)


    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant", avatar="./src/img/perfil-alan.jpg"):
            response = generate_arctic_response()
            full_response = st.write_stream(response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)



