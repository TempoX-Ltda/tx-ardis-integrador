from httpx import Client
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from ..utils.commons import SuccessResponse


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

    response.raise_for_status()

    return SuccessResponse[LoginReturn](**response.json()).retorno
