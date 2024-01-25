from httpx import Client
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .types import PlanoDeCorteModel

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
    PlanoDeCorte: PlanoDeCorteModel


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

    def novo_plano_de_corte_peca(
        self,
        codigo_layout: str,
        qtd_cortada_no_layout: int,
        id_unico_peca: int,
        tempo_corte_segundos: float,
    ):
        response = self.client.post(
            f"/plano-de-corte/{codigo_layout}/pecas",
            json={
                "qtd_cortada_no_layout": qtd_cortada_no_layout,
                "id_unico_peca": id_unico_peca,
                "tempo_corte_segundos": tempo_corte_segundos,
            },
        )

        response.raise_for_status()
