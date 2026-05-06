from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from .schemas import UserRegister, UserLogin, TokenResponse
from .service import registrar_usuario, autenticar_usuario
from api.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(dados: UserRegister, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await registrar_usuario(dados, db)


@router.post("/login", response_model=TokenResponse)
async def login(dados: UserLogin, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await autenticar_usuario(dados.email, dados.senha, db)
