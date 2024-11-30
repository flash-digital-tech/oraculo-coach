import streamlit as st
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from httpx import AsyncClient
import pandas as pd
from configuracao import ASAAS_API_KEY, BASE_URL  # Importando as configurações necessárias
from typing import Optional
from datetime import datetime


app = FastAPI()


class LinkPagamento(BaseModel):
    name: str
    id: Optional[str]  # ID do link de pagamento, gerado pela API
    billingType: str
    chargeType: str
    endDate: str
    dueDateLimitDays: int
    status: str  # Status do link (ex: ACTIVE, INACTIVE)
    value: float  # Valor do pagamento
    description: Optional[str]  # Descrição do pagamento
    createdAt: datetime  # Data de criação do link
    dueDate: datetime  # Data de vencimento do link
    customerId: str  # ID do cliente associado ao link


async def criar_link_pagamento(link: LinkPagamento):
    async with AsyncClient() as client:
        response = await client.post(
            f'{BASE_URL}/paymentLinks',  # Endpoint para criar links de pagamento
            headers={'access_token': ASAAS_API_KEY},
            json=link.dict()
        )
        response.raise_for_status()
        return response.json()


async def fetch_payment_links():
    async with AsyncClient() as client:
        response = await client.get(
            f'{BASE_URL}/paymentLinks',
            headers={'access_token': ASAAS_API_KEY}
        )
        response.raise_for_status()  # Levanta um erro se a resposta não for bem-sucedida
        return response.json()["data"]  # Retorna apenas os dados dos links de pagamento


@app.post("/links-pagamento/")
async def create_payment_link(link: LinkPagamento):
    response = await criar_link_pagamento(link)
    return {"id": response["id"]}


@app.get("/links-pagamento/")
async def get_payment_links():
    try:
        links_pagamento = await fetch_payment_links()
        if links_pagamento:
            data = []
            for link in links_pagamento:
                data.append({
                    'Nome do Link': link['name'],
                    'Valor': link['value'],
                    'ID': link['id'],
                    'Forma de Pagamento': link['billingType'],
                    'chargeType': link['Forma de Cobrança'],
                    'dueDateLimitDate': link['Validade do Link'],
                    'endDate': link['Vencimento'],  # Usa .get() para evitar KeyError
                    'status': link.get('status', 'N/A')
                })
            df = pd.DataFrame(data)
            return df.to_dict("records")
        else:
            return {"message": "Nenhum link de pagamento encontrado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao carregar links de pagamento: {e}")


def show_pagamento_links():
    st.title("Flash Pagamentos")

    # Seção para criar um novo link de pagamento
    st.header("Criar Link de Pagamento")
    with st.form(key='create_link_pagamento'):
        name = st.text_input("Nome do Link")
        id = st.text_input("ID do Link")
        valor = st.number_input("Valor do Pagamento", min_value=0.0, format="%.2f")
        billingType = st.text_input("Forma de Pagamento")
        dueDate = st.date_input("Data de Vencimento")
        customerId = st.text_input("ID do Cliente")
        description = st.text_input("Descrição (opcional)")
        submit_button = st.form_submit_button("Criar Link de Pagamento")

        if submit_button:
            novo_link = LinkPagamento(value=valor, dueDate=dueDate.strftime("%Y-%m-%d"), customerId=customerId, description=description)
            import requests
            response = requests.post(f"{BASE_URL}/paymentLinks", headers={'access_token': ASAAS_API_KEY}, json=novo_link.dict())
            st.success(f"Link de pagamento criado com sucesso! ID: {response.json()['id']}")

    # Seção para listar links de pagamento
    st.header("Listar Links")
    if st.button("Carregar Links de Pagamento"):
        with st.spinner("Carregando lista de links de pagamento..."):
            import requests
            response = requests.get(f"{BASE_URL}/paymentLinks", headers={'access_token': ASAAS_API_KEY})
            links_pagamento = response.json()["data"]
            if links_pagamento:
                data = []
                for link in links_pagamento:
                    data.append({
                        'Nome do Link': link['name'],
                        'Valor': link['value'],
                        'ID': link['id'],
                        'Forma de Pagamento': link['billingType'],
                        'chargeType': link.get('Forma de Cobrança', 'N/A'),
                        'dueDateLimitDate': link.get('Validade', 'N/A'),
                        'endDate': link.get('Vencimento do Link', 'N/A'),  # Usa .get() para evitar KeyError
                        'status': link.get('status', 'N/A')
                    })
                df = pd.DataFrame(data)
                st.dataframe(df)  # Exibe a tabela de links de pagamento no Streamlit
            else:
                st.warning("Nenhum link de pagamento encontrado.")


