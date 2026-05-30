from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import UserRegister, UserLogin, TokenResponse
from .service import registrar_usuario, autenticar_usuario
from api.dependencies import get_db
from api.middleware import limiter

router = APIRouter(prefix="/auth", tags=["🔐 Autenticação"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Criar conta",
    description=(
        "Cria uma nova conta de MEI na plataforma.\n\n"
        "- O CNPJ deve ter 14 dígitos (com ou sem formatação)\n"
        "- A senha deve ter no mínimo 8 caracteres\n"
        "- Após o cadastro, o token de acesso é retornado imediatamente"
    ),
)
@limiter.limit("10/minute")
async def register(request: Request, dados: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await registrar_usuario(dados, db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Entrar na conta",
    description=(
        "Autentica o usuário e retorna o token de acesso JWT.\n\n"
        "**Como usar o token no Swagger:**\n"
        "1. Copie o valor do campo `access_token` da resposta\n"
        "2. Clique em **Authorize** no topo da página\n"
        "3. Cole o token no campo **Value** (sem digitar \"Bearer\")\n"
        "4. Clique em Authorize — todos os endpoints autenticados estarão liberados"
    ),
)
@limiter.limit("10/minute")
async def login(request: Request, dados: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await autenticar_usuario(dados.email, dados.senha, db)
