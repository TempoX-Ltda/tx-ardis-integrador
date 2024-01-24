from httpx import Client
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .types import PlanoDeCorte

from ...utils.commons import SuccessResponse


class PlanoDeCortePecas(BaseModel):
    id: int
    codigo_layout: str
    tempo_corte_segundos: float
    qtd_cortada_no_layout: int
    qtd_retrabalho: Optional[int]
    created_on: datetime
    modified_on: datetime
    id_unico_peca: int
    conferido: bool
    data_conferencia: Optional[datetime]


class Return(BaseModel):
    PlanoDeCortePecas: PlanoDeCortePecas
    PlanoDeCorte: PlanoDeCorte


class Pecas:
    def __init__(self, client: Client):
        self.client = client

    def busca_plano_de_corte_por_peca(self, id_unico_peca: int):
        """
        Retorna todos os planos de corte que contém a peça com o id único informado
        """

        response = self.client.get(f"/plano-de-corte/peca/{id_unico_peca}")

        response.raise_for_status()

        return SuccessResponse[List[Return]](**response.json()).retorno
