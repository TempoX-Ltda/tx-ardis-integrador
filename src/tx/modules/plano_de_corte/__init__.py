from httpx import Client
from tx.modules.plano_de_corte.types import PlanoDeCorteModel, TipoMateriaPrima

from tx.utils.commons import SuccessResponse

from .pecas import Pecas


class PlanoDeCorte:
    def __init__(self, client: Client):
        self.client = client

        self.pecas = Pecas(self.client)

    def novo_plano_de_corte(
        self,
        codigo_layout: str,
        id_recurso: int,
        perc_aproveitamento: float,
        nome_projeto: str,
        descricao_material: str,
        perc_sobras: float,
        tipo: TipoMateriaPrima,
        codigo_lote: str,
        qtd_chapas: int,
        mm_comp_linear: float,
        mm_comprimento: float,
        mm_largura: float,
        tempo_estimado_seg: int,
    ):
        response = self.client.post(
            "/plano-de-corte",
            json={
                "mm_largura": mm_largura,
                "tempo_estimado_seg": tempo_estimado_seg,
                "id_recurso": id_recurso,
                "perc_aproveitamento": perc_aproveitamento,
                "mm_comprimento": mm_comprimento,
                "nome_projeto": nome_projeto,
                "codigo_layout": codigo_layout,
                "perc_sobras": perc_sobras,
                "tipo": tipo,
                "codigo_lote": codigo_lote,
                "qtd_chapas": qtd_chapas,
                "mm_comp_linear": mm_comp_linear,
                "descricao_material": descricao_material,
            },
        )

        response.raise_for_status()

        return SuccessResponse(**response.json()).retorno

    def salvar_imagem_do_plano_de_corte(
        self, codigo_plano_de_corte: str, imageBase64: bytes
    ):
        response = self.client.post(
            f"/plano-de-corte/{codigo_plano_de_corte}/figure",
            json={"decoded_figure": imageBase64.decode("utf-8")},
        )

        response.raise_for_status()
