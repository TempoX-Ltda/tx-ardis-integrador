from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class Metadata(BaseModel):
    page: int
    page_size: int
    last_page: Optional[int]


class SuccessResponse(BaseModel, Generic[DataT]):
    sucesso: bool
    mensagem: str
    metadata: Optional[Metadata]
    retorno: DataT
