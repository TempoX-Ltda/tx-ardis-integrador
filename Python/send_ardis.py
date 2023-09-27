from requests import Session
from requests.exceptions import HTTPError
from argparse import ArgumentParser
import logging
from logging.handlers import RotatingFileHandler
from pandas import read_csv
from urllib.parse import urljoin
import PySimpleGUI as sg
import tempfile
import sys

sg.theme('Dark Blue 3')

log_file = tempfile.gettempdir() + '/send_ardis.log'

formatter = logging.Formatter('%(asctime)s,%(msecs)d | %(name)s | %(levelname)s | %(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_log_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
file_log_handler.setLevel(logging.DEBUG)
file_log_handler.setFormatter(formatter)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

logger.addHandler(file_log_handler)
logger.addHandler(stdout_handler)

parser = ArgumentParser(
    prog='send_ardis',
    description='Insere as informações das otimizações do Ardis no sistema GTRP.'
)

parser.add_argument(
    '--host',
    type=str,
    help='Endereço IP da API Ex.: http://localhost:6543/',
    required=True
)

parser.add_argument(
    '-u', '--user',
    type=str,
    help='Usuario que será utilizado para acessar a API',
    required=True
)

parser.add_argument(
    '-p', '--password',
    type=str,
    help='Senha do usuário',
    required=True
)

parser.add_argument(
    '--layouts-file',
    type=open,
    help='Arquivo csv contendo as informações de cada layout',
    required=True
)

parser.add_argument(
    '--parts-file',
    type=open,
    help='Arquivo csv contendo as informações de peça de cada layout',
    required=True
)

parser.add_argument(
    '--sep',
    type=str,
    help='Separador de campos dos arquivos csv',
    default=','
)

parser.add_argument(
    '--error-on-duplicated-part',
    action='store_true',
    help='Impede o programa de continuar se o id único de uma peça já está inserido em algum plano ativo',
)

args = parser.parse_args()

logger.debug('Argumentos: %s', args)

URL_PLANO_DE_CORTE       = urljoin(args.host, 'plano-de-corte')
URL_PLANO_DE_CORTE_PECAS = urljoin(args.host, 'plano-de-corte/{codigo_layout}/pecas')

logger.debug('URL_PLANO_DE_CORTE: %s',       URL_PLANO_DE_CORTE)
logger.debug('URL_PLANO_DE_CORTE_PECAS: %s', URL_PLANO_DE_CORTE_PECAS)

# Cria sessão da API e coleta o token que é utilizado nas futuras requisições
s = Session()

def get_auth_key():

    try:

        login = s.post(
            url = urljoin(args.host, 'auth/login'),
            json= {
                "user":     args.user,
                "password": args.password
            }
        )

        login.raise_for_status()

        logger.info('Sucesso no Login')

        return login.json().get('retorno').get('key')

    except Exception as exc:

        logger.exception('')

        try:
            mensagem = exc.response.json().get('mensagem')
        except Exception:
            mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

        sg.Popup(
            'Não foi possível se conectar a API',
            mensagem,
            f'Log completo em: {log_file}',
            title='Erro ao conectar a API',
            button_type=sg.POPUP_BUTTONS_OK
        )

        raise SystemExit from exc

def envia_layouts(layouts):
    # Envia os layouts
    for row_num, layout in enumerate(layouts.itertuples(index=True)):
        logger.debug('Enviando layout: %s',layout)

        if not sg.one_line_progress_meter(
                                    'Enviando Layouts',
                                    row_num, len(layouts.index),
                                    f'Codigo layout: {layout.codigo_layout}',
                                    orientation='h',
                                    no_titlebar=False,
                                    grab_anywhere=False):
            break
    
        plano_de_corte = {
            "codigo_layout":       layout.codigo_layout,
            "qtd_chapas":          layout.qtd_chapas,
            "perc_aproveitamento": layout.perc_aproveitamento,
            "perc_sobras":         layout.perc_sobras,
            "tempo_estimado_seg":  layout.tempo_estimado_seg,
            "descricao_material":  layout.descricao_material,
            "id_recurso":          layout.id_recurso,
            "mm_comprimento":      layout.mm_comprimento,
            "mm_largura":          layout.mm_largura,
            "mm_comp_linear":      layout.mm_comp_linear,
            "nome_projeto":        layout.nome_projeto,
            "sobra":               layout.sobra == 'S'
        }

        logger.info(f'Cadastrando plano_de_corte {layout.codigo_layout}')

        res = s.post(
            url=URL_PLANO_DE_CORTE,
            json=plano_de_corte
        )

        try:
            res.raise_for_status()
        except HTTPError as exc:

            logger.exception('')

            try:
                mensagem = exc.response.json().get('mensagem')
            except Exception:
                mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

            logger.error(mensagem)

            response = sg.Popup(
                            f'Codigo layout: {layout.codigo_layout}',
                            'Ocorreu um erro ao enviar esse layout:',
                            mensagem,
                            f'Log completo em: {log_file}',
                            title='Erro ao enviar Layouts',
                            button_type=sg.POPUP_BUTTONS_OK
                        )
            
            sg.one_line_progress_meter_cancel()
            raise SystemExit from exc
        else:
            logger.debug('ok')

    sg.one_line_progress_meter_cancel()

def envia_pecas(parts):
    # Envia as pecas
    for row_num, part in enumerate(parts.itertuples(index=True)):
        logger.debug('Enviando peça: %s', part)

        if not sg.one_line_progress_meter(
                                    'Enviando Peças',
                                    row_num, len(parts.index),
                                    f'Layout: {part.codigo_layout}\n'
                                    f'ID Ordem: {part.id_ordem}\n',
                                    f'ID Único: {part.id_unico_peca}\n',
                                    orientation='h'):
            break

        peca = {
            "qtd_cortada_no_layout": str(part.qtd_cortada_no_layout),
            "id_unico_peca":         str(part.id_unico_peca),
            "tempo_corte_segundos":  str(part.tempo_corte_segundos)
        }

        logger.info(f'Cadastrando Peca {part.id_unico_peca}')

        res = s.post(
            url=URL_PLANO_DE_CORTE_PECAS.format(codigo_layout = part.codigo_layout),
            json=peca
        )

        try:
            res.raise_for_status()
        except HTTPError as exc:

            logger.exception('')

            try:
                mensagem = exc.response.json().get('mensagem')
            except Exception:
                mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

            logger.error(mensagem)

            response = sg.Popup(
                            f'Layout: {part.codigo_layout} \n'
                            f'ID Ordem: {part.id_ordem} \n',
                            f'ID Único: {part.id_unico_peca} \n'
                            'Ocorreu um erro ao enviar essa peca:',
                            mensagem,
                            f'Log completo em: {log_file}',
                            'Deseja continuar o envio das outras peças?',
                            title='Erro ao enviar peças',
                            button_type=sg.POPUP_BUTTONS_YES_NO
                        )
            if response == 'No' or not response:
                sg.one_line_progress_meter_cancel()
                raise SystemExit from exc
        else:
            logger.debug('ok')

    sg.one_line_progress_meter_cancel()

def verifica_duplicidade_pecas(parts):
    """
        Verifica se já alguma peça já está inserida em algum plano de corte ativo
    """

    for row_num, part in enumerate(parts.itertuples(index=True)):
        logger.debug('Consultando peça: %s ...', part)

        if not sg.one_line_progress_meter(
                                    'Consultando Peças Duplicadas',
                                    row_num, len(parts.index),
                                    f'Layout: {part.codigo_layout}\n'
                                    f'ID Ordem: {part.id_ordem}\n',
                                    f'ID Único: {part.id_unico_peca}\n',
                                    orientation='h'):
            break

        res = s.get(
            url=urljoin(args.host, f'plano-de-corte/peca/{part.id_unico_peca}'),
        )

        try:
            res.raise_for_status()
        except HTTPError as exc:

            logger.exception('')

            try:
                mensagem = e.response.json().get('mensagem')
            except Exception:
                mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

            logger.error(mensagem)

            response = sg.Popup(
                            f'Layout: {part.codigo_layout} \n'
                            f'ID Ordem: {part.id_ordem} \n',
                            f'ID Único: {part.id_unico_peca} \n'
                            'Ocorreu um erro ao consultar essa peça:',
                            mensagem,
                            f'Log completo em: {log_file}',
                            'Deseja continuar a conferência das outras peças?',
                            title='Erro ao consultar peças',
                            button_type=sg.POPUP_BUTTONS_YES_NO
                        )
            if response == 'No' or not response:
                sg.one_line_progress_meter_cancel()
                raise SystemExit from exc
            
            continue
            
        planos = res.json().get('retorno')

        if not planos:
            continue

        for plano in planos:

            if str(plano.get("PlanoDeCorte").get("codigo_layout")).startswith(('RETR', 'ASS')):
                # O Plano que ja foi enviado NÃO é um plano de LOTE
                continue

            if plano.get('PlanoDeCorte').get('inativo') == True:
                # Plano NÃO está Ativo
                continue

            if (
                    plano.get('PlanoDeCorte').get('finalizado') == False # Plano NÃO foi cortado
                        or 
                    not str(part.codigo_layout).startswith(('RETR', 'ASS')) # O Plano atual é um plano de LOTE 
                ):
                    response = sg.Popup(
                            f'ID Ordem: {part.id_ordem}',
                            f'ID Único: {part.id_unico_peca} \n'
                            'Essa peça já está inserida no seguinte plano de corte:',
                            f'{plano.get("PlanoDeCorte").get("codigo_layout")} - {plano.get("PlanoDeCorte").get("nome_projeto")}\n',
                            "Finalizado: Sim\n" if plano.get("PlanoDeCorte").get("finalizado") == True else "Finalizado: Não\n",
                            'Processo será interrompido!',
                            title='Peça já foi inserida',
                            button_type=sg.POPUP_BUTTONS_OK
                        )
                    
                    sg.one_line_progress_meter_cancel()
                    raise SystemExit

    sg.one_line_progress_meter_cancel()

def main():

    s.headers['Authorization'] = f"Bearer {get_auth_key()}"

    # Carrega os arquivos
    layouts = read_csv(args.layouts_file, sep=args.sep)
    parts   = read_csv(args.parts_file,   sep=args.sep)

    if args.error_on_duplicated_part:
        verifica_duplicidade_pecas(parts)

    envia_layouts(layouts)

    envia_pecas(parts)

    sg.Popup(
        'Envio finalizado!',
        f'Log completo em: {log_file}',
        'Essa mensagem irá fechar automaticamente em 5 segundos.',
        title='Envio finalizado',
        button_type=sg.POPUP_BUTTONS_OK,
        auto_close=True,
        auto_close_duration=5,
    )

if __name__ == '__main__':
    
    try:
        main()
    except Exception as exc:
    
        logger.exception('')

        sg.Popup(
            'Ocorreu um erro não esperado',
            str(exc),
            f'Log completo em: {log_file}',
            title='Erro não esperado',
            button_type=sg.POPUP_BUTTONS_OK
        )

        raise SystemExit from exc