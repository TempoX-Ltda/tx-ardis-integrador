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

args = parser.parse_args()

logger.debug('Argumentos: %s', args)

URL_PLANO_DE_CORTE       = urljoin(args.host, 'plano-de-corte')
URL_PLANO_DE_CORTE_PECAS = urljoin(args.host, 'plano-de-corte/pecas')

logger.debug('URL_PLANO_DE_CORTE: %s',       URL_PLANO_DE_CORTE)
logger.debug('URL_PLANO_DE_CORTE_PECAS: %s', URL_PLANO_DE_CORTE_PECAS)

# Cria sessão da API e coleta o token que é utilizado nas futuras requisições
s = Session()

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

except Exception as e:

    logger.exception('')

    try:
        mensagem = e.response.json().get('mensagem')
    except:
        mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

    sg.Popup(
        'Não foi possível se conectar a API',
        mensagem,
        f'Log completo em: {log_file}',
        title='Erro ao conectar a API',
        button_type=sg.POPUP_BUTTONS_OK
    )

    raise SystemExit

s.headers['Authorization'] = f"Bearer {login.json().get('retorno').get('key')}"

# Carrega os arquivos
layouts = read_csv(args.layouts_file, sep=args.sep)
parts   = read_csv(args.parts_file,   sep=args.sep)


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
    except HTTPError as e:

        logger.exception('')

        try:
            mensagem = e.response.json().get('mensagem')
        except:
            mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

        logger.error(mensagem)

        response = sg.Popup(
                        f'Codigo layout: {layout.codigo_layout}',
                        'Ocorreu um erro ao enviar esse layout:',
                        mensagem,
                        f'Log completo em: {log_file}',
                        'Deseja continuar o envio dos outros layouts?',
                        title='Erro ao enviar Layouts',
                        button_type=sg.POPUP_BUTTONS_YES_NO
                    )
        if response == 'No' or not response:
            sg.one_line_progress_meter_cancel()
            raise SystemExit
    else:
        logger.debug(f'ok')

sg.one_line_progress_meter_cancel()

# Envia as pecas
for row_num, part in enumerate(parts.itertuples(index=True)):
    logger.debug('Enviando peça: %s', part)

    if not sg.one_line_progress_meter(
                                'Enviando Peças',
                                row_num, len(parts.index),
                                f'Layout: {part.codigo_layout}'
                                f'ID Ordem: {part.id_ordem}',
                                f'ID Único: {part.id_unico_peca}',
                                orientation='h'):
        break

    peca = {
        "codigo_layout":         part.codigo_layout,
        "qtd_cortada_no_layout": part.qtd_cortada_no_layout,
        "id_unico_peca":         part.id_unico_peca,
        "tempo_corte_segundos":  part.tempo_corte_segundos
    }

    logger.info(f'Cadastrando Peca {part.id_unico_peca}')

    res = s.post(
        url=URL_PLANO_DE_CORTE_PECAS,
        json=peca
    )

    try:
        res.raise_for_status()
    except HTTPError as e:

        logger.exception('')

        try:
            mensagem = e.response.json().get('mensagem')
        except:
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
            raise SystemExit
    else:
        logger.debug(f'ok')

sg.one_line_progress_meter_cancel()


sg.Popup(
    'Envio finalizado!',
    f'Log completo em: {log_file}',
    title='Envio finalizado',
    button_type=sg.POPUP_BUTTONS_OK
)