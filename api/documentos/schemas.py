from pydantic import BaseModel


class DocumentoResponse(BaseModel):
    id: str
    nome: str
    categoria: str
    tamanho: int
    edital_id: str
