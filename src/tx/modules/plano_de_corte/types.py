from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


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


class TipoMateriaPrima(str, Enum):
    chapa = "chapa"
    sobra = "sobra"
    recorte = "recorte"
