import httpx

from .modules._auth import login
from .modules.plano_de_corte import PlanoDeCorte


class Tx:
    def __init__(self, base_url: str, user: str, password: str):
        self.base_url = base_url
        self.user = user
        self.password = password

        self.client = httpx.Client(
            base_url=base_url,
        )

        login_data = login(self.client, user, password)

        if not login_data.key:
            raise Exception("Login failed")

        self.client.headers = [("Authorization", f"Bearer {login_data.key}")]

        # submodules
        self.plano_de_corte = PlanoDeCorte(self.client)
