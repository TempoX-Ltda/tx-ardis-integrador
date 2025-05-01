import logging

import httpx

from src.tx.exceptions import CannotLoginError
from src.tx.modules._auth import login
from src.tx.modules.cliente import Cliente
from src.tx.modules.leituras import Leitura
from src.tx.modules.plano_de_corte import PlanoDeCorte
from src.utils import get_version

logger = logging.getLogger("src.tx.tx")


class Tx:
    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        default_timeout: httpx.Timeout = httpx.Timeout(30.0),
    ):
        self.base_url = base_url
        self.user = user
        self.password = password

        self.client = httpx.Client(
            base_url=base_url,
            timeout=default_timeout,
        )

        logger.info("Obtendo credênciais de acesso a API...")
        login_data = login(self.client, user, password)

        if not login_data.key:
            raise CannotLoginError(
                "Não foi possível realizar login no sistema MES. "
                "A resposta da API não contém a chave de autenticação."
            )

        self.client.headers = httpx.Headers(
            {
                "Authorization": f"Bearer {login_data.key}",
                "User-Agent": "tx-mes-cli/" + get_version(),
            }
        )

        logger.info("Credênciais obtidas com sucesso!")

        # submodules
        self.plano_de_corte = PlanoDeCorte(self.client)
        self.cliente = Cliente(self.client)
        self.leitura = Leitura(self.client)
