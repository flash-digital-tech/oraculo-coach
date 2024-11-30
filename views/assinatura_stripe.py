from fastapi import FastAPI, HTTPException, Depends
import stripe
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from decouple import config
import streamlit as st

# Configurações do Stripe
API_KEY_STRIPE = config('API_KEY_STRIPE')
stripe.api_key = API_KEY_STRIPE

# Inicialização do FastAPI
app = FastAPI()

# Configuração do CORS para permitir chamadas do Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir chamadas de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create_subscription")
async def create_subscription(customer_id: str, price_id: str):
    """Cria uma nova assinatura para um cliente usando a API do Stripe."""
    try:
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
        )
        return JSONResponse(content={"id": subscription.id}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/list_subscriptions")
async def list_subscriptions(customer_id: str):
    """Lista as assinaturas de um cliente usando a API do Stripe."""
    try:
        subscriptions = stripe.Subscription.list(customer=customer_id)
        return subscriptions
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Streamlit Interface ---
def showAssinatura():
    """Interface do Streamlit para criar e listar assinaturas."""
    st.title("Gerenciamento de Assinaturas com Stripe")

    # --- CRIAR ASSINATURA ---
    st.header("Criar Nova Assinatura")
    with st.form(key='create_assinatura'):
        customer_id = st.text_input("ID do Cliente")
        price_id = st.text_input("ID do Preço")
        submit_button = st.form_submit_button("Criar Assinatura")

        if submit_button:
            response = st.experimental_get_query_params()
            if customer_id and price_id:
                try:
                    response = requests.post(f"http://localhost:8000/create_subscription?customer_id={customer_id}&price_id={price_id}")
                    if response.status_code == 201:
                        st.success(f"Assinatura criada com sucesso! ID: {response.json()['id']}")
                except Exception as e:
                    st.error(f"Erro ao criar assinatura: {e}")

    # --- LISTAR ASSINATURAS ---
    st.header("Listar Assinaturas")
    customer_id_listar = st.text_input("ID do Cliente para listar assinaturas")
    if st.button("Carregar Assinaturas"):
        if customer_id_listar:
            try:
                response = requests.get(f"http://localhost:8000/list_subscriptions?customer_id={customer_id_listar}")
                subscriptions = response.json()
                if subscriptions and len(subscriptions['data']) > 0:
                    data = [{
                        'ID': sub['id'],
                        'Status': sub['status'],
                        'Data de Criação': sub['created'],
                        'Próximo Vencimento': sub['current_period_end']
                    } for sub in subscriptions['data']]
                    st.dataframe(data)  # Exibe a tabela de assinaturas no Streamlit
                else:
                    st.warning("Nenhuma assinatura encontrada.")
            except Exception as e:
                st.error(f"Erro ao listar assinaturas: {e}")
        else:
            st.warning("Por favor, insira o ID do cliente.")

# Para executar a função showAssinatura quando o script for chamado
if __name__ == "__main__":
    import threading

    # Executar o FastAPI em uma thread separada
    import uvicorn
    threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "0.0.0.0", "port": 8000}).start()

    # Iniciar o Streamlit
    showAssinatura()
