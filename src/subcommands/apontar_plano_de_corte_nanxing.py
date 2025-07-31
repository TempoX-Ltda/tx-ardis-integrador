import logging
import os
from pathlib import Path
import time
import xml.etree.ElementTree as ET
from argparse import Namespace
import httpx
from httpx import Timeout
from datetime import datetime, timedelta

from src.arguments import parse_args
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_plano_de_corte_nanxing")


def extrair_dados_cycle(cycle):
    plate_id = None
    panel_state = None

    for field in cycle.findall("Field"):
        name = field.get("Name")
        value = field.get("Value")
        if name == "PlateID" and value:
            plate_id = value.replace(".nc", "")
        elif name == "PanelState":
            panel_state = value

    return plate_id, panel_state


def processar_cycle(cycle, layouts_apontados, tx, tipo_apontamento, caminho_pasta_tx):
    plate_id, panel_state = extrair_dados_cycle(cycle)
    logger.debug(f"Cycle com PlateID={plate_id}, PanelState={panel_state}")

    if panel_state == "4" and plate_id and plate_id not in layouts_apontados:
        caminho_arquivo_tx = os.path.join(caminho_pasta_tx, f"{plate_id}.tx")
        caminho_arquivo_erro = os.path.join(caminho_pasta_tx, f"{plate_id}_COM_ERRO.tx")
        caminho_arquivo_apontado = os.path.join(caminho_pasta_tx, f"{plate_id}_APONTADO.tx")

        if os.path.exists(caminho_arquivo_apontado) or os.path.exists(caminho_arquivo_erro):
            return

        if not os.path.exists(caminho_arquivo_tx):
            logger.warning(f"Arquivo {caminho_arquivo_tx} não encontrado. Ignorando...")
            try:
                with open(caminho_arquivo_erro, "w", encoding="utf-8") as f:
                    f.write("ERRO: Arquivo não encontrado.")
            except Exception as e:
                logger.error(f"Erro ao criar {caminho_arquivo_erro}: {e}")
            return

        try:
            with open(caminho_arquivo_tx, "r", encoding="utf-8") as f:
                primeira_linha = f.readline().strip()

            if not primeira_linha:
                raise ValueError("Arquivo está vazio")

            logger.info(f"Apontando plano de corte com layout: {primeira_linha}")

            def apontar():
                try:
                    tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        logger.warning("Token expirado. Realizando novo login...")
                        tx.login(tx.user, tx.password)
                        tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                    else:
                        raise

            # Aponta INÍCIO
            apontar()
            time.sleep(2)

            # Aponta FIM se necessário
            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Apontando fim do plano de corte: {primeira_linha}")
                apontar()

            logger.info(f"Apontamento do plano {primeira_linha} realizado com sucesso.")
            layouts_apontados.add(plate_id)
            os.rename(caminho_arquivo_tx, caminho_arquivo_apontado)
        except Exception as e:
            erro_msg = str(e)
            if "já está finalizado" in erro_msg:
                logger.warning(f"O plano já está finalizado.")
                layouts_apontados.add(plate_id)
            else:
                logger.error(f"Erro ao apontar plano {plate_id}: {e}")
                try:
                    with open(caminho_arquivo_tx, "r", encoding="utf-8") as f:
                        conteudo_original = f.read()

                    if not os.path.exists(caminho_arquivo_erro):
                        os.rename(caminho_arquivo_tx, caminho_arquivo_erro)
                        with open(caminho_arquivo_erro, "a", encoding="utf-8") as f:
                            f.write("\n")
                            f.write(f"ERRO: {e}")
                    else:
                        with open(caminho_arquivo_erro, "a", encoding="utf-8") as f_dest, open(caminho_arquivo_tx, "r", encoding="utf-8") as f_src:
                            f_dest.write("\n--- NOVA TENTATIVA ---\n")
                            f_dest.write(f_src.read().strip())
                            f_dest.write(f"\nERRO: {e}")
                        os.remove(caminho_arquivo_tx)

                except Exception as erro_renomear:
                    logger.error(f"Erro ao renomear ou escrever em {caminho_arquivo_erro}: {erro_renomear}")


def processar_sem_cycle(caminho_arquivo_tx_apontar_sem_cycle, layouts_apontados, tx, tipo_apontamento):
    if not caminho_arquivo_tx_apontar_sem_cycle or not os.path.exists(caminho_arquivo_tx_apontar_sem_cycle):
        return

    for nome_arquivo in os.listdir(caminho_arquivo_tx_apontar_sem_cycle):
        if not nome_arquivo.endswith(".tx"):
            continue

        if "_APONTADO" in nome_arquivo or "_COM_ERRO" in nome_arquivo:
            continue  # Ignora arquivos já processados ou com erro

        plate_id = nome_arquivo.replace(".tx", "")
        caminho_arquivo_tx = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, nome_arquivo)
        caminho_arquivo_apontado = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, f"{plate_id}_APONTADO.tx")
        caminho_arquivo_erro = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, f"{plate_id}_COM_ERRO.tx")

        try:
            with open(caminho_arquivo_tx, "r", encoding="utf-8") as f:
                primeira_linha = f.readline().strip()

            if not primeira_linha:
                raise ValueError("Arquivo está vazio")

            logger.info(f"Apontando plano de corte (sem cycle) com layout: {primeira_linha}")

            def apontar():
                try:
                    tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        logger.warning("Token expirado. Realizando novo login...")
                        tx.login(tx.user, tx.password)
                        tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
                    else:
                        raise

            # Aponta INÍCIO
            apontar()
            time.sleep(2)

            # Aponta FIM se necessário
            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Apontando fim do plano de corte (sem cycle): {primeira_linha}")
                apontar()

            logger.info(f"Apontamento do plano {primeira_linha} realizado com sucesso.")
            layouts_apontados.add(plate_id)
            os.rename(caminho_arquivo_tx, caminho_arquivo_apontado)

        except Exception as e:
            logger.error(f"Erro ao processar {caminho_arquivo_tx}: {e}")
            try:
                if not os.path.exists(caminho_arquivo_erro):
                    os.rename(caminho_arquivo_tx, caminho_arquivo_erro)
                    with open(caminho_arquivo_erro, "a", encoding="utf-8") as f:
                        f.write("\n")
                        f.write(f"ERRO: {e}")
                else:
                    with open(caminho_arquivo_erro, "a", encoding="utf-8") as f_dest, open(caminho_arquivo_tx, "r", encoding="utf-8") as f_src:
                        f_dest.write("\n--- NOVA TENTATIVA ---\n")
                        f_dest.write(f_src.read().strip())
                        f_dest.write(f"\nERRO: {e}")
                    os.remove(caminho_arquivo_tx)

            except Exception as erro_renomear:
                logger.error(f"Erro ao renomear ou escrever em {caminho_arquivo_erro}: {erro_renomear}")

def reapontar_planos_com_erro_nanxing(
    caminhos: "list[str]",
    tx: Tx,
    tipo_apontamento: str,
    dias_reapontamento: int,
):
    logger.info("Iniciando reapontamento de arquivos *_COM_ERRO.tx...")

    data_limite = datetime.now() - timedelta(days=dias_reapontamento)

    for caminho in caminhos:
        pasta = Path(caminho)
        if not pasta.exists():
            logger.warning(f"Caminho {pasta} não existe.")
            continue

        for arquivo_erro in pasta.glob("*_COM_ERRO.tx"):
            if datetime.fromtimestamp(arquivo_erro.stat().st_mtime) < data_limite:
                continue

            plate_id = arquivo_erro.stem.replace("_COM_ERRO", "")
            caminho_apontado = arquivo_erro.with_name(f"{plate_id}_APONTADO.tx")

            try:
                with open(arquivo_erro, "r", encoding="utf-8") as f:
                    linhas = f.readlines()
                    if not linhas:
                        logger.warning(f"{arquivo_erro.name} está vazio.")
                        continue
                    primeira_linha = linhas[0].strip()

                if not primeira_linha or primeira_linha.startswith("ERRO:"):
                    logger.warning(f"{arquivo_erro.name} sem conteúdo válido para reapontamento.")
                    continue

                logger.info(f"Reapontando plano de corte: {primeira_linha}")

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
                time.sleep(2)

                if tipo_apontamento == "INICIO_E_FIM":
                    logger.info(f"Reapontando fim do plano de corte: {primeira_linha}")
                    apontar()

                logger.info(f"Reapontamento do plano {primeira_linha} concluído com sucesso.")
                os.rename(arquivo_erro, caminho_apontado)

            except Exception as e:
                logger.error(f"Erro ao reapontar {arquivo_erro.name}: {e}")
                try:
                    with open(arquivo_erro, "a", encoding="utf-8") as f:
                        f.write("\n--- NOVA TENTATIVA ---\n")
                        f.write(f"ERRO: {e}")
                except Exception as erro_escrita:
                    logger.error(f"Erro ao escrever no arquivo {arquivo_erro.name}: {erro_escrita}")

def apontar_plano_de_corte_nanxing_subcommand(parsed_args: Namespace):
    logger.info("Iniciando apontamento dos planos no MES...")
    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=Timeout(parsed_args.timeout),
    )

    caminho_xml = parsed_args.caminho_arquivo
    tipo_apontamento = parsed_args.tipo_apontamento
    caminho_arquivo = parsed_args.caminho_arquivo_tempox
    caminho_arquivo_tx_apontar_sem_cycle = parsed_args.caminho_arquivo_tx_sem_registo_maquina
    layouts_apontados = set()
    ultimo_plate_em_processo = None

    while True:
        reapontar_planos_com_erro_nanxing(
            caminhos=[
                parsed_args.caminho_arquivo_tempox,
                parsed_args.caminho_arquivo_tx_sem_registo_maquina,
            ],
            tx=tx,
            tipo_apontamento=tipo_apontamento,
            dias_reapontamento=parsed_args.dias_reapontamento,
        )

        logger.info("Aguardando 20 segundos.")
        time.sleep(20)

        processar_sem_cycle(
            caminho_arquivo_tx_apontar_sem_cycle,
            layouts_apontados,
            tx,
            tipo_apontamento
        )

        if not os.path.exists(caminho_xml):
            logger.warning(f"Arquivo {caminho_xml} não encontrado. Aguardando 10 segundos...")
            time.sleep(10)
            continue

        try:
            tree = ET.parse(caminho_xml)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Erro ao parsear XML: {e}. Aguardando 10 segundos...")
            time.sleep(10)
            continue

        plate_id_atual = None

        for cycle in root.findall(".//Cycle"):
            plate_id, panel_state = extrair_dados_cycle(cycle)

            if panel_state == "2":
                plate_id_atual = plate_id

            # Processa normalmente se estiver como 4
            processar_cycle(cycle, layouts_apontados, tx, tipo_apontamento, caminho_arquivo)

        # Aponta o anterior se ele estava em processo e foi trocado por outro
        if ultimo_plate_em_processo and ultimo_plate_em_processo != plate_id_atual:
            logger.warning(f"PlateID anterior {ultimo_plate_em_processo} não foi finalizado. Apontando mesmo assim.")
            ciclo_falso = ET.Element("Cycle")
            ET.SubElement(ciclo_falso, "Field", Name="PlateID", Value=f"{ultimo_plate_em_processo}.nc")
            ET.SubElement(ciclo_falso, "Field", Name="PanelState", Value="4")
            processar_cycle(ciclo_falso, layouts_apontados, tx, tipo_apontamento, caminho_arquivo)

        ultimo_plate_em_processo = plate_id_atual
