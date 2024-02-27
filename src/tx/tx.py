import httpx

from .modules._auth import login
from .modules.plano_de_corte import PlanoDeCorte


class Tx:
    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        default_timeout: httpx.Timeout = httpx.Timeout(30.0),
        user_agent: str = "tx-cli/",
    ):
        self.base_url = base_url
        self.user = user
        self.password = password

        self.client = httpx.Client(
            base_url=base_url,
            timeout=default_timeout,
        )

        login_data = login(self.client, user, password)

        if not login_data.key:
            raise Exception("Login failed")

        self.client.headers = httpx.Headers(
            {
                "Authorization": f"Bearer {login_data.key}",
                "User-Agent": user_agent,
            }
        )

        # submodules
        self.plano_de_corte = PlanoDeCorte(self.client)
