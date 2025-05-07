import json
from pathlib import Path

from httpx import HTTPStatusError
from plyer import notification


def get_version():
    current_dir = Path(__file__).parent

    version_file = current_dir / "version"

    return version_file.read_text().strip()


def handle_http_error(exc: HTTPStatusError):
    response = exc.response

    try:
        response_json = response.json()
        server_message = response_json.get("mensagem") or json.dumps(response_json)

    except json.decoder.JSONDecodeError:
        server_message = response.text

    message = (
        f"Erro {response.status_code} ao enviar dados para a API:\n" f"{server_message}"
    )

    return message


def mostrar_toast(titulo: str, mensagem: str):
    notification.notify(title=titulo, message=mensagem, timeout=5) # type: ignore funciona mas da erro
