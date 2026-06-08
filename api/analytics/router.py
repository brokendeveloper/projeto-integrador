from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from api.dependencies import get_db, get_usuario_atual
from .schemas import (
    ContratosMEIResponse,
    EstatisticasResponse,
    SparkJobResponse,
    SparkSummaryResponse,
    TopOrgaosResponse,
)
from .service import (
    executar_spark,
    obter_contratos_mei,
    obter_dados_spark,
    obter_estatisticas,
    obter_top_orgaos,
)

router = APIRouter(prefix="/analytics", tags=["📈 Analytics"])


@router.get(
    "/estatisticas",
    response_model=EstatisticasResponse,
    summary="Estatísticas gerais dos contratos",
    description=(
        "Retorna o total de contratos na base e as estatísticas dos valores iniciais "
        "(média, máximo e mínimo). Equivale ao `summary()` produzido pelo pipeline PySpark."
    ),
)
async def estatisticas(
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await obter_estatisticas(db)


@router.get(
    "/top-orgaos",
    response_model=TopOrgaosResponse,
    summary="Top N órgãos por volume de contratos",
    description=(
        "Lista os órgãos públicos com mais contratos publicados, "
        "ordenados de forma decrescente. Equivale ao `groupBy().count()` do PySpark."
    ),
)
async def top_orgaos(
    n: int = Query(10, ge=1, le=100, description="Quantidade de órgãos a retornar"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await obter_top_orgaos(db, n)


@router.get(
    "/contratos-mei",
    response_model=ContratosMEIResponse,
    summary="Contratos favoráveis ao MEI (valor ≤ R$ 80.000)",
    description=(
        "Retorna contratos com valor inicial igual ou inferior a R$ 80.000, "
        "faixa considerada favorável à participação de MEIs. "
        "Equivale ao filtro `valorInicial <= 80000` do pipeline PySpark."
    ),
)
async def contratos_mei(
    limite: int = Query(20, ge=1, le=200, description="Número máximo de contratos a retornar"),
    db: AsyncIOMotorDatabase = Depends(get_db),
    _: dict = Depends(get_usuario_atual),
):
    return await obter_contratos_mei(db, limite)


@router.get(
    "/spark",
    response_model=SparkSummaryResponse,
    summary="Resumo do pipeline PySpark (CSVs gerados)",
    description=(
        "Lê os arquivos CSV produzidos pelo `spark/pyspark_transform.py` e retorna "
        "um resumo estruturado: totais, estatísticas dos valores MEI, histograma de buckets, "
        "top órgãos e amostra dos contratos. Se os CSVs ainda não existirem, retorna "
        "`disponivel: false`."
    ),
)
async def spark_summary(
    _: dict = Depends(get_usuario_atual),
):
    return obter_dados_spark()


@router.post(
    "/executar-spark",
    response_model=SparkJobResponse,
    summary="Disparar o pipeline PySpark em background",
    description=(
        "Inicia `spark/pyspark_transform.py` como subprocesso assíncrono. "
        "O endpoint retorna imediatamente com o PID do processo. "
        "Os CSVs transformados são salvos em `spark/output/` ao término. "
        "Requer que PySpark e Java estejam instalados no servidor."
    ),
)
async def executar_pipeline_spark(
    _: dict = Depends(get_usuario_atual),
):
    return await executar_spark()
