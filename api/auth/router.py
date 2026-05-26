from fastapi import APIRouter, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import UserRegister, UserLogin, TokenResponse
from .service import registrar_usuario, autenticar_usuario
from api.dependencies import get_db
from api.middleware import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, dados: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await registrar_usuario(dados, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, dados: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await autenticar_usuario(dados.email, dados.senha, db)
