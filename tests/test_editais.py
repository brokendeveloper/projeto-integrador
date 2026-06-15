import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from api.main import app


def _make_usuario():
    return {"_id": ObjectId(), "email": "mei@teste.com", "plano": "free"}


def _make_contrato(valor=50000.0):
    oid = ObjectId()
    return {
        "_id": oid,
        "numeroControlePNCP": "00038.00004/2024-00",
        "objetoContrato": "Aquisição de material de escritório",
        "orgaoEntidade": {"razaoSocial": "Prefeitura Municipal", "ufSigla": "SP"},
        "valorInicial": valor,
        "modalidadeNome": "Dispensa",
        "dataPublicacaoPncp": "2024-01-10",
        "dataVigenciaFim": "2024-03-10",
    }


def _make_mock_db(contratos=None):
    """Mock do MongoDB retornando uma lista de contratos."""
    docs = contratos or []

    async def count_documents(query):
        return len(docs)

    def find(query):
        class Cursor:
            def skip(self, n): return self
            def limit(self, n): return self
            async def to_list(self, length): return docs[:length]
        return Cursor()

    async def find_one(query):
        if "_id" in query:
            for doc in docs:
                if doc["_id"] == query["_id"]:
                    return doc
        return None

    col = MagicMock()
    col.count_documents = count_documents
    col.find = find
    col.find_one = find_one

    db = MagicMock()
    db.contratos = col
    db.usuarios = MagicMock()
    db.usuarios.find_one = AsyncMock(return_value=_make_usuario())
    return db


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_buscar_editais_retorna_paginacao():
    """GET /editais deve retornar estrutura com items, total, pagina e paginas."""
    usuario = _make_usuario()
    contratos = [_make_contrato() for _ in range(3)]
    mock_db = _make_mock_db(contratos)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "pagina" in data
    assert "paginas" in data
    assert data["total"] == 3


@pytest.mark.asyncio
async def test_buscar_editais_favoravel_mei():
    """Edital com valor ≤ 80000 deve ter favoravel_mei=True."""
    usuario = _make_usuario()
    contratos = [_make_contrato(valor=79999.0)]
    mock_db = _make_mock_db(contratos)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["favoravel_mei"] is True


@pytest.mark.asyncio
async def test_buscar_editais_nao_favoravel_mei():
    """Edital com valor > 80000 deve ter favoravel_mei=False."""
    usuario = _make_usuario()
    contratos = [_make_contrato(valor=150000.0)]
    mock_db = _make_mock_db(contratos)
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["favoravel_mei"] is False


@pytest.mark.asyncio
async def test_buscar_edital_por_id_valido():
    """GET /editais/{id} com ObjectId válido deve retornar o edital."""
    usuario = _make_usuario()
    contrato = _make_contrato()
    mock_db = _make_mock_db([contrato])
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/editais/{contrato['_id']}")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["id"] == str(contrato["_id"])


@pytest.mark.asyncio
async def test_buscar_edital_por_id_invalido():
    """GET /editais/{id} com formato inválido deve retornar 400."""
    usuario = _make_usuario()
    mock_db = _make_mock_db([])
    app.state.db = mock_db

    from api.dependencies import get_usuario_atual
    app.dependency_overrides[get_usuario_atual] = lambda: usuario

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais/id-invalido-formato-errado")

    app.dependency_overrides.clear()
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_buscar_editais_sem_autenticacao():
    """GET /editais sem token deve retornar 401."""
    mock_db = _make_mock_db([])
    app.state.db = mock_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/editais")

    assert response.status_code == 401
