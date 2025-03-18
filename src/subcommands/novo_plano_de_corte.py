import base64
import logging
import os
from argparse import Namespace
from math import isnan
from typing import Any, List, Optional

from httpx import Timeout
from pandas import read_csv
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    ValidationError,
    model_validator,
)
from typing_extensions import Annotated

from src.tx.modules.plano_de_corte.types import (
    PlanoDeCorteCreateModel,
    PlanoDeCortePecasCreateModel,
    TipoMateriaPrima,
)
from src.tx.tx import Tx

logger = logging.getLogger(__name__)


def coerce_nan_to_none(x: Any) -> Any:
    try:
        if isnan(x):
            return None
    except TypeError as exc:
        raise ValueError(f"Erro ao converter {x} para None") from exc

    return x


class PlanoDeCortePecasCsvModel(BaseModel):
    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.coerce_numbers_to_str
    model_config = ConfigDict(coerce_numbers_to_str=True)

    id_ordem: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]
    id_unico_peca: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]
    codigo_layout: str
    qtd_cortada_no_layout: int
    tempo_corte_segundos: float
    id_retrabalho: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]
    qtd_separacao_manual: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]
    qtd_separacao_automatica: Annotated[Optional[int], BeforeValidator(coerce_nan_to_none)]

    # Se `recorte` for true, a peça será considerada como recorte
    # nesse caso `id_ordem` e `id_unico_peca` podem ser None
    recorte: bool

    @model_validator(mode="after")
    def verifica_recorte(self):
        if self.recorte:
            if self.id_ordem is not None or self.id_unico_peca is not None:
                raise ValueError(
                    "Peça de recorte não deve ter id_ordem ou id_unico_peca"
                )

        return self


class PlanoDeCorteCsvModel(BaseModel):
    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.coerce_numbers_to_str
    model_config = ConfigDict(coerce_numbers_to_str=True)

    codigo_layout: str
    descricao_material: str
    id_recurso: int
    mm_comp_linear: float
    mm_comprimento: float
    mm_largura: float
    nome_projeto: str
    perc_aproveitamento: float
    perc_sobras: float
    tipo: TipoMateriaPrima
    codigo_lote: str
    qtd_chapas: int
    tempo_estimado_seg: float
    qtd_separacao_manual: int
    qtd_separacao_automatica: int


def get_figure_for_layout(parsed_args: Namespace, plano: PlanoDeCorteCsvModel):
    figure_path = os.path.join(
        str(parsed_args.figures_directory)
        .strip('"')
        .strip("'"),  # Remove ' and/or " from figures_directory
        f"{plano.codigo_layout}.png",
    )

    if not os.path.exists(figure_path):
        logger.warning('O arquivo "%s" não foi encontrado', figure_path)

        return None

    with open(figure_path, "rb") as figure_img:
        return base64.b64encode(figure_img.read()).decode("utf-8")


def parse_files(parsed_args: Namespace):
    logger.info("Lendo arquivos csv...")

    layouts_df = read_csv(parsed_args.layouts_file, sep=parsed_args.sep)
    parts_df = read_csv(parsed_args.parts_file, sep=parsed_args.sep)

    logger.debug("Layouts: %s", layouts_df)
    logger.debug("Parts: %s", parts_df)

    pecas: List[PlanoDeCortePecasCsvModel] = []
    planos: List[PlanoDeCorteCreateModel] = []

    for idx, row in parts_df.iterrows():
        try:
            peca = PlanoDeCortePecasCsvModel.model_validate(row.to_dict())
            pecas.append(peca)

        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar peça na linha {idx}: {row.to_dict()}"
            ) from exc

    logger.info("Arquivo %s lido com sucesso", parsed_args.parts_file.name)

    for idx, row in layouts_df.iterrows():
        try:
            row = PlanoDeCorteCsvModel.model_validate(row.to_dict())

        except ValidationError as exc:
            raise Exception(
                f"Erro ao validar layout na linha {idx}: {row.to_dict()}"
            ) from exc

        # Pode incluir recorte, que não devem ser tratados como peças
        todas_as_pecas_desse_plano = [
            peca for peca in pecas if peca.codigo_layout == row.codigo_layout
        ]

        # Conta quantas peças são recortes
        qtd_recortes = len(
            [peca for peca in todas_as_pecas_desse_plano if peca.recorte]
        )

        # Mantem somente as peças que não são recortes
        pecas_desse_plano = [
            peca for peca in todas_as_pecas_desse_plano if not peca.recorte
        ]

        figure = get_figure_for_layout(parsed_args, row)

        plano = PlanoDeCorteCreateModel(
            codigo_layout=row.codigo_layout,
            codigo_lote=row.codigo_lote,
            descricao_material=row.descricao_material,
            id_recurso=row.id_recurso,
            mm_comp_linear=row.mm_comp_linear,
            mm_comprimento=row.mm_comprimento,
            mm_largura=row.mm_largura,
            nome_projeto=row.nome_projeto,
            perc_aproveitamento=row.perc_aproveitamento,
            perc_sobras=row.perc_sobras,
            qtd_chapas=row.qtd_chapas,
            qtd_separacao_manual=row.qtd_separacao_manual,
            qtd_separacao_automatica=row.qtd_separacao_automatica,
            tempo_estimado_seg=row.tempo_estimado_seg,
            tipo=row.tipo,
            qtd_recortes=qtd_recortes,
            figure=figure,
            pecas=[
                PlanoDeCortePecasCreateModel(
                    qtd_cortada_no_layout=peca.qtd_cortada_no_layout,
                    id_unico_peca=peca.id_unico_peca,
                    id_ordem=peca.id_ordem,
                    tempo_corte_segundos=peca.tempo_corte_segundos,
                    id_retrabalho=peca.id_retrabalho,
                )
                for peca in pecas_desse_plano
            ],
        )

        planos.append(plano)

    logger.info("Arquivo %s lido com sucesso", parsed_args.layouts_file.name)

    return planos


def novo_plano_de_corte_subcommand(parsed_args: Namespace):
    logger.info("Iniciando envio de arquivos para o MES")

    tx = Tx(
        base_url=parsed_args.host,
        user=parsed_args.user,
        password=parsed_args.password,
        default_timeout=Timeout(parsed_args.timeout),
    )

    # Carrega os arquivos
    planos = parse_files(parsed_args)

    tx.plano_de_corte.novo_projeto(planos)

    logger.info("Envio finalizado!")
