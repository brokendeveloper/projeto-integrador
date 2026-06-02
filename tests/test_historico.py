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

    async def insert_one(doc):
        oid = ObjectId()
        doc["_id"] = oid
        store[str(oid)] = doc
        result = MagicMock()
        result.inserted_id = oid
        return result

    async def count_documents(query):
        count = 0
        for doc in store.values():
            if all(doc.get(k) == v for k, v in query.items()):
                count += 1
        return count

    def find(query):
        docs = [doc for doc in store.values() if all(doc.get(k) == v for k, v in query.items())]

        class AsyncCursor:
            def __aiter__(self):
                return self._gen()

            async def _gen(self):
                for doc in docs:
                    yield doc

        return AsyncCursor()

    collection = MagicMock()
    collection.insert_one = insert_one
    collection.find = find
    collection.count_documents = count_documents

    db = MagicMock()
    db.historico = collection
    return db


_PAYLOAD = {
    "edital_id": "abc123",
    "valor_proposta": 15000.0,
    "status": "em_andamento",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_registrar_participacao():
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/historico", json=_PAYLOAD)

    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["edital_id"] == "abc123"
    assert "data_participacao" in data


@pytest.mark.asyncio
async def test_listar_participacoes():
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/historico", json=_PAYLOAD)
        response = await client.get("/historico")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_resumo_participacoes():
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/historico", json={**_PAYLOAD, "status": "vencida"})
        await client.post("/historico", json={**_PAYLOAD, "status": "perdida"})
        response = await client.get("/historico/resumo")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["vencidas"] == 1
    assert data["perdidas"] == 1
