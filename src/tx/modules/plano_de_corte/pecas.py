from datetime import datetime
from typing import List, Optional

from httpx import Client
from pydantic import BaseModel

from src.tx.utils.commons import SuccessResponse


class PlanoDeCortePecas(BaseModel):
    created_on: datetime
    modified_on: datetime
    id: int
    codigo_layout: str
    id_recurso: int
    id_unico_peca: Optional[int]
    tempo_corte_segundos: Optional[float]
    qtd_cortada_no_layout: int
    conferido: bool
    data_conferencia: Optional[datetime]
    nome_projeto: str
    descricao_material: str
    inativo: bool
    pendente: bool
    finalizado: bool
    em_processo: bool
    inicio_apontamento: Optional[datetime]
    fim_apontamento: Optional[datetime]
    id_ordem: Optional[int]
    item_codigo: Optional[str]
    item_descricao: Optional[str]
    item_mascara: Optional[str]
    item_mascara_descricao: Optional[str]
    mm_comprimento: Optional[float]
    mm_largura: Optional[float]
    mm_espessura: Optional[float]
    quantidade_ordem: Optional[int]
    codigo_lote: Optional[str]
    kg_peso_liquido: Optional[float]
    kg_peso_bruto: Optional[float]
    cancelada: Optional[bool]


class Pecas:
    def __init__(self, client: Client):
        self.client = client

    def busca_plano_de_corte_por_peca(self, id_unico_peca: int):
        """
        Retorna todos os planos de corte que contém a peça com o id único informado
        """

        response = self.client.get(
            "/plano-de-corte/pecas", params={"id_unico_peca": id_unico_peca}
        )

        response.raise_for_status()

        return SuccessResponse[List[PlanoDeCortePecas]](**response.json()).retorno

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
