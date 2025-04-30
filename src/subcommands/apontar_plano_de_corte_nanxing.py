import logging
import os
from argparse import Namespace
import time
from httpx import Timeout
import xml.etree.ElementTree as ET

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


def processar_cycle(cycle, layouts_apontados, tx, tipo_apontamento):
    plate_id, panel_state = extrair_dados_cycle(cycle)
    logger.debug(f"Cycle com PlateID={plate_id}, PanelState={panel_state}")

    if panel_state == "4" and plate_id and plate_id not in layouts_apontados:
        logger.info(f"Apontando plano de corte: {plate_id}")
        try:
            tx.plano_de_corte.apontar(codigo_layout=plate_id)
            # Aguarda 2 segundos para o plano não ficar com tempo zerado
            time.sleep(2)
            if tipo_apontamento == "INICIO_E_FIM":
                logger.info(f"Apontando fim do plano de corte: {plate_id}")
                tx.plano_de_corte.apontar(codigo_layout=plate_id)
            logger.info(f"Apontamento do plano {plate_id} realizado com sucesso.")
            layouts_apontados.add(plate_id)
        except Exception as e:
            if 'já está finalizado' in str(e):
                layouts_apontados.add(plate_id)
            else:
                logger.error(f"Erro ao apontar plano {plate_id}: {e}")


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
    layouts_apontados = set()

    while True:
        logger.info("Aguardando 1 segundo.")
        time.sleep(1)

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

        for cycle in root.findall(".//Cycle"):
            processar_cycle(cycle, layouts_apontados, tx, tipo_apontamento)
