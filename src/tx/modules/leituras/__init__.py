import logging

from httpx import Client, HTTPStatusError

from src.tx.utils.commons import SuccessResponse
from src.utils import handle_http_error, mostrar_toast

logger = logging.getLogger("src.tx.modules.leituras")


class Leitura:
    def __init__(self, client: Client):
        self.client = client

    def nova_leitura(
        self,
        id_recurso: int,
        codigo: str,
        qtd: int,
        leitura_manual: bool,
    ):
        logger.info(
            f"Enviando leitura para a API: código={codigo}, qtd={qtd}, leitura_manual={leitura_manual}"
        )

        body = {
            "id_recurso": id_recurso,
            "codigo": codigo,
            "qtd": qtd,
            "leitura_manual": leitura_manual,
        }

        try:
            response = self.client.post("/leituras", json=body)
            response.raise_for_status()
        except Exception as exc:
            message = "Erro ao enviar dados para a API"
            mostrar_toast(titulo="TempoX", mensagem=f"Erro ao apontar o codigo: {codigo} no MES")
            if isinstance(exc, HTTPStatusError):
                message = handle_http_error(exc)
            logger.error(f"{message}: {exc}")
            raise Exception(message) from exc

        mostrar_toast(titulo="TempoX", mensagem=f"Codigo {codigo}, apontado com sucesso")
        return SuccessResponse(**response.json()).retorno
