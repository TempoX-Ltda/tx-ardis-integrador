from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanoDeCorteModel(BaseModel):
    id: int
    codigo_layout: str
    perc_aproveitamento: float
    perc_sobras: float
    descricao_material: str
    descricao: str
    sequencia_corte: int
    inicio_apontamento: Optional[datetime]
    fim_apontamento: Optional[datetime]
    perc_performance: Optional[float]
    created_on: datetime
    modified_on: datetime
    qtd_chapas: int
    inativo: bool
    id_recurso: int
    mm_comprimento: float
    mm_largura: float
    mm_comp_linear: float
    id_projeto: Optional[int]
    nome_projeto: str
    codigo_lote: str
    sobra: bool
    sucesso_integrador: Optional[bool]
    data_integrador: Optional[datetime]
    log_integrador: str
    tempo_estimado: str
    tempo_parada: Optional[str]
    tempo_trabalhado: Optional[str]
    pendente: bool
    em_processo: bool
    finalizado: bool
    tempo_bruto: Optional[str]
    qtd_separacao_automatica: int
    qtd_separacao_manual: int


class TipoMateriaPrima(str, Enum):
    chapa = "chapa"
    sobra = "sobra"
    recorte = "recorte"


class PlanoDeCortePecasCreateModel(BaseModel):
    qtd_cortada_no_layout: int
    id_unico_peca: Optional[int]
    id_ordem: Optional[int]
    id_retrabalho: Optional[int]
    tempo_corte_segundos: float


class PlanoDeCorteCreateModel(BaseModel):
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
    qtd_recortes: int
    qtd_separacao_automatica: int
    qtd_separacao_manual: int
    figure: Optional[str] = Field(None)
    pecas: List[PlanoDeCortePecasCreateModel] = Field([])
