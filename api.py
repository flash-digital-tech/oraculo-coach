from fastapi import FastAPI

# Criação da instância da aplicação FastAPI
app = FastAPI()

# Definição de uma rota simples
@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


# Definição de uma rota com um parâmetro
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "query": q}
