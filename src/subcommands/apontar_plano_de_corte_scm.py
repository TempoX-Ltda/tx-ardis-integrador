import logging
import os
import time
from argparse import Namespace
from pathlib import Path

from httpx import Timeout
import httpx

from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_plano_de_corte_scm")

from datetime import datetime, timedelta


def reapontar_planos_com_erro_scm(
    caminho_pasta: Path,
    tx: Tx,
    tipo_apontamento: str,
    dias_reapontamento: int,
):
    logger.info("Iniciando reapontamento de planos SCM com erro...")

    data_limite = datetime.now() - timedelta(days=dias_reapontamento)

    if not caminho_pasta.exists() or not caminho_pasta.is_dir():
        logger.warning(f"Pasta {caminho_pasta} não existe ou não é diretório.")
        return

    arquivos_erro = sorted(caminho_pasta.glob("*_COM_ERRO.tx"))

    for arquivo_erro in arquivos_erro:
        if datetime.fromtimestamp(arquivo_erro.stat().st_mtime) < data_limite:
            continue

        nome_base = arquivo_erro.stem.replace("_COM_ERRO", "")
        caminho_apontado = arquivo_erro.with_name(f"{nome_base}_APONTADO.tx")

        try:
            with open(arquivo_erro, "r", encoding="utf-8") as f:
                linhas = f.readlines()
                if not linhas:
                    logger.warning(f"{arquivo_erro.name} está vazio.")
                    continue
                primeira_linha = linhas[0].strip()

            if not primeira_linha or primeira_linha.startswith("ERRO:"):
                logger.warning(f"{arquivo_erro.name} sem conteúdo válido.")
                continue

            logger.info(f"Reapontando plano SCM: {primeira_linha}")

            def apontar():
                try:
                    tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        logger.warning("Token expirado. Reautenticando...")
                        tx.login(tx.user, tx.password)
                        tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                    else:
                        raise

            # Aponta INÍCIO
            apontar()
            time.sleep(1)

            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Reapontando FIM do plano SCM: {primeira_linha}")
                apontar()

            logger.info(f"Reapontamento do plano {primeira_linha} concluído com sucesso.")
            os.rename(arquivo_erro, caminho_apontado)

        except Exception as e:
            logger.error(f"Erro ao reapontar {arquivo_erro.name}: {e}")
            try:
                with open(arquivo_erro, "a", encoding="utf-8") as f:
                    f.write("\n")
                    f.write(f"ERRO: {e}")
            except Exception as erro_arquivo:
                logger.error(f"Erro ao escrever erro no arquivo {arquivo_erro.name}: {erro_arquivo}")


def apontar_plano_de_corte_scm_subcommand(parsed_args: Namespace):
    logger.info("Iniciando apontamento dos planos SCM...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=Timeout(parsed_args.timeout),
    )

    caminho_pasta = Path(parsed_args.caminho_arquivo).resolve()
    tipo_apontamento = parsed_args.tipo_apontamento.upper()

    def apontar(layout: str):
        try:
            tx.plano_de_corte.apontar(codigo_layout=layout)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.warning("Token expirado. Realizando novo login...")
                tx.login(tx.user, tx.password)
                tx.plano_de_corte.apontar(codigo_layout=layout)
            else:
                raise

    while True:
        reapontar_planos_com_erro_scm(
            caminho_pasta=caminho_pasta,
            tx=tx,
            tipo_apontamento=tipo_apontamento,
            dias_reapontamento=parsed_args.dias_reapontamento,
        )
        logger.info("Aguardando 30 segundos...")
        time.sleep(30)

        if not caminho_pasta.exists() or not caminho_pasta.is_dir():
            logger.warning(f"Pasta {caminho_pasta} não encontrada ou não é diretório.")
            try:
                parent = caminho_pasta.parent
                logger.debug(f"Conteúdo de {parent}: {os.listdir(parent)}")
            except Exception as e:
                logger.error(f"Erro ao listar conteúdo: {e}")
            continue

        arquivos_tx = sorted(caminho_pasta.glob("*.tx"))

        if not arquivos_tx:
            logger.info("Nenhum arquivo .tx encontrado no diretório.")
            continue

        for arquivo in arquivos_tx:
            nome_base = arquivo.stem
            for sufixo in ["_APONTADO", "_COM_ERRO"]:
                if nome_base.endswith(sufixo):
                    nome_base = nome_base[: -len(sufixo)]
            caminho_apontado = arquivo.with_name(f"{nome_base}_APONTADO.tx")
            caminho_erro = arquivo.with_name(f"{nome_base}_COM_ERRO.tx")

            if caminho_apontado.exists() or caminho_erro.exists():
                logger.debug(f"Arquivo {arquivo.name} já processado. Pulando...")
                continue

            try:
                with open(arquivo, "r", encoding="utf-8") as f:
                    primeira_linha = f.readline().strip()

                if not primeira_linha:
                    logger.warning(f"{arquivo} está vazio. Ignorando...")
                    continue

                logger.info(f"Apontando plano SCM: {primeira_linha}")
                apontar(primeira_linha)

                if tipo_apontamento == "INICIO_E_FIM":
                    time.sleep(1)
                    logger.info(f"Apontando fim do plano de corte: {primeira_linha}")
                    apontar(primeira_linha)

                logger.info(f"Apontamento do plano {primeira_linha} realizado com sucesso.")
                os.rename(arquivo, caminho_apontado)

            except Exception as e:
                logger.error(f"Erro ao apontar plano {arquivo.name}: {e}")
                try:
                    os.rename(arquivo, caminho_erro)
                    with open(caminho_erro, "a", encoding="utf-8") as f:
                        f.write("\n")
                        f.write(f"ERRO: {e}")
                except Exception as erro_renomeio:
                    logger.error(f"Erro ao renomear/escrever erro: {erro_renomeio}")

