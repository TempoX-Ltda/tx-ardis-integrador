from typing import Literal, Optional
from pydantic import BaseModel


class PartFromCsv(BaseModel):
    codigo_layout: str
    id_ordem: str
    id_unico_peca: int
    qtd_cortada_no_layout: int
    tempo_corte_segundos: float


class PlanoDeCorteFromCsv(BaseModel):
    codigo_layout: str
    descricao_material: str
    id_recurso: int
    mm_comp_linear: float
    mm_comprimento: float
    mm_largura: float
    nome_projeto: str
    perc_aproveitamento: float
    perc_sobras: float
    qtd_chapas: int
    sobra: Literal["S", "N"]
    tempo_estimado_seg: int
    codigo_lote: Optional[str]
