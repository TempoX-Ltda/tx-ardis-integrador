import csv
import logging
import time
from argparse import Namespace
from pathlib import Path

from httpx import Timeout

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_scm_pratika")


def obter_ultimo_csv(diretorio: Path) -> Path:
    arquivos_csv = list(diretorio.glob("*.csv"))
    if not arquivos_csv:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado.")

    return max(arquivos_csv, key=lambda p: p.stat().st_mtime)


def carregar_linhas_processadas(arquivo_processado: Path) -> set:
    if not arquivo_processado.exists():
        return set()

    with arquivo_processado.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return set(tuple(row) for row in reader)


def apontar_leitura_furadeira_scm_pratika_subcommand(parsed_args: Namespace):
    diretorio = Path(parsed_args.diretorio_csv)
    timeout = Timeout(parsed_args.timeout)

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=timeout,
    )

    while True:
        try:
            csv_entrada = obter_ultimo_csv(diretorio)
            nome_processado = csv_entrada.stem + "_PROCESSADO_TEMPOX.csv"
            caminho_processado = csv_entrada.with_name(nome_processado)

            linhas_processadas = carregar_linhas_processadas(caminho_processado)

            with csv_entrada.open("r", newline="", encoding="utf-8") as f_in:
                reader = csv.reader(f_in)
                linhas = list(reader)[1:]  # Ignora cabeçalho

            with caminho_processado.open("a", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)

                for linha in linhas:
                    if tuple(linha) in linhas_processadas:
                        logger.debug("Linha já processada, ignorando.")
                        continue

                    try:
                        path = Path(linha[1])
                        nome_arquivo = path.stem

                        if not nome_arquivo:
                            logger.warning(
                                f"Nome do arquivo inválido na linha: {linha}"
                            )
                            continue

                        logger.info(f"Enviando leitura para API: {nome_arquivo}")

                        leitura = LeiturasPost(
                            id_recurso=parsed_args.id_recurso,
                            codigo=nome_arquivo,
                            qtd=parsed_args.qtd,
                            leitura_manual=False,
                        )

                        tx.leitura.nova_leitura(
                            id_recurso=leitura.id_recurso,
                            codigo=leitura.codigo,
                            qtd=leitura.qtd,
                            leitura_manual=leitura.leitura_manual,
                        )

                        writer.writerow(linha)
                        logger.info(f"Linha processada com sucesso: {linha}")

                    except Exception as e:
                        logger.error(f"Erro ao processar linha {linha}: {e}")

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        logger.info("Aguardando próximo ciclo (5 segundos)...")
        time.sleep(5)
