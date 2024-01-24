from pydantic import BaseModel


class Part(BaseModel):
    codigo_layout: str
    id_ordem: str
    id_unico_peca: int
    qtd_cortada_no_layout: int
    tempo_corte_segundos: float
