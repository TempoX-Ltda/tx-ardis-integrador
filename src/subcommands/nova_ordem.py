import csv
import logging
from argparse import Namespace
from io import TextIOWrapper
from typing import List

from httpx import Timeout
from pydantic import ValidationError

from src.tx.modules.cliente.types import (
    NovaOrdemParams,
    NovaOrdemRoteiroEIdUnico,
    NovoIdUnicoParams,
    NovoRoteiroParams,
)
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.nova_ordem")


def detect_dialect(text: str):
    know_delimiters = ";,\t"

    dialect = csv.Sniffer().sniff(text, delimiters=know_delimiters)

    return dialect


def parse_files(parsed_args: Namespace):
    ordens_file = parsed_args.ordens_file
    assert isinstance(ordens_file, TextIOWrapper)

    roteiros_file = parsed_args.roteiros_file
    assert isinstance(roteiros_file, TextIOWrapper)

    ids_unicos_file = parsed_args.ids_unicos_file
    assert isinstance(ids_unicos_file, TextIOWrapper)

    # Processando CSV das ORDENS
    logger.info("Processando csv das ordens: %s", ordens_file)

    first_line = ordens_file.readline()
    ordens_file.seek(0)

    ordens_file_csv = csv.DictReader(ordens_file, dialect=detect_dialect(first_line))

    assert (
        ordens_file_csv.fieldnames
    ), f"Não foi possível detectar os nomes das colunas no arquivo: {ordens_file}"

    lowercase_field_names = [field.lower() for field in ordens_file_csv.fieldnames]
    ordens_file_csv.fieldnames = lowercase_field_names

    ordens_roteiros_e_id_unicos: List[NovaOrdemRoteiroEIdUnico] = []

    for row in ordens_file_csv:
        try:
            NovaOrdemParams.model_validate(row)
        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar layout na linha {ordens_file_csv.line_num} "
                f"do arquivo {ordens_file}\n\n"
                f"Input: {row}\n\n"
                f"{exc}"
            ) from exc

        ordens_roteiros_e_id_unicos.append(
            NovaOrdemRoteiroEIdUnico.model_validate(
                {
                    **row,
                    "roteiros": [],
                    "ids_unicos": [],
                }
            )
        )

    # Processando CSV dos ROTEIROS
    logger.info("Processando csv dos roteiros: %s", roteiros_file)

    first_line = roteiros_file.readline()
    roteiros_file.seek(0)

    roteiros_file_csv = csv.DictReader(
        roteiros_file, dialect=detect_dialect(first_line)
    )

    assert (
        roteiros_file_csv.fieldnames
    ), f"Não foi possível detectar os nomes das colunas no arquivo: {roteiros_file}"

    lowercase_field_names = [field.lower() for field in roteiros_file_csv.fieldnames]
    roteiros_file_csv.fieldnames = lowercase_field_names

    for row in roteiros_file_csv:
        try:
            roteiro = NovoRoteiroParams.model_validate(row)
        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar layout na linha {roteiros_file_csv.line_num} "
                f"do arquivo {roteiros_file}\n\n"
                f"Input: {row}\n\n"
                f"{exc}"
            ) from exc

        ordem = next(
            (
                ordem
                for ordem in ordens_roteiros_e_id_unicos
                if ordem.id_ordem == roteiro.id_ordem
            ),
            None,
        )

        if not ordem:
            raise Exception(
                f"Ordem {roteiro.id_ordem} não encontrada no arquivo de ordens"
            )

        ordem.roteiros.append(roteiro)

    # Processando CSV dos IDS ÚNICOS
    logger.info("Processando csv dos ids únicos: %s", ids_unicos_file)

    first_line = ids_unicos_file.readline()
    ids_unicos_file.seek(0)

    ids_unicos_file_csv = csv.DictReader(
        ids_unicos_file, dialect=detect_dialect(first_line)
    )

    assert (
        ids_unicos_file_csv.fieldnames
    ), f"Não foi possível detectar os nomes das colunas no arquivo: {ids_unicos_file}"

    lowercase_field_names = [field.lower() for field in ids_unicos_file_csv.fieldnames]
    ids_unicos_file_csv.fieldnames = lowercase_field_names

    for row in ids_unicos_file_csv:
        try:
            id_unico = NovoIdUnicoParams.model_validate(row)
        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar layout na linha {ids_unicos_file_csv.line_num} "
                f"do arquivo {ids_unicos_file}\n\n"
                f"Input: {row}\n\n"
                f"{exc}"
            ) from exc

        ordem = next(
            (
                ordem
                for ordem in ordens_roteiros_e_id_unicos
                if ordem.id_ordem == id_unico.id_ordem
            ),
            None,
        )

        if not ordem:
            raise Exception(
                f"Ordem {id_unico.id_ordem} não encontrada no arquivo de ordens"
            )

        ordem.ids_unicos.append(id_unico)

    return ordens_roteiros_e_id_unicos


def nova_ordem_subcommand(parsed_args: Namespace):
    logger.info("Iniciando envio de ordens...")

    ordens_roteiros_e_id_unicos = parse_files(parsed_args)

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=Timeout(parsed_args.timeout),
    )

    tx.cliente.nova_ordem(ordens_roteiros_e_id_unicos)

    logger.info("Ordens enviadas com sucesso!")
