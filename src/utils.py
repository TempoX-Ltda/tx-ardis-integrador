from typing import Optional
from pydantic import BaseModel

from tx.modules.plano_de_corte.types import TipoMateriaPrima


class PlanoDeCortePecasCsvModel(BaseModel):
    codigo_layout: str
    qtd_cortada_no_layout: int
    id_unico_peca: Optional[int]
    id_ordem: Optional[int]
    tempo_corte_segundos: float


class PlanoDeCorteCsvModel(BaseModel):
    codigo_layout: str
    descricao_material: str
    id_recurso: int
    mm_comp_linear: float
    mm_comprimento: float
    mm_largura: float
    nome_projeto: str
    perc_aproveitamento: float
    perc_sobras: float
    tipo: TipoMateriaPrima
    codigo_lote: str
    qtd_chapas: int
    tempo_estimado_seg: float
