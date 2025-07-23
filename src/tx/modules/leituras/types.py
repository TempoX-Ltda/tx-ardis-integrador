from pydantic import BaseModel


class LeiturasPost(BaseModel):
    id_recurso: int
    codigo: str
    qtd: int
    leitura_manual: bool
