from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import stripe
import requests
import streamlit as st
from key_config import API_KEY_STRIPE, URL_BASE, STRIPE_WEBHOOK_SECRET


app = FastAPI()


# Configurações do Stripe
stripe.api_key = API_KEY_STRIPE

@app.post("/create-checkout-session/")
async def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {
                        "name": "ACESSO: Oráculo Med",
                    },
                    "unit_amount": 500,  # Preço em centavos (ex: 500 = $5.00)
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url="http://localhost:8501/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:8501/cancel",
    )
    return {"id": session.id}

@app.get("/success")
async def success(session_id: str):
    # Aqui você pode verificar o status do pagamento
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status == "paid":
        return {"message": "Pagamento realizado com sucesso!"}
    else:
        raise HTTPException(status_code=400, detail="Pagamento não confirmado.")

@app.get("/cancel")
async def cancel():
    return {"message": "Pagamento cancelado."}


# Função para criar a sessão de checkout
def create_checkout_session():
    response = requests.post("http://localhost:8000/create-checkout-session/")
    if response.status_code == 200:
        session_id = response.json().get("id")
        return session_id
    else:
        st.error("Erro ao criar a sessão de checkout.")
        return None

# Função para verificar o status do pagamento
def check_payment_status(session_id):
    response = requests.get(f"http://localhost:8000/success?session_id={session_id}")
    if response.status_code == 200:
        return True
    else:
        return False

# Menu principal
def show_checkout():
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Escolha uma opção:", ["Home", "Checkout", "Chat"])

    if menu == "Home":
        st.title("Bem-vindo ao Sistema de Checkout")
        st.write("Aqui você pode gerenciar seus produtos e realizar pagamentos.")

    elif menu == "Checkout":
        st.title("Checkout")
        if st.button("Iniciar Checkout"):
            session_id = create_checkout_session()
            if session_id:
                st.write("Redirecionando para o Stripe...")
                st.markdown(f"[Clique aqui para pagar](https://checkout.stripe.com/pay/{session_id})")

    elif menu == "Chat":
        st.title("Chat Med")
        session_id = st.text_input("Insira o ID da sessão de checkout:")
        if st.button("Verificar Pagamento"):
            if check_payment_status(session_id):
                st.success("Pagamento confirmado! Acesso ao Chat Med concedido.")
                # Aqui você pode incluir a lógica para carregar a página mestre.py
            else:
                st.error("Pagamento não confirmado. Acesso negado.")
