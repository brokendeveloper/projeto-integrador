from pydantic import BaseModel
from typing import Optional
from enum import Enum


class StatusParticipacao(str, Enum):
    em_andamento = "em_andamento"
    vencida = "vencida"
    perdida = "perdida"
    desistida = "desistida"


class ParticipacaoCriar(BaseModel):
    edital_id: str
    numero_controle_pncp: Optional[str] = None
    objeto: Optional[str] = None
    valor_proposta: Optional[float] = None
    status: StatusParticipacao = StatusParticipacao.em_andamento


class ParticipacaoResponse(BaseModel):
    id: str
    edital_id: str
    status: str
    valor_proposta: Optional[float] = None
    data_participacao: str


class ResumoResponse(BaseModel):
    total: int
    vencidas: int
    em_andamento: int
    perdidas: int
