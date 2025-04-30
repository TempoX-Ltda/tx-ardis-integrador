import json
import logging
from typing import List

from httpx import Client, HTTPStatusError

from src.tx.modules.cliente.types import NovaOrdemRoteiroEIdUnico
from src.tx.utils.commons import SuccessResponse
from src.utils import handle_http_error

logger = logging.getLogger("src.tx.modules.cliente")


class Cliente:
    def __init__(self, client: Client):
        self.client = client

    def nova_ordem(self, ordens: List[NovaOrdemRoteiroEIdUnico]):
        logger.info("Enviando ordem para a API...")

        body = {"ordens": [ordem.model_dump() for ordem in ordens]}

        response = self.client.post(
            "/cliente/ordem",
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
