import json
import logging
from datetime import datetime
from typing import Any, Optional

from httpx import Client
from pydantic import BaseModel

from src.tx.exceptions import CannotLoginError
from src.tx.utils.commons import SuccessResponse

logger = logging.getLogger("src.tx.modules._auth")


class LoginReturn(BaseModel):
    id: int
    inicio: datetime
    validade: datetime
    ip: Optional[str]
    created_on: datetime
    modified_on: datetime
    login: str
    key: str
    usuario: Optional[Any]


def login(client: Client, user: str, password: str):
    response = client.post("/auth/login", json={"user": user, "password": password})

    try:
        response.raise_for_status()
    except Exception as e:
        raise CannotLoginError(
            f"Não foi possível realizar login no sistema MES. "
            f"Retorno da API: {response.text}"
        ) from e

    try:
        json_response = response.json()
    except json.decoder.JSONDecodeError as e:
        logger.exception('Erro ao decodificar a resposta da API: "%s"', response.text)

        raise e

    return SuccessResponse[LoginReturn](**json_response).retorno
