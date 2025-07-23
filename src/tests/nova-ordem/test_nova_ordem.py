import re
from pathlib import Path

import httpx
import pytest
from pytest_httpx import HTTPXMock

current_dir = Path(__file__).parent


@pytest.fixture
def mock_post_cliente_ordem(httpx_mock: HTTPXMock):
    def post_cliente_ordem(request: httpx.Request):
        valid_request_content = (current_dir / "valid_request_content.json").read_text()

        assert (
            request.content.decode("utf-8") == valid_request_content
        ), "Request content is not as expected. "

        return httpx.Response(
            200,
            json={"sucesso": True, "mensagem": "Ok", "metadata": None, "retorno": None},
        )

    httpx_mock.add_callback(
        post_cliente_ordem,
        url=re.compile(r".*/cliente/ordem"),
    )

    return True


def test_envia_nova_ordem(mock_login_sucess, mock_post_cliente_ordem):
    from src.arguments import parse_args
    from src.main import main

    files_folder = current_dir / "arquivos"

    args = [
        "--host",
        "http://192.168.3.15:6543/",
        "--user",
        "admin",
        "--password",
        "qwe123",
        "nova-ordem",
        "--ordens-file",
        str(files_folder / "ordens.csv"),
        "--roteiros-file",
        str(files_folder / "roteiros.csv"),
        "--ids-unicos-file",
        str(files_folder / "ids-unicos.csv"),
    ]

    parsed_args = parse_args(args)

    main(parsed_args)
