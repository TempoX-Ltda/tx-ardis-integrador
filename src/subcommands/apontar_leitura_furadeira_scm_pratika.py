import csv
import logging
import time
from argparse import Namespace
from pathlib import Path

import httpx

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_scm_pratika")


def obter_pasta_ano_mais_recente(diretorio: Path) -> Path:
    subpastas_ano = [p for p in diretorio.iterdir() if p.is_dir() and p.name.isdigit()]
    if not subpastas_ano:
        raise FileNotFoundError(f"Nenhuma subpasta de ano encontrada em {diretorio}")
    return max(subpastas_ano, key=lambda p: int(p.name))


def normalizar_linha(linha):
    return tuple(campo.strip() for campo in linha)


def carregar_linhas_processadas(arquivo_processado: Path):
    if not arquivo_processado.exists():
        return set()
    with arquivo_processado.open("r", newline="", encoding="latin1") as f:
        reader = csv.reader(f)
        return set(normalizar_linha(row) for row in reader)


def carregar_todas_linhas_com_erro(pasta_ano: Path):
    linhas_com_erro = set()
    for arquivo in pasta_ano.glob("*_COM_ERRO_TEMPOX.pro"):
        with arquivo.open("r", newline="", encoding="latin1") as f:
            reader = csv.reader(f)
            linhas_com_erro.update(normalizar_linha(row) for row in reader)
    return linhas_com_erro


def apontar_leitura_furadeira_scm_pratika_subcommand(parsed_args: Namespace):
    logger.info("Iniciando processo de apontamento de leituras no MES...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=parsed_args.timeout,
    )

    diretorio = Path(parsed_args.caminho_arquivo)

    def enviar_leitura(leitura: LeiturasPost):
        try:
            tx.leitura.nova_leitura(
                id_recurso=leitura.id_recurso,
                codigo=leitura.codigo,
                qtd=leitura.qtd,
                leitura_manual=leitura.leitura_manual,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Token expirado. Realizando novo login...")
                tx.login(tx.user, tx.password)
                tx.leitura.nova_leitura(
                    id_recurso=leitura.id_recurso,
                    codigo=leitura.codigo,
                    qtd=leitura.qtd,
                    leitura_manual=leitura.leitura_manual,
                )
            else:
                raise

    while True:
        try:
            pasta_ano = obter_pasta_ano_mais_recente(diretorio)
            linhas_com_erro_globais = carregar_todas_linhas_com_erro(pasta_ano)

            arquivos_pro_validos = [
                p for p in pasta_ano.glob("*.pro")
                if "_COM_ERRO_TEMPOX" not in p.stem and "_PROCESSADO_TEMPOX" not in p.stem
            ]

            if not arquivos_pro_validos:
                logger.info("Nenhum arquivo .pro válido para processar.")
                time.sleep(30)
                continue

            for csv_entrada in sorted(arquivos_pro_validos, key=lambda p: p.stat().st_mtime):
                caminho_processado = csv_entrada.with_name(csv_entrada.stem + "_PROCESSADO_TEMPOX.pro")
                caminho_com_erro = csv_entrada.with_name(csv_entrada.stem + "_COM_ERRO_TEMPOX.pro")

                linhas_processadas = carregar_linhas_processadas(caminho_processado)

                with csv_entrada.open("r", newline="", encoding="latin1") as f_in:
                    reader = csv.reader(f_in)
                    linhas = list(reader)[1:]  # Ignora cabeçalho

                for linha in linhas:
                    linha_normalizada = normalizar_linha(linha)
                    if linha_normalizada in linhas_processadas or linha_normalizada in linhas_com_erro_globais:
                        continue

                    try:
                        tratando_ord = linha[1].strip().strip('"')
                        ord = Path(tratando_ord.split("\\")[-1]).stem

                        if not ord:
                            logger.warning(f"ORD inválida na linha: {linha}")
                            continue

                        logger.info(f"Enviando leitura para API: {ord}")

                        leitura = LeiturasPost(
                            id_recurso=parsed_args.id_recurso,
                            codigo=ord,
                            qtd=1,
                            leitura_manual=False,
                        )

                        enviar_leitura(leitura)

                        with caminho_processado.open("a", newline="", encoding="latin1") as f_out:
                            writer_arquivo_processado = csv.writer(f_out)
                            writer_arquivo_processado.writerow(linha_normalizada)
                            logger.info(f"Linha processada com sucesso: {linha}")

                    except Exception as e:
                        logger.error(f"Erro ao processar linha {linha}: {e}")
                        with caminho_com_erro.open("a", newline="", encoding="latin1") as f_out:
                            writer_arquivo_com_erro = csv.writer(f_out)
                            writer_arquivo_com_erro.writerow(linha_normalizada)

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        logger.info("Aguardando próximo ciclo (30 segundos)...")
        time.sleep(30)
