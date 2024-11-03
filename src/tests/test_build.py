import os
import subprocess
from pathlib import Path

import pytest
from PyInstaller.__main__ import run as pyinstaller_run

current_dir = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def build_path():
    """
    Compila o projeto e retorna o caminho do binário gerado.
    """

    # O escopo do fixture é module, ou seja, ele será executado uma única vez
    # para todos os testes desse arquivo.

    pyinstaller_run(["src/tx-mes-cli.spec"])

    if os.name == "nt":
        # Windows
        return "dist/tx-mes-cli.exe"
    elif os.name == "posix":
        # Linux
        return "dist/tx-mes-cli"
    else:
        raise NotImplementedError("Unsupported OS")


def test_binary_build(build_path):
    assert os.path.exists(build_path)


def test_binary_get_version(build_path):
    args = [
        build_path,
        "-v",
    ]

    try:
        res = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as exc:
        pytest.fail(f"Failed to run binary: {exc}")

    res.wait()

    error_msg = None
    if res.stderr is not None:
        error_msg = res.stderr.read().decode("utf-8")

    assert res.returncode == 0, error_msg
