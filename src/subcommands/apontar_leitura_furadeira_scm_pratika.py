import csv
import logging
import os
import re
import time
from argparse import Namespace
from pathlib import Path
from typing import Optional

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_scm_pratika")


def obter_ultimo_pro(diretorio: Path) -> Path:
    arquivos_pro = [
        p for p in diretorio.glob("*.pro")
        if "_PROCESSADO_SCM_PRATIKA" not in p.stem
    ]
    if not arquivos_pro:
        raise FileNotFoundError("Nenhum arquivo .pro encontrado.")

    return max(arquivos_pro, key=lambda p: p.stat().st_mtime)


def extrair_codigos_ordem(arquivo_pro: Path) -> list:
    padrao_ordem = re.compile(r"ORD\d+#\d+")
    codigos_ordem = []
    
    with arquivo_pro.open("r", encoding="utf-8") as f:
        for linha in f:
            if ".PGM" in linha.upper():
                match = padrao_ordem.search(linha)
                if match:
                    codigos_ordem.append(match.group(0))  # Adiciona o código encontrado à lista
                    
    return codigos_ordem


def carregar_codigos_processados_scm_pratika(arquivo_processado: Path) -> set:
    if not arquivo_processado.exists():
        return set()

    with arquivo_processado.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        codigos_processados = set()
        for row in reader:
            # Supondo que a primeira coluna seja o caminho do arquivo
            # e as demais sejam os códigos de ordem
            codigos_processados.update(row[1:])  # Adiciona os códigos de ordem (ignora a primeira coluna)
        return codigos_processados


def apontar_leitura_furadeira_scm_pratika_subcommand(parsed_args: Namespace):
    logger.info("Iniciando leitura dos planos da furadeira SCM Pratika...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=parsed_args.timeout,
    )

    diretorio = Path(parsed_args.caminho_arquivo)

    while True:
        time.sleep(5)
        try:
            arquivo_pro = obter_ultimo_pro(diretorio)
            nome_processado = arquivo_pro.stem + "_PROCESSADO_SCM_PRATIKA.pro"
            caminho_processado = arquivo_pro.with_name(nome_processado)

            codigos_processados = carregar_codigos_processados_scm_pratika(caminho_processado)

            codigos_ordem = extrair_codigos_ordem(arquivo_pro)
            if not codigos_ordem:
                logger.warning(f"Não foi possível extrair códigos de ordem do arquivo: {arquivo_pro.name}")
                continue

            # Verifica se todos os códigos de ordem já foram processados
            codigos_nao_processados = [codigo for codigo in codigos_ordem if codigo not in codigos_processados]
            if not codigos_nao_processados:
                logger.debug(f"Todos os códigos de ordem já processados para o arquivo: {arquivo_pro.name}")
                time.sleep(5)
                continue

            for codigo_ordem in codigos_nao_processados:
                logger.info(f"Enviando leitura para API: {codigo_ordem}")

                leitura = LeiturasPost(
                    id_recurso=parsed_args.id_recurso,
                    codigo=codigo_ordem,
                    qtd=1,
                    leitura_manual=False,
                )

                tx.leitura.nova_leitura(
                    id_recurso=leitura.id_recurso,
                    codigo=leitura.codigo,
                    qtd=leitura.qtd,
                    leitura_manual=leitura.leitura_manual,
                )

            # Escreve no arquivo processado com todos os códigos de ordem, incluindo os novos
            with caminho_processado.open("a", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)
                writer.writerow([str(arquivo_pro.resolve())] + codigos_ordem)

            logger.info(f"Arquivo processado com sucesso: {arquivo_pro.name}")

        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")

        logger.info("Aguardando próximo ciclo (5 segundos)...")
        time.sleep(5)