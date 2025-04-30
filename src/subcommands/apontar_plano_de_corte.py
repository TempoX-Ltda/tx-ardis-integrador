import base64
import logging
import os
from argparse import Namespace
from math import isnan
from typing import Any, List, Optional

from httpx import Timeout
from pandas import read_csv
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Annotated

from src.tx.modules.plano_de_corte.types import (
    PlanoDeCorteCreateModel,
    PlanoDeCortePecasCreateModel,
    TipoMateriaPrima,
)
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_plano_de_corte")


def apontar_plano_de_corte_subcommand(parsed_args: Namespace):
    logger.info("Iniciando apontamento dos planos no MES...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=Timeout(parsed_args.timeout),
    )

    tx.plano_de_corte.apontar(
        codigo_layout=parsed_args.cod_layout,
    )

    if parsed_args.tipo_apontamento == "INICIO_E_FIM":
        logger.info("Apontando o fim do plano de corte...")
        tx.plano_de_corte.apontar(
            codigo_layout=parsed_args.cod_layout,
        )

    logger.info("Apontamento realizado com sucesso!")
