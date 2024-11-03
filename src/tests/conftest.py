import re

import pytest
from pytest_httpx import HTTPXMock


@pytest.fixture
def mock_login_sucess(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=re.compile(r".*/auth/login"),
        status_code=200,
        json={
            "sucesso": True,
            "mensagem": "OK",
            "metadata": {"page": 0, "page_size": 100, "last_page": None},
            "retorno": {
                "id": 3,
                "login": "admin",
                "inicio": "2024-11-02T21:49:32.873144",
                "validade": "2024-11-03T03:49:32.873144",
                "key": "fc174dab-6b0e-4705-bcd4-975760776572",
                "ip": None,
                "created_on": "2024-11-02T21:49:32.873144",
                "modified_on": "2024-11-02T21:49:32.873144",
                "usuario": {
                    "id": 1,
                    "nome": "Administrador",
                    "email": "contato@tempox.com.br",
                    "inativo": False,
                    "id_referencia": "0",
                    "login": "admin",
                    "id_setor": None,
                    "telas": [],
                    "created_on": "2024-11-02T21:45:09.353745",
                    "modified_on": "2024-11-02T21:47:28.305388",
                    "permissoes": [],
                },
            },
        },
    )
