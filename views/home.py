import streamlit as st
from streamlit_lottie import st_lottie
import requests
import json
from forms.contact import agendar_reuniao  # Importando a função de cadastro


def showHome():
    # Adicionando Font Awesome para ícones e a nova fonte
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
        .title {
            text-align: center;
            font-size: 50px;
            font-family: 'Poppins', sans-serif;
        }
        .highlight {
            color: #D4AF37; /* Ouro Suave */
        }
        .subheader {
            text-align: center;
            font-size: 30px;
            font-family: 'Poppins', sans-serif;
            color: #002F6C; /* Azul Profundo */
        }
        .benefits {
            font-size: 20px;
            font-family: 'Poppins', sans-serif;
            margin: 20px 0;
            color: #4A4A4A; /* Cinza Escuro */
        }
        .icon {
            color: #C0C0C0; /* Prata Metálico */
            font-size: 24px;
            margin-right: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Título da página
    st.markdown(
        """
        <style>
        .highlight-gradient {
            background: linear-gradient(90deg, #002F6C, #FFFFFF); /* Gradiente Azul Forte para Branco */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"<h1 class='title'><span class='highlight-gradient'>Bem-vindo ao ALAN COACH</span></h1>",
        unsafe_allow_html=True
    )

    # Apresentação do Alan Coach
    st.write("O Alan Coach é sua fonte de inteligência emocional, pronto para guiá-lo em sua jornada de autodescoberta e desenvolvimento pessoal.")

    # Exibindo a imagem do Alan Coach
    st.image("./src/img/perfil.png", width=230)

    # Estilo CSS para gradiente
    st.markdown(
        """
        <style>
        .benefit-highlight {
            background: linear-gradient(90deg, #002F6C, #FFFFFF); /* Gradiente Azul Forte para Branco */
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- BENEFÍCIOS DO ALAN COACH ---
    st.subheader("Benefícios do Coaching com Alan", anchor=False)
    st.write(
        """
        <div class='benefits'>
            <i class="fas fa-lightbulb icon"></i> <span class='benefit-highlight'>Clareza nas Decisões:</span> <span class='benefit-highlight'>Aprenda a tomar decisões com confiança.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-clock icon"></i> <span class='benefit-highlight'>Gestão do Tempo:</span> <span class='benefit-highlight'>Descubra técnicas para gerenciar seu tempo de forma eficaz.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-comments icon"></i> <span class='benefit-highlight'>Comunicação Eficaz:</span> <span class='benefit-highlight'>Melhore suas habilidades de comunicação interpessoal.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-chart-line icon"></i> <span class='benefit-highlight'>Crescimento Pessoal:</span> <span class='benefit-highlight'>Desenvolva a confiança e alcance seus objetivos.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-users icon"></i> <span class='benefit-highlight'>Networking:</span> <span class='benefit-highlight'>Construa conexões significativas e colabore com outros.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-heart icon"></i> <span class='benefit-highlight'>Inteligência Emocional:</span> <span class='benefit-highlight'>Aprenda a gerenciar suas emoções e as dos outros.</span>
        </div>
        <div class='benefits'>
            <i class="fas fa-clipboard-list icon"></i> <span class='benefit-highlight'>Planejamento Estratégico:</span> <span class='benefit-highlight'>Elabore um plano de ação para o seu sucesso.</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- CHAMADA À AÇÃO ---
    st.write("\n")
    st.markdown(
        f"<h2 class='subheader'>Preparado para transformar sua vida?</h2>",
        unsafe_allow_html=True
    )
    st.write("Participe das sessões de coaching com Alan e inicie sua jornada de autodescoberta!")

    # --- BOTÃO DE INSCRIÇÃO ---
    if st.button("✉️ INSCREVA-SE AGORA"):
        # Chama a função de cadastro que contém o modal
        nome, whatsapp, email, endereco, message = agendar_reuniao()  # Modifique a função para retornar os valores

        # Verifica se os campos foram preenchidos
        if nome and whatsapp and email and endereco and message:
            # Se todos os campos foram preenchidos, exibe a mensagem de sucesso
            st.success("A sua mensagem foi enviada com sucesso! 🎉", icon="🚀")
        else:
            # Se algum campo estiver vazio, exibe uma mensagem de erro
            st.error("Por favor, preencha todos os campos antes de confirmar o agendamento.")
