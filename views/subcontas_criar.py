import streamlit as st
import asyncio
from fastapi import HTTPException
from pydantic import BaseModel
import httpx
from configuracao import BASE_URL, ASAAS_API_KEY  # Importando as constantes
from datetime import date


# Modelo para a Subconta
class Subaccount(BaseModel):
    name: str
    email: str
    cpfCnpj: str
    mobilePhone: str
    incomeValue: float
    fixedPhone: str = None
    birthDate: str
    companyType: str = None
    address: str  # Logradouro
    number: str  # Número do endereço
    complement: str = None  # Complemento do endereço
    province: str  # Estado
    city: str  # Cidade
    neighborhood: str  # Bairro
    postalCode: str  # CEP do endereço


async def criar_subconta(subconta: Subaccount):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'{BASE_URL}/accounts',
            headers={'access_token': ASAAS_API_KEY},
            json=subconta.dict()
        )
        response.raise_for_status()  # Levanta um erro se a resposta não for bem-sucedida
        return response.json()  # Retorna a resposta da API


# Interface do Streamlit
async def showSbconta():

    st.title("Sistema Flash Pagamentos")

    st.header("Criar Novo Parceiro")

    # Formulário para cadastro de subconta
    with st.form(key='form_subconta'):
        # Cria colunas para organizar os campos
        col1, col2 = st.columns(2)  # Colunas para Nome e Email/CPF/CNPJ
        col3, col4 = st.columns(2)  # Colunas para Contato e Endereço

        # Coleta de dados da subconta
        with col1:
            nome = st.text_input("Nome Parceiro")
            birthDate = st.date_input(label='Data de Nascimento:', min_value=date(1950, 1, 1), max_value=date(2030, 12, 31))

        with col2:
            email = st.text_input("E-mail")
            cpf_cnpj = st.text_input("CPF/CNPJ")

        with col3:
            mobile_phone = st.text_input("WhatsApp")
            fixed_phone = st.text_input("Telefone Fixo (opcional)")
            incomeValue = st.number_input("Sua renda")
            address = st.text_input("Endereço")
            number = st.text_input("Número")

        with col4:

            complement = st.text_input("Complemento do endereço (opcional):")
            neighborhood = st.text_input("Bairro:")
            city = st.text_input("Cidade")
            province = st.text_input("Estado:")
            postalCode = st.text_input("CEP:")

        # Botão para enviar os dados do formulário
        submit_button = st.form_submit_button("Cadastrar Parceiro")

        if submit_button:
            # Lógica para cadastrar o cliente (substitua pela sua lógica de cadastro)
            new_subaccount = Subaccount(
                name=nome,
                birthDate=birthDate,
                email=email,
                cpfCnpj=cpf_cnpj,
                mobilePhone=mobile_phone,
                fixedPhone=fixed_phone,
                incomeValue=incomeValue,
                address=address,
                number=number,
                complement=complement,
                province=province,
                city=city,
                neighborhood=neighborhood,
                postalCode=postalCode
            )
            st.success(f"Parceiro cadastrado com sucesso! Nome: {nome}")

            try:
                # Chamando a função criar_subconta para enviar os dados
                resultado = await criar_subconta(new_subaccount)
                st.write(resultado)
            except HTTPException as e:
                st.error(f"Erro ao criar novo parceiro: {e.detail}")

if __name__ == "__main__":
    asyncio.run(showSbconta())
