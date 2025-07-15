import csv
import logging
import time
from argparse import Namespace
from pathlib import Path
from datetime import datetime, timedelta

import httpx

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_nanxing")



def reapontar_leituras_com_erro(diretorio: Path, tx: Tx, id_recurso: int, quantidade_dias_reapontamento: int):
    logger.info("Iniciando tentativa de reapontamento de arquivos com erro...")

    data_limite = datetime.now() - timedelta(days=quantidade_dias_reapontamento)

    arquivos_com_erro = [
        p for p in diretorio.glob("*_COM_ERRO.csv")
        if p.stat().st_mtime >= data_limite.timestamp()
    ]

    for caminho_com_erro in arquivos_com_erro:
        caminho_processado = caminho_com_erro.with_name(
            caminho_com_erro.stem.replace("_COM_ERRO", "_PROCESSADO_TEMPOX") + ".csv"
        )

        try:
            with caminho_com_erro.open("r", newline="", encoding="utf-8") as f_in:
                reader = csv.reader(f_in)
                linhas = list(reader)

            if not linhas:
                continue

            header = linhas[0]
            linhas = linhas[1:]

            linhas_ja_processadas = set()
            if caminho_processado.exists():
                with caminho_processado.open("r", newline="", encoding="utf-8") as f_in:
                    reader = csv.reader(f_in)
                    existentes = list(reader)
                    if existentes:
                        linhas_ja_processadas.update(tuple(row) for row in existentes[1:])

            novas_linhas_ok = []

            for linha in linhas:
                if (
                    not linha
                    or len(linha) < 2
                    or linha[0].strip().startswith("ERRO:")
                    or tuple(linha) in linhas_ja_processadas
                ):
                    continue

                try:
                    path = Path(linha[1])
                    ord = path.stem
                    if not ord:
                        logger.warning(f"ORD inválida na linha: {linha}")
                        continue

                    logger.info(f"Tentando reapontar leitura para: {ord}")

                    leitura = LeiturasPost(
                        id_recurso=id_recurso,
                        codigo=ord,
                        qtd=1,
                        leitura_manual=False,
                    )

                    try:
                        tx.leitura.nova_leitura(
                            id_recurso=leitura.id_recurso,
                            codigo=leitura.codigo,
                            qtd=leitura.qtd,
                            leitura_manual=leitura.leitura_manual,
                        )
                    except httpx.HTTPStatusError as e:
                        if e.response.status_code == 401:
                            logger.warning("Token expirado. Reautenticando...")
                            tx.login(tx.user, tx.password)
                            tx.leitura.nova_leitura(
                                id_recurso=leitura.id_recurso,
                                codigo=leitura.codigo,
                                qtd=leitura.qtd,
                                leitura_manual=leitura.leitura_manual,
                            )
                        else:
                            raise

                    novas_linhas_ok.append(linha)
                    logger.info(f"Linha reapontada com sucesso: {linha}")

                except Exception as e:
                    logger.error(f"Falha ao reapontar linha {linha}: {e}")
                    continue  # mantém no arquivo de erro

            # Anexa as reapontadas com sucesso ao arquivo processado
            if novas_linhas_ok:
                modo_abertura = "a" if caminho_processado.exists() else "w"
                with caminho_processado.open(modo_abertura, newline="", encoding="utf-8") as f_out:
                    writer = csv.writer(f_out)
                    if modo_abertura == "w":
                        writer.writerow(header)
                    writer.writerows(novas_linhas_ok)

                # Atualiza arquivo de erro com apenas as linhas que ainda falharam
                linhas_restantes = [linha for linha in linhas if linha not in novas_linhas_ok]
                with caminho_com_erro.open("w", newline="", encoding="utf-8") as f_out:
                    writer = csv.writer(f_out)
                    writer.writerow(header)
                    writer.writerows(linhas_restantes)

        except Exception as erro:
            logger.error(f"Erro ao reapontar arquivo {caminho_com_erro.name}: {erro}")

def apontar_leitura_furadeira_nanxing_subcommand(parsed_args: Namespace):
    logger.info("Iniciando processo de apontamento de leituras no MES...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=parsed_args.timeout,
    )

    diretorio = Path(parsed_args.caminho_arquivo)
    logger.info(f"Diretório configurado: {diretorio.resolve()}")

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
            logger.info("=== Novo ciclo de apontamento ===")
            logger.info("Listando todos os arquivos .csv encontrados no diretório:")

            todos_csv = list(diretorio.glob("*.csv"))
            for arq in todos_csv:
                logger.info(f"- {arq.name}")

            arquivos_csv = [
                p for p in todos_csv
                if "_PROCESSADO_TEMPOX" not in p.stem and "_COM_ERRO" not in p.stem
            ]
            logger.info("Arquivos filtrados para processamento:")
            for p in arquivos_csv:
                logger.info(f"→ {p.name}")

            for csv_entrada in arquivos_csv:
                logger.info(f"Processando arquivo: {csv_entrada.name}")

                nome_com_erro = csv_entrada.stem + "_COM_ERRO.csv"
                caminho_com_erro = csv_entrada.with_name(nome_com_erro)
                caminho_processado = csv_entrada.with_name(csv_entrada.stem + "_PROCESSADO_TEMPOX.csv")

                linhas_ok = []

                with csv_entrada.open("r", encoding="utf-8", errors="replace") as f_in:
                    linhas_brutas = f_in.read().replace('\x00', '')  # remove bytes nulos
                    reader = csv.reader(linhas_brutas.splitlines())
                    linhas = list(reader)
                    header = linhas[0]
                    linhas = linhas[1:]  # remove cabeçalho

                # Carrega linhas já processadas (caso arquivo exista)
                linhas_ja_processadas = set()
                if caminho_processado.exists():
                    with caminho_processado.open("r", newline="", encoding="utf-8") as f_in:
                        reader = csv.reader(f_in)
                        linhas_existentes = list(reader)
                        if linhas_existentes:
                            linhas_ja_processadas.update(tuple(row) for row in linhas_existentes[1:])  # ignora cabeçalho

                for linha in linhas:
                    if (
                        not linha
                        or len(linha) < 2
                        or linha[0].strip().startswith("ERRO:")
                        or tuple(linha) in linhas_ja_processadas
                    ):
                        continue  # ignora erro, linha vazia ou já processada

                    try:
                        try:
                            path = Path(linha[1])
                            ord = path.stem
                        except Exception:
                            logger.warning(f"Caminho inválido na linha: {linha}")
                            continue

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

                # Anexa somente as novas linhas OK ao arquivo de processados
                novas_linhas_ok = [linha for linha in linhas_ok if tuple(linha) not in linhas_ja_processadas]
                modo_abertura = "a" if caminho_processado.exists() else "w"
                with caminho_processado.open(modo_abertura, newline="", encoding="utf-8") as f_out:
                    writer = csv.writer(f_out)
                    if modo_abertura == "w":
                        writer.writerow(header)
                    writer.writerows(novas_linhas_ok)

                # Remove o arquivo original apenas se todas as linhas foram tratadas
                csv_entrada.unlink()

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        reapontar_leituras_com_erro(
            diretorio=diretorio,
            tx=tx,
            id_recurso=parsed_args.id_recurso,
            quantidade_dias_reapontamento=parsed_args.dias_reapontamento
        )

        logger.info("Aguardando próximo ciclo (30 segundos)...")
        time.sleep(30)
