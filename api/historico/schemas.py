from pydantic import BaseModel
from typing import Optional
from enum import Enum


class StatusParticipacao(str, Enum):
    em_andamento = "em_andamento"
    venceu = "venceu"
    perdeu = "perdeu"
    desistiu = "desistiu"


class ParticipacaoCriar(BaseModel):
    edital_id: str
    numero_controle_pncp: str
    objeto: str
    valor: Optional[float] = None
    status: StatusParticipacao = StatusParticipacao.em_andamento


class ParticipacaoResponse(ParticipacaoCriar):
    id: str
    usuario_id: str
    registrado_em: str


class ResumoResponse(BaseModel):
    total: int
    venceu: int
    em_andamento: int
    perdeu: int
    desistiu: int
