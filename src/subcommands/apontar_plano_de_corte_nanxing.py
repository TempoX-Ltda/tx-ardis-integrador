import logging
import os
import time
import xml.etree.ElementTree as ET
from argparse import Namespace

from httpx import Timeout

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
        caminho_arquivo_apontado = os.path.join(
            caminho_pasta_tx, f"{plate_id}_APONTADO.tx"
        )

        if os.path.exists(caminho_arquivo_apontado):
            return

        if os.path.exists(caminho_arquivo_erro):
            return

        if not os.path.exists(caminho_arquivo_tx):
            logger.warning(f"Arquivo {caminho_arquivo_tx} não encontrado. Ignorando...")
            return

        try:
            with open(caminho_arquivo_tx, "r", encoding="utf-8") as f:
                primeira_linha = f.readline().strip()
        except Exception as e:
            logger.error(f"Erro ao ler {caminho_arquivo_tx}: {e}")
            return

        if not primeira_linha:
            logger.warning(f"Arquivo {caminho_arquivo_tx} está vazio. Ignorando...")
            return

        logger.info(f"Apontando plano de corte com layout: {primeira_linha}")
        try:
            tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
            time.sleep(2)  # espera 2 segundos para dar um tempo par ao layout
            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Apontando fim do plano de corte: {primeira_linha}")
                tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
            logger.info(f"Apontamento do plano {primeira_linha} realizado com sucesso.")
            layouts_apontados.add(plate_id)

            os.rename(caminho_arquivo_tx, caminho_arquivo_apontado)
        except Exception as e:
            if "já está finalizado" in str(e):
                layouts_apontados.add(plate_id)
            else:
                logger.error(f"Erro ao apontar plano {primeira_linha}: {e}")
                try:
                    os.rename(caminho_arquivo_tx, caminho_arquivo_erro)
                    with open(caminho_arquivo_erro, "a", encoding="utf-8") as f:
                        f.write("\n")
                        f.write(f"ERRO: {e}")
                except Exception as erro_renomear:
                    logger.error(
                        f"Erro ao renomear ou escrever em {caminho_arquivo_erro}: {erro_renomear}"
                    )
def processar_sem_cycle(caminho_arquivo_tx_apontar_sem_cycle, layouts_apontados, tx, tipo_apontamento):
    if not caminho_arquivo_tx_apontar_sem_cycle or not os.path.exists(caminho_arquivo_tx_apontar_sem_cycle):
        return

    for nome_arquivo in os.listdir(caminho_arquivo_tx_apontar_sem_cycle):
        if not nome_arquivo.endswith(".tx"):
            continue

        plate_id = nome_arquivo.replace(".tx", "")
        if plate_id.endswith("_APONTADO") or plate_id.endswith("_COM_ERRO"):
            continue

        caminho_arquivo_tx = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, nome_arquivo)
        caminho_arquivo_apontado = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, f"{plate_id}_APONTADO.tx")
        caminho_arquivo_erro = os.path.join(caminho_arquivo_tx_apontar_sem_cycle, f"{plate_id}_COM_ERRO.tx")

        if os.path.exists(caminho_arquivo_apontado) or os.path.exists(caminho_arquivo_erro):
            continue

        try:
            with open(caminho_arquivo_tx, "r", encoding="utf-8") as f:
                primeira_linha = f.readline().strip()
        except Exception as e:
            logger.error(f"Erro ao ler {caminho_arquivo_tx}: {e}")
            continue

        if not primeira_linha:
            logger.warning(f"Arquivo {caminho_arquivo_tx} está vazio. Ignorando...")
            continue

        logger.info(f"Apontando plano de corte (sem cycle) com layout: {primeira_linha}")
        try:
            tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
            time.sleep(2)
            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Apontando fim do plano de corte (sem cycle): {primeira_linha}")
                tx.plano_de_corte.apontar(codigo_layout=primeira_linha)
            logger.info(f"Apontamento do plano {primeira_linha} realizado com sucesso.")
            layouts_apontados.add(plate_id)
            os.rename(caminho_arquivo_tx, caminho_arquivo_apontado)
        except Exception as e:
            if "já está finalizado" in str(e):
                layouts_apontados.add(plate_id)
            else:
                logger.error(f"Erro ao apontar plano {primeira_linha}: {e}")
                try:
                    os.rename(caminho_arquivo_tx, caminho_arquivo_erro)
                    with open(caminho_arquivo_erro, "a", encoding="utf-8") as f:
                        f.write("\n")
                        f.write(f"ERRO: {e}")
                except Exception as erro_renomear:
                    logger.error(
                        f"Erro ao renomear ou escrever em {caminho_arquivo_erro}: {erro_renomear}"
                    )

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
