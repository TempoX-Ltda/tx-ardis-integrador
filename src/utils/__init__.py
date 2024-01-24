from tx.modules.plano_de_corte.types import PlanoDeCorte
from utils.types import Part


def peca_no_plano_considera_duplicidade(plano: PlanoDeCorte, peca: Part):
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
