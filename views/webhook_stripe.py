import streamlit as st
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import requests
import pandas as pd
#import logging
import stripe
from key_config import API_KEY_STRIPE, URL_BASE, STRIPE_WEBHOOK_SECRET


# Configurações do Stripe
stripe.api_key = API_KEY_STRIPE


# Configuração do logging
#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logger = logging.getLogger(__name__)

# Inicialização do FastAPI
app = FastAPI()


# Modelo para Webhook
class Webhook(BaseModel):
    id: Optional[int]  # ID do webhook, gerado automaticamente
    name: str          # Nome do webhook
    url: str           # URL onde o webhook será enviado
    event: str         # Evento que irá acionar o webhook
    enabled: bool      # Status do webhook (ativo ou inativo)



@app.post("/webhooks/", response_model=Webhook)
def create_webhook(webhook: Webhook):
    global next_id
    webhook.id = next_id
    webhooks_db.append(webhook)
    next_id += 1
    return webhook


@app.get("/webhooks/", response_model=List[Webhook])
def list_webhooks():
    return webhooks_db


@app.get("/webhooks/{webhook_id}", response_model=Webhook)
def get_webhook(webhook_id: int):
    for webhook in webhooks_db:
        if webhook.id == webhook_id:
            return webhook
    raise HTTPException(status_code=404, detail="Webhook not found")


@app.delete("/webhooks/{webhook_id}")
def delete_webhook(webhook_id: int):
    global webhooks_db
    webhooks_db = [webhook for webhook in webhooks_db if webhook.id != webhook_id]
    return {"message": "Webhook deleted successfully"}


# Função para mostrar webhooks no Streamlit
def showWebhook():
    st.title("Gerenciar Webhooks")

    # Seção para criar um novo webhook
    st.header("Criar Webhook")
    with st.form(key='create_webhook'):
        name = st.text_input("Nome do Webhook")  # Adicionado campo para nome do webhook
        url = st.text_input("URL do Webhook")
        # Usando selectbox para escolher o evento
        event_options = [
            "payment_intent.succeeded",
            "payment_intent.payment_failed",
            "charge.succeeded",
            "charge.failed",
            "customer.created",
            "customer.updated",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            # Adicione outros eventos conforme necessário
        ]

        event = st.multiselect("Eventos que Ativa: ", event_options)
        enabled = st.checkbox("Ativo", value=True)
        submit_button = st.form_submit_button("Criar Webhook")

        if submit_button:
            webhook_data = {
                "name": name,  # Incluindo o nome na criação do webhook
                "url": url,
                "event": event,
                "enabled": enabled
            }
            response = requests.post("http://localhost:8000/webhooks/", json=webhook_data)  # Ajuste o BASE_URL conforme necessário
            if response.status_code == 200:
                st.success(f"Webhook criado com sucesso! ID: {response.json()['id']}")
            else:
                st.error("Erro ao criar webhook.")

    # Seção para listar webhooks
    st.header("Listar Webhooks")
    if st.button("Carregar Webhooks"):
        with st.spinner("Carregando lista de webhooks..."):
            response = requests.get("http://localhost:8000/webhooks/")  # Ajuste o BASE_URL conforme necessário
            if response.status_code == 200:
                webhooks = response.json()
                if webhooks:
                    df = pd.DataFrame(webhooks)
                    st.dataframe(df)  # Exibe a tabela de webhooks no Streamlit
                else:
                    st.warning("Nenhum webhook encontrado.")
            else:
                st.error("Erro ao carregar webhooks.")

