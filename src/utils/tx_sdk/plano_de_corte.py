
class PlanoDeCorte:

    def __init__(self, tx_connection) -> None:
        
        from . import TxSDK

        self.tx_connection: TxSDK = tx_connection

    def gerar_id_de_projeto(self):

        res = self.tx_connection.post('plano-de-corte/projeto/gerar-id')

        res.raise_for_status()

        return res.json()['retorno']['id_projeto']
