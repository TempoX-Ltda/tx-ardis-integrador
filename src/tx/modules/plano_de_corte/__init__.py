from httpx import Client

from .pecas import Pecas


class PlanoDeCorte:
    def __init__(self, client: Client):
        self.client = client

        self.pecas = Pecas(self.client)
