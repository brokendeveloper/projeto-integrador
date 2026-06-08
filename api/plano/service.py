from motor.motor_asyncio import AsyncIOMotorDatabase

_PLANOS = {
    "free": {
        "nome": "Gratuito",
        "preco": "R$ 0/mês",
        "recursos": [
            "Até 3 alertas de editais",
            "Checklist básico de habilitação",
            "Upload de documentos por edital",
            "Histórico de participações",
            "Busca no acervo do PNCP",
        ],
        "limite_alertas": 3,
    },
    "premium": {
        "nome": "Premium",
        "preco": "R$ 29,90/mês",
        "recursos": [
            "Alertas ilimitados",
            "Checklist completo (Lei 14.133/2021)",
            "Upload ilimitado com OCR automático",
            "Histórico detalhado com relatórios",
            "Busca avançada com filtros MEI",
            "Suporte prioritário",
            "Acesso ao assistente Léo",
        ],
        "limite_alertas": -1,
    },
}


async def obter_plano(usuario: dict) -> dict:
    plano_atual = usuario.get("plano", "free")
    proximo = "premium" if plano_atual == "free" else "free"
    return {
        "plano_atual": plano_atual,
        "info": _PLANOS[plano_atual],
        "proximo_plano": _PLANOS[proximo],
    }


async def simular_upgrade(db: AsyncIOMotorDatabase, usuario: dict) -> dict:
    plano_atual = usuario.get("plano", "free")
    novo_plano = "premium" if plano_atual == "free" else "free"
    await db.usuarios.update_one(
        {"_id": usuario["_id"]}, {"$set": {"plano": novo_plano}}
    )
    return {
        "plano_atual": novo_plano,
        "info": _PLANOS[novo_plano],
        "proximo_plano": _PLANOS["free" if novo_plano == "premium" else "premium"],
    }
