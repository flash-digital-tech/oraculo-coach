import streamlit as st
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
import pandas as pd
import stripe
import asyncio
from typing import Optional
from key_config import API_KEY_STRIPE, URL_BASE


app = FastAPI()

# Modelo de Produto
class Produto(BaseModel):
    nome: str
    descricao: Optional[str] = ''
    preco: float
    moeda: str = "brl"  # Moeda padrão é BRL

class ProdutoResponse(BaseModel):
    id: str
    nome: str
    descricao: str
    preco: float
    moeda: str

async def create_product(produto: Produto):
    try:
        product = stripe.Product.create(
            name=produto.nome,
            description=produto.descricao if produto.descricao else 'N/A',  # Verifica se descricao é None antes de passá-la
        )
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(produto.preco * 100),  # O valor deve ser em centavos
            currency=produto.moeda,
        )
        return ProdutoResponse(
            id=product['id'],
            nome=product['name'],
            descricao=product['description'] if product['description'] else 'N/A',  # Verifica se descricao é None antes de passá-la
            preco=produto.preco,
            moeda=produto.moeda
        )
    except ValidationError as exc:
        # Captura erros de validação do Pydantic
        raise HTTPException(status_code=422, detail=exc.errors())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def fetch_products(limit: int = 100):
    try:
        products = stripe.Product.list(limit=limit)
        return [
            ProdutoResponse(
                id=product['id'],
                nome=product['name'],
                descricao=product.get('description', '') if product.get('description') is not None else '',
                preco=0,  # O preço não é retornado diretamente aqui, você pode querer buscar o preço separadamente
                moeda="brl"  # Definindo moeda padrão
            ) for product in products['data']
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/products", response_model=ProdutoResponse)
async def api_create_product(produto: Produto):
    return await create_product(produto)


@app.get("/products", response_model=list[ProdutoResponse])
async def api_fetch_products(limit: int = 100):
    return await fetch_products(limit)


# Streamlit Interface
def run_streamlit():
    st.title("Sistema Flash Pagamentos")

    # Seção para criar um novo produto
    st.header("Criar Novo Produto")

    # Inicializa os campos no session_state se não existirem
    if 'nome' not in st.session_state:
        st.session_state.nome = ""
    if 'descricao' not in st.session_state:
        st.session_state.descricao = ""
    if 'preco' not in st.session_state:
        st.session_state.preco = 0.0
    if 'moeda' not in st.session_state:
        st.session_state.moeda = "brl"

    # Formulário para cadastro de produto
    with st.form(key='form_produto'):
        st.session_state.nome = st.text_input("Nome do Produto", value=st.session_state.nome)
        st.session_state.descricao = st.text_area("Descrição do Produto", value=st.session_state.descricao)
        st.session_state.preco = st.number_input("Preço do Produto (R$)", min_value=0.0, format="%.2f", value=st.session_state.preco)
        st.session_state.moeda = st.selectbox("Moeda", options=["brl", "usd", "eur"], index=0)

        # Botão para enviar os dados do formulário
        submit_button = st.form_submit_button("CRIAR PRODUTO!")

        if submit_button:
            produto = Produto(
                nome=st.session_state.nome,
                descricao=st.session_state.descricao,
                preco=st.session_state.preco,
                moeda=st.session_state.moeda
            )
            try:
                produtos = asyncio.run(create_product(produto=produto))  # Chame a função assíncrona diretamente
                st.success(f"Produto {produto.nome} criado com sucesso!")

                # Limpa os campos do formulário
                st.session_state.nome = ""
                st.session_state.descricao = ""
                st.session_state.preco = 0.0
                st.session_state.moeda = "brl"

            except Exception as e:
                st.error(f"Erro ao criar produto: {e}")

    # Seção para listar produtos
    st.header("Listar Produtos")
    limit = st.number_input("Limite", min_value=1, max_value=100, value=5)

    if st.button("Carregar Lista de Produtos"):
        try:
            produtos = asyncio.run(fetch_products(limit=limit))
            if produtos:
                data = []
                for produto in produtos:
                    data.append({
                        'ID': produto.id,
                        'Nome': produto.nome,
                        'Descrição': produto.descricao,
                        'Preço': produto.preco,
                    })
                df = pd.DataFrame(data)
                st.dataframe(df)  # Exibe a tabela de produtos no Streamlit
            else:
                st.warning("Nenhum produto encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar produtos: {e}")

