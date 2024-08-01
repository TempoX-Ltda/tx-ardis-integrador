from argparse import ArgumentParser, Namespace
import base64
import json
import os
import pathlib
import logging
from logging.handlers import RotatingFileHandler
import tempfile
import sys
from typing import List
from httpx import HTTPStatusError, Timeout
import numpy as np
from pydantic import ConfigDict, ValidationError, validator
from typing import Optional
from pydantic import BaseModel

from pandas import read_csv
import PySimpleGUI as sg
from tx.modules.plano_de_corte.types import PlanoDeCorteCreateModel, PlanoDeCortePecasCreateModel, TipoMateriaPrima

from tx.tx import Tx

__version__ = "2.0.4"

sg.theme("Dark Blue 3")

log_file = tempfile.gettempdir() + "/send_ardis.log"

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
    "--error-on-duplicated-part",
    action="store_true",
    help="Impede o programa de continuar se o id único de uma peça já está inserido em algum plano ativo",
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

args = parser.parse_args()

logger.debug("Argumentos: %s", args)


class PlanoDeCortePecasCsvModel(BaseModel):
    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.coerce_numbers_to_str
    model_config = ConfigDict(coerce_numbers_to_str=True)

    codigo_layout: str
    qtd_cortada_no_layout: int
    id_unico_peca: Optional[int]
    id_ordem: Optional[int]
    tempo_corte_segundos: float

    # Custom validator here
    @validator('id_unico_peca', 'id_ordem', pre=True)
    def allow_none(cls, v):
        if v is None or np.isnan(v):
            return None
        else:
            return v


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


def show_error_popup(msg: str, exc: Exception):
    _ = sg.Popup(
        msg,
        str(exc),
        f"Log completo em: {log_file}",
        title="Erro",
        button_type=sg.POPUP_BUTTONS_OK,
    )


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
            logger.exception("")

            show_error_popup(
                f"Erro ao validar peça {row['id_unico_peca']}",
                exc
            )

            raise SystemExit from exc

    for idx, row in layouts_df.iterrows():

        try:
            row = PlanoDeCorteCsvModel.model_validate(row.to_dict())

        except ValidationError as exc:
            logger.exception("")

            show_error_popup(
                f"Erro ao validar layout {row['codigo_layout']}",
                exc
            )

            raise SystemExit from exc

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
            figure=get_figure_for_layout(args, row),
            pecas=[
                PlanoDeCortePecasCreateModel(
                    qtd_cortada_no_layout=peca.qtd_cortada_no_layout,
                    id_unico_peca=peca.id_unico_peca,
                    id_ordem=peca.id_ordem,
                    tempo_corte_segundos=peca.tempo_corte_segundos,
                ) for peca in pecas if peca.codigo_layout == row.codigo_layout
            ]
        )

        planos.append(plano)

    return planos


def main():
    try:
        tx = Tx(
            base_url=args.host,
            user=args.user,
            password=args.password,
            user_agent="send_ardis/" + __version__,
            default_timeout=Timeout(args.timeout),
        )
    except Exception as exc:
        logger.exception("")

        show_error_popup(
            "Não foi possível se conectar a API",
            exc
        )

        raise SystemExit from exc

    # Carrega os arquivos
    planos = parse_files(args)

    try:
        tx.plano_de_corte.novo_projeto(planos)
    except Exception as exc:
        logger.exception("")

        message = "Erro ao enviar dados para a API"

        if isinstance(exc, HTTPStatusError):

            response = exc.response.json()

            server_message = response.get("mensagem") or json.dumps(response)

            message = f"Erro {exc.response.status_code} ao enviar dados para a API\n\n{server_message}"

        show_error_popup(message, exc)

        raise SystemExit from exc

    _ = sg.Popup(
        "Envio finalizado!",
        f"Log completo em: {log_file}",
        "Essa mensagem irá fechar automaticamente em 5 segundos.",
        title="Envio finalizado",
        button_type=sg.POPUP_BUTTONS_OK,
        auto_close=True,
        auto_close_duration=5,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("")

        _ = sg.Popup(
            "Ocorreu um erro não esperado",
            str(exc),
            f"Log completo em: {log_file}",
            title="Erro não esperado",
            button_type=sg.POPUP_BUTTONS_OK,
        )

        raise SystemExit from exc
