import csv
import logging
import time
from argparse import Namespace
from pathlib import Path

import httpx

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_nanxing")


def apontar_leitura_furadeira_nanxing_subcommand(parsed_args: Namespace):
    logger.info("Iniciando processo de apontamento de leituras no MES...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=parsed_args.timeout,
    )

    diretorio = Path(parsed_args.caminho_arquivo)

    def tentar_enviar_leitura(leitura: LeiturasPost):
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
            arquivos_csv = [
                p for p in diretorio.glob("*.csv")
                if "_PROCESSADO_TEMPOX" not in p.stem and "_COM_ERRO_TEMPOX" not in p.stem
            ]

            for csv_entrada in arquivos_csv:
                nome_com_erro = csv_entrada.stem + "_COM_ERRO_TEMPOX.csv"
                caminho_com_erro = csv_entrada.with_name(nome_com_erro)

                linhas_ok = []

                with csv_entrada.open("r", newline="", encoding="utf-8") as f_in:
                    reader = csv.reader(f_in)
                    linhas = list(reader)
                    header = linhas[0]
                    linhas = linhas[1:]  # remove cabeçalho

                for linha in linhas:
                    if not linha or len(linha) < 2 or linha[0].strip().startswith("ERRO:"):
                        continue  # ignora linha de erro ou vazia
                    try:
                        path = Path(linha[1])
                        ord = path.stem

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

                        tentar_enviar_leitura(leitura)

                        linhas_ok.append(linha)
                        logger.info(f"Linha processada com sucesso: {linha}")

                    except Exception as e:
                        logger.error(f"Erro ao processar linha {linha}: {e}")
                        escrever_cabecalho = not caminho_com_erro.exists()
                        with caminho_com_erro.open("a", newline="", encoding="utf-8") as f_out:
                            writer = csv.writer(f_out)
                            if escrever_cabecalho:
                                writer.writerow(header)
                            writer.writerow(linha)
                            writer.writerow([f"ERRO: {str(e)}"])

                # Salvar apenas as linhas que deram certo
                caminho_processado = csv_entrada.with_name(csv_entrada.stem + "_PROCESSADO_TEMPOX.csv")
                try:
                    with caminho_processado.open("w", newline="", encoding="utf-8") as f_out:
                        writer = csv.writer(f_out)
                        writer.writerow(header)
                        writer.writerows(linhas_ok)
                    csv_entrada.unlink()
                except Exception as e:
                    logger.error(f"Erro ao salvar ou apagar arquivo original {csv_entrada.name}: {e}")

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        logger.info("Aguardando próximo ciclo (30 segundos)...")
        time.sleep(30)
