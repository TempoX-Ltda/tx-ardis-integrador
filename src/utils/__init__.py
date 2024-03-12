from tx.modules.plano_de_corte.pecas import PlanoDeCortePecas
from utils.types import PartFromCsv


def peca_no_plano_considera_duplicidade(plano: PlanoDeCortePecas, peca: PartFromCsv):
    if peca.codigo_layout.startswith(("RETR", "ASS")):
        # O novo plano que está sendo enviado é de Retrabalho ou assistência
        return False

    if plano.codigo_layout.startswith(("RETR", "ASS")):
        # O Plano que ja foi enviado é um plano de Assistência ou retrabalho
        return False

    if plano.pendente and plano.inativo:
        # O Plano que ja foi enviado não foi cortado e foi inativado
        return False

    return True
