from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class NovoRoteiroParams(BaseModel):
    id_ordem: int
    sequencia_operacao: int
    codigo_operacao: str
    id_setor: int
    operacao_final: bool = False
    codigo_roteiro: Optional[str] = None
    descricao_roteiro: Optional[str] = None
    id_metrica_performance: Optional[int] = None
    valor_metrica_performance: Optional[float] = None
    sincronizado_em: Optional[datetime] = None
    qtd_finalizada: Optional[int] = None
    id_roteiro_erp: Optional[int] = None
    qtd_finalizada_erp: Optional[int] = None


class NovoIdUnicoParams(BaseModel):
    id_ordem: int
    id_unico_peca: int


class NovaOrdemParams(BaseModel):
    id_ordem: int
    item_codigo: str
    item_mascara: str
    quantidade_ordem: int
    kg_peso_liquido: float = 0
    kg_peso_bruto: float = 0
    data_emissao: Optional[datetime] = None
    item_descricao: Optional[str] = None
    item_mascara_descricao: Optional[str] = None
    mm_comprimento: Optional[float] = None
    mm_largura: Optional[float] = None
    mm_espessura: Optional[float] = None
    codigo_lote: Optional[str] = None
    materia_prima_descricao: Optional[str] = None
    campo01: Optional[str] = None
    campo02: Optional[str] = None
    campo03: Optional[str] = None
    campo04: Optional[str] = None
    campo05: Optional[str] = None
    campo06: Optional[str] = None
    campo07: Optional[str] = None
    campo08: Optional[str] = None
    campo09: Optional[str] = None
    campo10: Optional[str] = None
    campo11: Optional[str] = None
    campo12: Optional[str] = None
    campo13: Optional[str] = None
    campo14: Optional[str] = None
    campo15: Optional[str] = None
    campo16: Optional[str] = None
    campo17: Optional[str] = None
    campo18: Optional[str] = None
    campo19: Optional[str] = None
    campo20: Optional[str] = None


class NovaOrdemRoteiroEIdUnico(NovaOrdemParams):
    roteiros: List[NovoRoteiroParams] = []
    ids_unicos: List[NovoIdUnicoParams] = []
