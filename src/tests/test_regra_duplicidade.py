from datetime import datetime, timedelta
from src.utils.types import PartFromCsv

from utils import peca_no_plano_considera_duplicidade

from tx.modules.plano_de_corte.types import PlanoDeCorteModel

plano_base = PlanoDeCorteModel(
    finalizado=False,
    pendente=True,
    em_processo=False,
    inativo=False,
    sobra=False,
    codigo_layout="1234I12345L12-",
    codigo_lote="1234",
    created_on=datetime.now(),
    modified_on=datetime.now(),
    descricao="ASDQWERTYFGH",
    descricao_material="ZXCASDQWE",
    inicio_apontamento=None,
    fim_apontamento=None,
    id=1234,
    id_projeto=None,
    id_recurso=1,
    data_integrador=None,
    log_integrador="",
    sucesso_integrador=None,
    mm_comp_linear=10000,
    mm_comprimento=1000,
    mm_largura=500,
    nome_projeto="ASDQWE",
    perc_aproveitamento=90,
    perc_performance=85,
    perc_sobras=5,
    qtd_chapas=1,
    sequencia_corte=1,
    tempo_bruto=None,
    tempo_estimado="PT1H",
    tempo_parada=None,
    tempo_trabalhado=None,
)

part_base = PartFromCsv(
    codigo_layout="4321I54321L21-",
    id_ordem="1234",
    id_unico_peca=1234,
    qtd_cortada_no_layout=1,
    tempo_corte_segundos=0,
)


def test_regra_duplicidade():
    plano = plano_base
    peca = part_base

    # Ex.:

    testes = [
        #   Plano que já foi enviado está pendente
        #   Plano que já foi enviado está ativo
        #   Plano que já foi enviado fazia parte de um lote_normal
        #   Plano que está sendo enviado agora é um lote_normal
        # Result: Bloqueia - Porque o plano que já foi enviado ainda está pendente
        #                    para cortar, portanto não deve ser enviado nenhum novo
        #                    plano que contenha as mesmas peças
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        ("pendente", "ativo", "lote_normal", "lote_normal", True),
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ("pendente", "ativo", "lote_normal", "lote_retrab", False),
        ("pendente", "ativo", "lote_retrab", "lote_normal", False),
        ("pendente", "ativo", "lote_retrab", "lote_retrab", False),
        ("pendente", "inativo", "lote_normal", "lote_normal", False),
        ("pendente", "inativo", "lote_normal", "lote_retrab", False),
        ("pendente", "inativo", "lote_retrab", "lote_normal", False),
        ("pendente", "inativo", "lote_retrab", "lote_retrab", False),
        #   Plano que já foi enviado está finalizado
        #   Plano que já foi enviado está ativo
        #   Plano que já foi enviado fazia parte de um lote_normal
        #   Plano que está sendo enviado agora é um lote_normal
        # Result: Bloqueia - Porque o plano que já foi enviado já foi cortado e
        #                    as peças já estão produzidas, não se deve produzir
        #                    novamente as mesmas (somente como retrabalho)
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        ("finalizado", "ativo", "lote_normal", "lote_normal", True),
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ("finalizado", "ativo", "lote_normal", "lote_retrab", False),
        ("finalizado", "ativo", "lote_retrab", "lote_normal", False),
        ("finalizado", "ativo", "lote_retrab", "lote_retrab", False),
        #   Plano que já foi enviado está pendente
        #   Plano que já foi enviado está ativo
        #   Plano que já foi enviado fazia parte de um lote_normal
        #   Plano que está sendo enviado agora é um lote_normal
        # Result: Bloqueia - Porque o plano que já foi enviado já foi cortado e
        #                    as peças já estão produzidas, não se deve produzir
        #                    novamente as mesmas (somente como retrabalho). Por
        #                    algum motivo, o plano cortado foi inativado, mas
        #                    isso não muda o fato de que as peças já foram cortadas
        # vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        ("finalizado", "inativo", "lote_normal", "lote_normal", True),
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        ("finalizado", "inativo", "lote_normal", "lote_retrab", False),
        ("finalizado", "inativo", "lote_retrab", "lote_normal", False),
        ("finalizado", "inativo", "lote_retrab", "lote_retrab", False),
    ]

    for status_apont, status_plano, lote_existente, lote_novo, resultado in testes:
        # Status do Apontamento
        if status_apont == "pendente":
            # Plano Pendente
            plano.pendente = True
            plano.em_processo = False
            plano.finalizado = False
            plano.inicio_apontamento = None
            plano.fim_apontamento = None

        elif status_apont == "finalizado":
            # Plano Finalizado
            plano.pendente = False
            plano.em_processo = False
            plano.finalizado = True
            plano.inicio_apontamento = datetime.now() - timedelta(minutes=10)
            plano.fim_apontamento = datetime.now()

        # Status do Plano
        if status_plano == "ativo":
            # Plano Ativo
            plano.inativo = False
        elif status_plano == "inativo":
            # Plano Inativo
            plano.inativo = True

        # Tipo Lote Existente
        if lote_existente == "lote_normal":
            # Faz parte de um lote comum de produção
            plano.codigo_layout = "1234I12345L12-"
            plano.codigo_lote = "1234"
        elif lote_existente == "lote_retrab":
            # Faz parte de um lote comum de produção
            plano.codigo_layout = "RETRI12345L12-"
            plano.codigo_lote = "RETR"

        # Tipo do Lote que está sendo inserido
        if lote_novo == "lote_normal":
            peca.codigo_layout = "4321I54321L21-"
        elif lote_novo == "lote_retrab":
            peca.codigo_layout = "RETRI54321L21-"

        assert (
            peca_no_plano_considera_duplicidade(plano, peca) is resultado
        ), f"{status_apont}, {status_plano}, {lote_existente}, {lote_novo}"
