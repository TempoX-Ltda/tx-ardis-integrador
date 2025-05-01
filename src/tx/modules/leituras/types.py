from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class LeiturasPost(BaseModel):
    id_recurso: int
    codigo: str
    qtd: int
    leitura_manual: bool
