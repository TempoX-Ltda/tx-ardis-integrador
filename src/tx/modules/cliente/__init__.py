import json
import logging
from typing import List

from httpx import Client, HTTPStatusError

from src.tx.modules.cliente.types import NovaOrdemRoteiroEIdUnico
from src.tx.utils.commons import SuccessResponse

logger = logging.getLogger(__name__)


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
                response = exc.response.json()

                server_message = response.get("mensagem") or json.dumps(response)

                message = (
                    f"Erro {exc.response.status_code} ao enviar dados para a API:\n"
                    f"{server_message}"
                )

            raise Exception(message) from exc

        return SuccessResponse(**response.json()).retorno
