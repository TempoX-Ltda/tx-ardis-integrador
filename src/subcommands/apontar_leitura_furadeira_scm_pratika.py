import csv
import logging
import time
from argparse import Namespace
from pathlib import Path

from src.tx.modules.leituras.types import LeiturasPost
from src.tx.tx import Tx

logger = logging.getLogger("src.subcommands.apontar_leitura_furadeira_scm_pratika")


def obter_pasta_ano_mais_recente(diretorio: Path) -> Path:
    """Retorna a subpasta cujo nome é o ano (apenas dígitos) mais alto."""
    subpastas_ano = [p for p in diretorio.iterdir() if p.is_dir() and p.name.isdigit()]
    if not subpastas_ano:
        raise FileNotFoundError(f"Nenhuma subpasta de ano encontrada em {diretorio}")
    return max(subpastas_ano, key=lambda p: int(p.name))


def obter_ultimo_csv(diretorio: Path) -> Path:
    """
    Dentro da subpasta de ano mais recente de 'diretorio',
    retorna o .pro mais recente que NÃO contenha
    '_PROCESSADO_TEMPOX' nem '_COM_ERRO_TEMPOX' no nome.
    """
    pasta_ano = obter_pasta_ano_mais_recente(diretorio)
    arquivos = [
        p for p in pasta_ano.glob("*.pro")
        if "_PROCESSADO_TEMPOX" not in p.stem and "_COM_ERRO_TEMPOX" not in p.stem
    ]
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .pro válido em {pasta_ano}")
    return max(arquivos, key=lambda p: p.stat().st_mtime)


def obter_ultimo_csv_com_erro(diretorio: Path) -> Path:
    """
    Dentro da subpasta de ano mais recente de 'diretorio',
    retorna o .pro mais recente que contenha '_COM_ERRO_TEMPOX' no nome.
    """
    pasta_ano = obter_pasta_ano_mais_recente(diretorio)
    arquivos = [
        p for p in pasta_ano.glob("*.pro")
        if "_COM_ERRO_TEMPOX" in p.stem
    ]
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo .pro com erro em {pasta_ano}")
    return max(arquivos, key=lambda p: p.stat().st_mtime)


def carregar_linhas_processadas(arquivo_processado: Path):
    if not arquivo_processado.exists():
        return set()

    with arquivo_processado.open("r", newline="", encoding="latin1") as f:
        reader = csv.reader(f)
        return set(tuple(row) for row in reader)


def carregar_linhas_com_erro(arquivo_com_erro: Path):
    if not arquivo_com_erro.exists():
        return set()

    with arquivo_com_erro.open("r", newline="", encoding="latin1") as f:
        reader = csv.reader(f)
        return set(tuple(row) for row in reader)


def apontar_leitura_furadeira_scm_pratika_subcommand(parsed_args: Namespace):
    logger.info("Iniciando processo de apontamento de leituras no MES...")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=parsed_args.timeout,
    )

    diretorio = Path(parsed_args.caminho_arquivo)
    while True:
        try:
            csv_entrada = obter_ultimo_csv(diretorio)
            csv_com_erro = obter_ultimo_csv(diretorio)

            nome_processado = csv_entrada.stem + "_PROCESSADO_TEMPOX.pro"
            caminho_processado = csv_entrada.with_name(nome_processado)
            linhas_processadas = carregar_linhas_processadas(caminho_processado)

            nome_com_erro = csv_com_erro.stem + "_COM_ERRO_TEMPOX.pro"
            caminho_com_erro = csv_com_erro.with_name(nome_com_erro)
            linhas_com_erro = carregar_linhas_com_erro(caminho_com_erro)

            with csv_entrada.open("r", newline="", encoding="latin1") as f_in:
                reader = csv.reader(f_in)
                linhas = list(reader)[1:]  # Ignora cabeçalho

            for linha in linhas:
                if tuple(linha) in linhas_processadas:
                    continue

                if tuple(linha) in linhas_com_erro:
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

                    tx.leitura.nova_leitura(
                        id_recurso=leitura.id_recurso,
                        codigo=leitura.codigo,
                        qtd=leitura.qtd,
                        leitura_manual=leitura.leitura_manual,
                    )

                    with caminho_processado.open(
                        "a", newline="", encoding="utf-8"
                    ) as f_out:
                        writer_arquivo_processado = csv.writer(f_out)
                        writer_arquivo_processado.writerow(linha)
                        logger.info(f"Linha processada com sucesso: {linha}")

                except Exception as e:
                    logger.error(f"Erro ao processar linha {linha}: {e}")
                    with caminho_com_erro.open(
                        "a", newline="", encoding="utf-8"
                    ) as f_out:
                        writer_arquivo_com_erro = csv.writer(f_out)
                        writer_arquivo_com_erro.writerow(linha)

        except Exception as erro:
            logger.error(f"Erro no processamento: {erro}")

        logger.info("Aguardando próximo ciclo (30 segundos)...")
        time.sleep(30)
