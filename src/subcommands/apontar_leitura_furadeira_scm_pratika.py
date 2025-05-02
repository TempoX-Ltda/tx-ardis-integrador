import csv
import logging
import time
from argparse import Namespace
from pathlib import Path

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


def carregar_linhas_processadas_scm_pratika(arquivo_processado: Path) -> set:
    if not arquivo_processado.exists():
        return set()

    with arquivo_processado.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        return set(tuple(row) for row in reader)


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
        try:
            arquivo_pro = obter_ultimo_pro(diretorio)
            nome_processado = arquivo_pro.stem + "_PROCESSADO_SCM_PRATIKA.csv"
            caminho_processado = arquivo_pro.with_name(nome_processado)

            linhas_processadas = carregar_linhas_processadas_scm_pratika(caminho_processado)

            linha_atual = [str(arquivo_pro.resolve())]
            if tuple(linha_atual) in linhas_processadas:
                logger.debug("Arquivo já processado, ignorando.")
                time.sleep(5)
                continue

            try:
                codigo_ordem = arquivo_pro.stem
                if not codigo_ordem:
                    logger.warning(f"Código de ordem inválido: {arquivo_pro.name}")
                    continue

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

                with caminho_processado.open("a", newline="", encoding="utf-8") as f_out:
                    writer = csv.writer(f_out)
                    writer.writerow(linha_atual)

                logger.info(f"Arquivo processado com sucesso: {arquivo_pro.name}")

            except Exception as e:
                logger.error(f"Erro ao processar arquivo {arquivo_pro.name}: {e}")

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        logger.info("Aguardando próximo ciclo (5 segundos)...")
        time.sleep(5)
