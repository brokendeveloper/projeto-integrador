import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from api.main import app


def _make_usuario(plano="free"):
    return {"_id": ObjectId(), "email": "mei@teste.com", "plano": plano}


def _make_mock_db(usuario, progresso_existente=None):
    """Mock com coleção checklist_progresso em memória."""
    store = {}
    if progresso_existente:
        store["inicial"] = progresso_existente

    async def find_one_progresso(query):
        for doc in store.values():
            if (doc.get("usuario_id") == query.get("usuario_id") and
                    doc.get("edital_id") == query.get("edital_id")):
                return doc
        return None

    async def update_one(filtro, update, upsert=False):
        key = f"{filtro.get('usuario_id')}:{filtro.get('edital_id')}"
        if key not in store:
            store[key] = {**filtro}
        store[key].update(update.get("$set", {}))
        result = MagicMock()
        result.upserted_id = None
        return result

    progresso_col = MagicMock()
    progresso_col.find_one = find_one_progresso
    progresso_col.update_one = update_one

    db = MagicMock()
    db.checklist_progresso = progresso_col
    db.usuarios = MagicMock()
    db.usuarios.find_one = AsyncMock(return_value=usuario)
    return db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_obter_checklist_estrutura():
    """GET /editais/{id}/checklist deve retornar edital_id, progresso e items."""
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais/abc123/checklist")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert "edital_id" in data
    assert "progresso" in data
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_checklist_progresso_inicial_zero():
    """Sem nenhum item marcado, progresso deve ser 0."""
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais/edital-001/checklist")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["progresso"] == 0.0


@pytest.mark.asyncio
async def test_checklist_plano_free_menos_itens_que_premium():
    """Plano free deve ter menos itens que premium (item mei_02 é exclusivo premium)."""
    usuario_free = _make_usuario("free")
    usuario_premium = _make_usuario("premium")

    app.state.db = _make_mock_db(usuario_free)
    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario_free

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r_free = await client.get("/editais/edital-001/checklist")

    app.state.db = _make_mock_db(usuario_premium)
    app.dependency_overrides[get_usuario_atual] = lambda: usuario_premium

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r_premium = await client.get("/editais/edital-001/checklist")

    app.dependency_overrides.clear()
    assert r_free.status_code == 200
    assert r_premium.status_code == 200
    assert len(r_free.json()["items"]) < len(r_premium.json()["items"])


@pytest.mark.asyncio
async def test_marcar_item_concluido():
    """PATCH /editais/{id}/checklist deve persistir item como concluído e aumentar progresso."""
    usuario = _make_usuario()
    mock_db = _make_mock_db(usuario)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.patch("/editais/edital-001/checklist", json={
            "item_id": "jur_01",
            "concluido": True,
        })

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["progresso"] > 0
    item_marcado = next((i for i in data["items"] if i["id"] == "jur_01"), None)
    assert item_marcado is not None
    assert item_marcado["concluido"] is True


@pytest.mark.asyncio
async def test_checklist_sem_autenticacao():
    """GET /editais/{id}/checklist sem token deve retornar 403."""
    mock_db = _make_mock_db(_make_usuario())
    app.state.db = mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais/edital-001/checklist")

    assert response.status_code == 403
