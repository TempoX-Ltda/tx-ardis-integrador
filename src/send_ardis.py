from argparse import ArgumentParser
import pathlib
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urljoin
import tempfile
import sys
import os
import base64

from requests import Session
from requests.exceptions import HTTPError
from pandas import read_csv
import PySimpleGUI as sg

__version__ = '1.0.2'

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
    '-v', '--version',
    action='version',
    version='%(prog)s ' + __version__
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

parser.add_argument(
    '--figures-directory',
    type=pathlib.Path,
    help='Diretório onde as figures de cada plano serão buscadas. O nome de cada arquivo deve ser igual ao código do plano, com extensão .png',
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
    
    def envia_layout(layout):

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
        
        if hasattr(layout, 'codigo_lote'):
            plano_de_corte["codigo_lote"] = str(layout.codigo_lote)

        logger.info('Cadastrando plano_de_corte %s', layout.codigo_layout)

        res = s.post(
            url=URL_PLANO_DE_CORTE,
            json=plano_de_corte
        )

        try:
            res.raise_for_status()
        except HTTPError as err:

            logger.exception('')

            try:
                mensagem = err.response.json().get('mensagem')
            except Exception:
                mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

            logger.error(mensagem)

            sg.Popup(
                f'Codigo layout: {layout.codigo_layout}',
                'Ocorreu um erro ao enviar esse layout:',
                mensagem,
                f'Log completo em: {log_file}',
                title='Erro ao enviar Layouts',
                button_type=sg.POPUP_BUTTONS_OK
            )
            
            sg.one_line_progress_meter_cancel()
            raise SystemExit from err

    def envia_layout_figure(layout):

        logger.info('Enviando figure do plano_de_corte %s', layout.codigo_layout)

        figure_path = os.path.join(
            str(args.figures_directory).strip('"').strip("'"), # Remove ' and/or " from figures_directory
            f'{layout.codigo_layout}.png'
        )

        if not os.path.exists(figure_path):
            logger.warning('O arquivo "%s" não foi encontrado', figure_path)
            return
        
        with open(figure_path, 'rb') as figure_img:

            encoded_str = base64.b64encode(figure_img.read())

            res = s.post(
                url=urljoin(args.host, f'plano-de-corte/{layout.codigo_layout}/figure'),
                json={
                    'decoded_figure': encoded_str.decode('utf-8')
                }
            )

            try:
                res.raise_for_status()
            except HTTPError as err:

                logger.exception('')

                try:
                    mensagem = err.response.json().get('mensagem')
                except Exception:
                    mensagem = 'A API não enviou uma mensagem de erro, verifique os logs.'

                logger.error(mensagem)

                sg.Popup(
                    f'Codigo layout: {layout.codigo_layout}',
                    'Ocorreu um erro ao enviar a figure desse layout:',
                    mensagem,
                    f'Log completo em: {log_file}',
                    title='Erro ao enviar Layouts',
                    button_type=sg.POPUP_BUTTONS_OK
                )
            else:
                logger.info('ok')

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
    
        envia_layout(layout)

        if args.figures_directory:
            envia_layout_figure(layout)

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
            "qtd_cortada_no_layout": int(part.qtd_cortada_no_layout),
            "id_unico_peca":         int(part.id_unico_peca),
            "tempo_corte_segundos":  float(part.tempo_corte_segundos)
        }

        logger.info('Cadastrando Peca %s', int(part.id_unico_peca))

        res = s.post(
            url=URL_PLANO_DE_CORTE_PECAS.format(codigo_layout = part.codigo_layout),
            json=peca
        )

        try:
            res.raise_for_status()
        except HTTPError as err:

            logger.exception('')

            try:
                mensagem = err.response.json().get('mensagem')
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
                raise SystemExit from err
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

        # Verifica se o id_unico_peca é um número inteiro
        try:
            int(part.id_unico_peca)
        except ValueError as exc:
            logger.exception('')
            response = sg.Popup(
                    f'Layout: {part.codigo_layout}',
                    f'ID Ordem: {part.id_ordem}',
                    f'ID Único: {part.id_unico_peca}',
                    'O campo "id_unico_peca" não pode ser interpretado como INTEGER.',
                    f'id_unico_peca: {part.id_unico_peca}',
                    f'Log completo em: {log_file}',
                    title='Erro',
                    button_type=sg.POPUP_BUTTONS_OK
                )
            sg.one_line_progress_meter_cancel()
            raise SystemExit from exc

        # Verifica se o qtd_cortada_no_layout é um número inteiro
        try:
            int(part.qtd_cortada_no_layout)
        except ValueError as exc:
            logger.exception('')
            response = sg.Popup(
                    f'Layout: {part.codigo_layout}',
                    f'ID Ordem: {part.id_ordem}',
                    f'ID Único: {part.id_unico_peca}',
                    'O campo "qtd_cortada_no_layout" não pode ser interpretado como INTEGER.',
                    f'qtd_cortada_no_layout: {part.qtd_cortada_no_layout}',
                    f'Log completo em: {log_file}',
                    title='Erro',
                    button_type=sg.POPUP_BUTTONS_OK
                )
            sg.one_line_progress_meter_cancel()
            raise SystemExit from exc

        # Verifica se o tempo_corte_segundos é um número float
        try:
            float(part.tempo_corte_segundos)
        except ValueError as exc:
            logger.exception('')
            response = sg.Popup(
                    f'Layout: {part.codigo_layout}',
                    f'ID Ordem: {part.id_ordem}',
                    f'ID Único: {part.id_unico_peca}',
                    'O campo "tempo_corte_segundos" não pode ser interpretado como FLOAT.',
                    f'tempo_corte_segundos: {part.tempo_corte_segundos}',
                    f'Log completo em: {log_file}',
                    title='Erro',
                    button_type=sg.POPUP_BUTTONS_OK
                )
            sg.one_line_progress_meter_cancel()
            raise SystemExit from exc

        res = s.get(
            url=urljoin(args.host, f'plano-de-corte/peca/{int(part.id_unico_peca)}'),
        )

        try:
            res.raise_for_status()
        except HTTPError as err:

            logger.exception('')

            try:
                mensagem = err.response.json().get('mensagem')
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
                raise SystemExit from err
            
            continue
            
        planos = res.json().get('retorno')

        if not planos:
            continue

        for plano in planos:

            if str(plano.get("PlanoDeCorte").get("codigo_layout")).startswith(('RETR', 'ASS')):
                # O Plano que ja foi enviado NÃO é um plano de LOTE
                continue

            if plano.get('PlanoDeCorte').get('inativo') is True:
                # Plano NÃO está Ativo
                continue

            if (
                    plano.get('PlanoDeCorte').get('finalizado') is False # Plano NÃO foi cortado
                        or 
                    not str(part.codigo_layout).startswith(('RETR', 'ASS')) # O Plano atual é um plano de LOTE 
                ):
                    response = sg.Popup(
                            f'ID Ordem: {part.id_ordem}',
                            f'ID Único: {part.id_unico_peca} \n'
                            'Essa peça já está inserida no seguinte plano de corte:',
                            f'{plano.get("PlanoDeCorte").get("codigo_layout")} - {plano.get("PlanoDeCorte").get("nome_projeto")}\n',
                            "Finalizado: Sim\n" if plano.get("PlanoDeCorte").get("finalizado") is True else "Finalizado: Não\n",
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
