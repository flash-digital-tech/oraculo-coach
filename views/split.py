import streamlit as st
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from key_config import API_KEY_STRIPE, URL_BASE

app = FastAPI()

# Modelo de split de pagamento
class SplitPaymentCreate(BaseModel):
    valor_total: float  # Valor total da transação
    percentual_vendedor: float  # Percentual que o vendedor deve receber
    vendedor_id: str  # ID do vendedor

class SplitPaymentResponse(BaseModel):
    id: str
    valor_total: float
    vendedor_id: str
    valor_vendedor: float
    valor_loja: float

async def criar_split_payments(split: SplitPaymentCreate):
    url = f"{URL_BASE}/transfers"
    headers = {
        "Authorization": f"Bearer {API_KEY_STRIPE}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    valor_vendedor = split.valor_total * (split.percentual_vendedor / 100)
    valor_loja = split.valor_total - valor_vendedor

    data = {
        "amount": int(split.valor_total * 100),  # Valor em centavos
        "currency": "brl",
        "destination": split.vendedor_id,
        "transfer_group": "group_1",
        "description": f"Pagamento de {valor_loja} para a loja e {valor_vendedor} para o vendedor."
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()

@app.post("/split", response_model=SplitPaymentResponse)
async def api_create_split_payment(split: SplitPaymentCreate):
    try:
        split_payment = await criar_split_payments(split)
        return SplitPaymentResponse(
            id=split_payment['id'],
            valor_total=split.valor_total,
            vendedor_id=split.vendedor_id,
            valor_vendedor=valor_vendedor,
            valor_loja=valor_loja
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Streamlit Interface
def showSplitPayment():
    st.title("Sistema de Splits de Pagamento")

    st.header("Criar Novo Split de Pagamento")

    # Inicializa os campos no session_state se não existirem
    if 'valor_total' not in st.session_state:
        st.session_state.valor_total = 0.0
    if 'percentual_vendedor' not in st.session_state:
        st.session_state.percentual_vendedor = 0.0
    if 'vendedor_id' not in st.session_state:
        st.session_state.vendedor_id = ""

    # Formulário para cadastro de split
    with st.form(key='form_split'):
        st.session_state.valor_total = st.number_input("Valor Total:", min_value=0.0, value=st.session_state.valor_total)
        st.session_state.percentual_vendedor = st.number_input("Percentual do Vendedor (%):", min_value=0.0, max_value=100.0, value=st.session_state.percentual_vendedor)
        st.session_state.vendedor_id = st.text_input("ID do Vendedor:", value=st.session_state.vendedor_id)

        # Botão para enviar os dados do formulário
        submit_button = st.form_submit_button("CRIAR SPLIT!")

        if submit_button:
            split = SplitPaymentCreate(
                valor_total=st.session_state.valor_total,
                percentual_vendedor=st.session_state.percentual_vendedor,
                vendedor_id=st.session_state.vendedor_id
            )
            try:
                # Chame a função de criação de split (sem await)
                resultado = api_create_split_payment(split)  # Chame a função de forma síncrona
                st.success(f"Split criado com sucesso! ID: {resultado.id}")

                # Limpa os campos do formulário
                st.session_state.valor_total = 0.0
                st.session_state.percentual_vendedor = 0.0
                st.session_state.vendedor_id = ""

            except Exception as e:
                st.error(f"Erro ao criar split: {e}")

    # Seção para listar splits
    st.header("Listar Splits de Pagamento")
    limit = st.number_input("Limite", min_value=1, max_value=100, value=10)

    if st.button("Carregar Lista de Splits"):
        try:
            # Aqui você deve implementar a função para buscar os splits, neste exemplo não está implementada
            # splits = fetch_splits(limit=limit)
            # Se houver splits, exiba-os em um dataframe
            # df = pd.DataFrame(splits)
            # st.dataframe(df)
            st.warning("Funcionalidade de listagem de splits ainda não implementada.")
        except Exception as e:
            st.error(f"Erro ao carregar splits: {e}")

