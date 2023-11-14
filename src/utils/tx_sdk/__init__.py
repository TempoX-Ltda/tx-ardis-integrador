import logging
from requests import Session
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class TxSDK:

    def __init__(self, host: str, user: str, password: str) -> None:
        
        from .plano_de_corte import PlanoDeCorte

        self.host = host

        self.session = Session()

        # Realiza login na API e salva a chave de acesso
        login = self.session.post(
            url = urljoin(host, 'auth/login'),
            json= {
                "user":     user,
                "password": password
            }
        )

        login.raise_for_status()

        logger.info('Sucesso no Login')

        session_key = login.json().get('retorno').get('key')

        self.session.headers['Authorization'] = f"Bearer {session_key}"

        self.plano_de_corte = PlanoDeCorte(self)

    def post(self, url, data=None, json=None, **kwargs):

        return self.session.post(
            url=urljoin(self.host, url),
            data=data,
            json=json,
            **kwargs
        )