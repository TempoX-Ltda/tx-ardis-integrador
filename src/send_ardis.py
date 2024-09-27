from argparse import ArgumentParser, Namespace
import base64
import json
from math import isnan
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
import tempfile
import sys
import threading
import time
from typing import Any, List, Optional
from typing_extensions import Annotated
from httpx import HTTPStatusError, Timeout
from pydantic import BeforeValidator, ConfigDict, ValidationError, model_validator

from pydantic import BaseModel

from pandas import read_csv
from tx.modules.plano_de_corte.types import (
    PlanoDeCorteCreateModel,
    PlanoDeCortePecasCreateModel,
    TipoMateriaPrima,
)

if os.name == 'nt':  # Verifica se o sistema operacional é Windows
    import win32gui
    import win32con
    import ctypes

    def set_console_active():
        # Obtém o identificador da janela do console atual
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            # Garante que a janela esteja visível
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            # Coloca a janela em primeiro plano
            win32gui.SetForegroundWindow(hwnd)


from tx.tx import Tx

__version__ = "2.2.1"

parser = ArgumentParser(
    prog="send_ardis",
    description="Insere as informações das otimizações do Ardis no sistema GTRP.",
)

parser.add_argument(
    "-v", "--version", action="version", version="%(prog)s " + __version__
)

parser.add_argument(
    "--host",
    type=str,
    help="Endereço IP da API Ex.: http://localhost:6543/",
    required=True,
)

parser.add_argument(
    "-u",
    "--user",
    type=str,
    help="Usuario que será utilizado para acessar a API",
    required=True,
)

parser.add_argument(
    "-p", "--password", type=str, help="Senha do usuário", required=True
)

parser.add_argument(
    "--layouts-file",
    type=open,
    help="Arquivo csv contendo as informações de cada layout",
    required=True,
)

parser.add_argument(
    "--parts-file",
    type=open,
    help="Arquivo csv contendo as informações de peça de cada layout",
    required=True,
)

parser.add_argument(
    "--sep", type=str, help="Separador de campos dos arquivos csv", default=","
)

parser.add_argument(
    "--figures-directory",
    type=pathlib.Path,
    help="Diretório onde as figures de cada plano serão buscadas. O nome de cada arquivo deve ser igual ao código do plano, com extensão .png",
)

parser.add_argument(
    "--timeout",
    type=float,
    help="Tempo limite para as requisições HTTP, em segundos.",
    default=None,
)

parser.add_argument(
    "--log-file",
    type=str,
    help="Caminho para o arquivo de log. Se não informado, o arquivo será temporário.",
    default=tempfile.gettempdir() + "/send_ardis.log",
)

args = parser.parse_args()

log_file = args.log_file
log_dir = os.path.dirname(log_file)

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

formatter = logging.Formatter(
    "%(asctime)s,%(msecs)d | %(name)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_log_handler = RotatingFileHandler(
    log_file, maxBytes=100 * 1024 * 1024, backupCount=2
)
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(formatter)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

logger.addHandler(file_log_handler)
logger.addHandler(stdout_handler)


logger.debug("Argumentos: %s", args)


def coerce_nan_to_none(x: Any) -> Any:
    try:
        if isnan(x):
            return None
    except TypeError as exc:
        raise ValueError(f"Erro ao converter {x} para None") from exc

    return x


class PlanoDeCortePecasCsvModel(BaseModel):
    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.coerce_numbers_to_str
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id_ordem: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]
    id_unico_peca: Annotated[Optional[int],
                             BeforeValidator(coerce_nan_to_none)]
    codigo_layout: str
    qtd_cortada_no_layout: int
    tempo_corte_segundos: float

    # Se `recorte` for true, a peça será considerada como recorte
    # nesse caso `id_ordem` e `id_unico_peca` podem ser None
    recorte: bool

    @model_validator(mode="after")
    def verifica_recorte(self):
        if self.recorte:
            if self.id_ordem is not None or self.id_unico_peca is not None:
                raise ValueError(
                    "Peça de recorte não deve ter id_ordem ou id_unico_peca"
                )

        return self


class PlanoDeCorteCsvModel(BaseModel):
    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.coerce_numbers_to_str
    model_config = ConfigDict(coerce_numbers_to_str=True)

    codigo_layout: str
    descricao_material: str
    id_recurso: int
    mm_comp_linear: float
    mm_comprimento: float
    mm_largura: float
    nome_projeto: str
    perc_aproveitamento: float
    perc_sobras: float
    tipo: TipoMateriaPrima
    codigo_lote: str
    qtd_chapas: int
    tempo_estimado_seg: float


def get_figure_for_layout(args: Namespace, plano: PlanoDeCorteCsvModel):
    figure_path = os.path.join(
        str(args.figures_directory)
        .strip('"')
        .strip("'"),  # Remove ' and/or " from figures_directory
        f"{plano.codigo_layout}.png",
    )

    if not os.path.exists(figure_path):
        logger.warning('O arquivo "%s" não foi encontrado', figure_path)

        return None

    with open(figure_path, "rb") as figure_img:
        return base64.b64encode(figure_img.read()).decode("utf-8")


def parse_files(args: Namespace):
    logger. info("Lendo arquivos csv...")

    layouts_df = read_csv(args.layouts_file, sep=args.sep)
    parts_df = read_csv(args.parts_file, sep=args.sep)

    logger.debug("Layouts: %s", layouts_df)
    logger.debug("Parts: %s", parts_df)

    pecas: List[PlanoDeCortePecasCsvModel] = []
    planos: List[PlanoDeCorteCreateModel] = []

    for idx, row in parts_df.iterrows():
        try:
            peca = PlanoDeCortePecasCsvModel.model_validate(row.to_dict())
            pecas.append(peca)

        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar peça na linha {idx}: {row.to_dict()}") from exc

    logger.info("Arquivo %s lido com sucesso", args.parts_file.name)

    for idx, row in layouts_df.iterrows():
        try:
            row = PlanoDeCorteCsvModel.model_validate(row.to_dict())

        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar layout na linha {idx}: {row.to_dict()}") from exc

        # Pode incluir recorte, que não devem ser tratados como peças
        todas_as_pecas_desse_plano = [
            peca for peca in pecas if peca.codigo_layout == row.codigo_layout
        ]

        # Conta quantas peças são recortes
        qtd_recortes = len(
            [peca for peca in todas_as_pecas_desse_plano if peca.recorte]
        )

        # Mantem somente as peças que não são recortes
        pecas_desse_plano = [
            peca for peca in todas_as_pecas_desse_plano if not peca.recorte
        ]

        figure = get_figure_for_layout(args, row)

        plano = PlanoDeCorteCreateModel(
            codigo_layout=row.codigo_layout,
            codigo_lote=row.codigo_lote,
            descricao_material=row.descricao_material,
            id_recurso=row.id_recurso,
            mm_comp_linear=row.mm_comp_linear,
            mm_comprimento=row.mm_comprimento,
            mm_largura=row.mm_largura,
            nome_projeto=row.nome_projeto,
            perc_aproveitamento=row.perc_aproveitamento,
            perc_sobras=row.perc_sobras,
            qtd_chapas=row.qtd_chapas,
            tempo_estimado_seg=row.tempo_estimado_seg,
            tipo=row.tipo,
            qtd_recortes=qtd_recortes,
            figure=figure,
            pecas=[
                PlanoDeCortePecasCreateModel(
                    qtd_cortada_no_layout=peca.qtd_cortada_no_layout,
                    id_unico_peca=peca.id_unico_peca,
                    id_ordem=peca.id_ordem,
                    tempo_corte_segundos=peca.tempo_corte_segundos,
                )
                for peca in pecas_desse_plano
            ],
        )

        planos.append(plano)

    logger.info("Arquivo %s lido com sucesso", args.layouts_file.name)

    return planos


def main():

    logger.info("Iniciando envio de arquivos para o MES")

    logger.info("Conectando a API...")
    try:
        tx = Tx(
            base_url=args.host,
            user=args.user,
            password=args.password,
            user_agent="send_ardis/" + __version__,
            default_timeout=Timeout(args.timeout),
        )
    except Exception as exc:
        raise Exception("Não foi possível se conectar a API") from exc

    logger.info("Conectado a API")

    # Carrega os arquivos
    planos = parse_files(args)

    logger.info("Enviando projeto para a API...")
    try:
        tx.plano_de_corte.novo_projeto(planos)
    except Exception as exc:
        message = "Erro ao enviar dados para a API"

        if isinstance(exc, HTTPStatusError):
            response = exc.response.json()

            server_message = response.get("mensagem") or json.dumps(response)

            message = f"Erro {exc.response.status_code} ao enviar dados para a API:\n{server_message}"

        raise Exception(message) from exc

    logger.info("Envio finalizado!")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("")

        if os.name == 'nt':  # Torna a janela do console ativa se estiver no Windows
            try:
                set_console_active()
            except Exception as exc:
                logger.error("Erro ao ativar janela do console: %s", exc)

        logger.info("Log completo em: %s", log_file)
        logger.info("Pressione ENTER para encerrar o programa")
        input()

        sys.exit(1)

    if os.name == 'nt':  # Torna a janela do console ativa se estiver no Windows
        try:
            set_console_active()
        except Exception as exc:
            logger.error("Erro ao ativar janela do console: %s", exc)

    logger.info("Log completo em: %s", log_file)

    logger.info("Finalizando automaticamente em 10 segundos...")
    logger.info("Pressione ENTER para finalizar agora")

    # Aguarda 10 segundos ou até o usuário pressionar ENTER
    input_thread = threading.Thread(target=input)
    input_thread.daemon = True
    input_thread.start()
    start_time = time.time()
    while True:
        if not input_thread.is_alive():
            break
        if time.time() - start_time >= 10:
            break
        time.sleep(0.1)

    sys.exit(0)
