import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from api.main import app


def _make_usuario():
    oid = ObjectId()
    return {"_id": oid, "email": "mei@teste.com", "plano": "free"}


def _make_mock_db(usuario):
    store = {}

    async def count_documents(query):
        count = 0
        for doc in store.values():
            if all(doc.get(k) == v for k, v in query.items()):
                count += 1
        return count

    async def insert_one(doc):
        oid = ObjectId()
        doc["_id"] = oid
        store[str(oid)] = doc
        result = MagicMock()
        result.inserted_id = oid
        return result

    def find(query):
        docs = [doc for doc in store.values() if all(doc.get(k) == v for k, v in query.items())]

        class AsyncCursor:
            def __aiter__(self):
                return self._gen()

            async def _gen(self):
                for doc in docs:
                    yield doc

        return AsyncCursor()

    async def delete_one(query):
        for key, doc in list(store.items()):
            if all(doc.get(k) == v for k, v in query.items() if k != "_id"):
                if "_id" in query and doc.get("_id") != query["_id"]:
                    continue
                del store[key]
                result = MagicMock()
                result.deleted_count = 1
                return result
        result = MagicMock()
        result.deleted_count = 0
        return result

    collection = MagicMock()
    collection.count_documents = count_documents
    collection.insert_one = insert_one
    collection.find = find
    collection.delete_one = delete_one

    db = MagicMock()
    db.alertas = collection
    db.usuarios = MagicMock()
    db.usuarios.find_one = AsyncMock(return_value=usuario)
    return db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_criar_alerta_sucesso():
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/alertas", json={
            "nome": "Alerta TI",
            "cnae": "6201-5/01",
            "valor_max": 80000.0,
            "uf": "SP",
        })

    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Alerta TI"
    assert "id" in data


@pytest.mark.asyncio
async def test_limite_alertas_free():
    """Plano free permite no máximo 3 alertas ativos."""
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for i in range(3):
            r = await client.post("/alertas", json={"nome": f"Alerta {i}", "ativo": True})
            assert r.status_code == 201

        response = await client.post("/alertas", json={"nome": "Alerta 4", "ativo": True})

    app.dependency_overrides.clear()
    assert response.status_code == 403
    assert "3 alertas" in response.json()["detail"]


@pytest.mark.asyncio
async def test_listar_alertas():
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/alertas", json={"nome": "Alerta Lista"})
        response = await client.get("/alertas")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert isinstance(response.json(), list)
