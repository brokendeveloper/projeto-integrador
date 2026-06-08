import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from api.main import app


def _make_mock_db():
    """Cria um banco em memória simples para os testes de auth."""
    store = {}

    async def find_one(query):
        for doc in store.values():
            match = all(doc.get(k) == v for k, v in query.items() if not k.startswith("$"))
            if match:
                return doc
        return None

    async def insert_one(doc):
        from bson import ObjectId
        oid = ObjectId()
        doc["_id"] = oid
        store[str(oid)] = doc
        result = MagicMock()
        result.inserted_id = oid
        return result

    collection = MagicMock()
    collection.find_one = find_one
    collection.insert_one = insert_one

    db = MagicMock()
    db.usuarios = collection
    return db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_registro_sucesso():
    mock_db = _make_mock_db()
    app.state.db = mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/register", json={
            "nome": "MEI Teste",
            "email": "mei@teste.com",
            "cnpj": "12345678000195",
            "senha": "senha123",
        })
    assert response.status_code == 201
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_registro_email_duplicado():
    mock_db = _make_mock_db()
    app.state.db = mock_db

    dados = {"nome": "MEI", "email": "dup@teste.com", "cnpj": "11222333000181", "senha": "senha123"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/auth/register", json=dados)
        response = await client.post("/auth/register", json=dados)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_credenciais_invalidas():
    mock_db = _make_mock_db()
    app.state.db = mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/auth/login", json={
            "email": "naoexiste@teste.com",
            "senha": "errada",
        })
    assert response.status_code == 401
