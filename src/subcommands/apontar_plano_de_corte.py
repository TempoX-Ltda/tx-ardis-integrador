import logging
import time
from argparse import Namespace

from httpx import Timeout

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
        time.sleep(2)

        logger.info("Apontando o fim do plano de corte...")
        tx.plano_de_corte.apontar(
            codigo_layout=parsed_args.cod_layout,
        )

    logger.info("Apontamento realizado com sucesso!")
