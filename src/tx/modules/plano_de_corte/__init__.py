import json
import logging
from typing import List, Literal

from httpx import Client, HTTPStatusError

from src.tx.modules.plano_de_corte.pecas import Pecas
from src.tx.modules.plano_de_corte.types import PlanoDeCorteCreateModel
from src.tx.utils.commons import SuccessResponse
from src.utils import handle_http_error

logger = logging.getLogger("src.tx.modules.plano_de_corte")


class PlanoDeCorte:
    def __init__(self, client: Client):
        self.client = client

        self.pecas = Pecas(self.client)

    def novo_projeto(
        self,
        planos: List[PlanoDeCorteCreateModel],
    ):
        logger.info("Enviando projeto para a API...")

        body = {"planos": [plano.model_dump() for plano in planos]}

        response = self.client.post(
            "/plano-de-corte/projeto",
            json=body,
        )

        try:
            response.raise_for_status()

        except Exception as exc:
            message = "Erro ao enviar dados para a API"

            if isinstance(exc, HTTPStatusError):
                message = handle_http_error(exc)

            raise Exception(message) from exc

        return SuccessResponse(**response.json()).retorno

    def apontar(
        self,
        codigo_layout: str,
    ):
        logger.info(f"Apontando layout {codigo_layout} no MES...")

        response = self.client.post(
            f"/plano-de-corte/{codigo_layout}/apontar",
        )

        try:
            response.raise_for_status()

        except Exception as exc:
            message = "Erro ao apontar layout no MES"

            if isinstance(exc, HTTPStatusError):
                message = handle_http_error(exc)

            raise Exception(message) from exc

        return SuccessResponse(**response.json()).retorno
