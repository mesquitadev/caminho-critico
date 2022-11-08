#!/usr/bin/env python3
# coding: utf-8
"""Retorna conteúdo de um dataset do mainframe."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from former.agz_error_handlers import AgilizaFormatError, response_codes
from former.auth import multi_auth
from former.log import LogTransaction
from pzowe import Pzowe

router = APIRouter(
    prefix="/content",
    tags=["content"],
    dependencies=[Depends(multi_auth)],
    route_class=LogTransaction
)


class BaseModelDatasetContent(BaseModel):
    plex: str
    dataset: str
    member: str = None
    mask: str = None
    user: str
    password: str


class BaseModelResponseData(BaseModel):
    content: str
    status: str
    status_code: int


@router.post(path="", response_model=BaseModelResponseData,
             responses=response_codes)
def get_contents(req: Request, data: BaseModelDatasetContent):
    req.app.logger.info(f"Buscando conteudo de {data.dataset}")
    if data.mask is not None and data.member is not None:
        raise AgilizaFormatError(info='Informe apenas um dos parametros: mask ou member')
    zowe_auth = f'{data.user}:{data.password}'
    pzowe = Pzowe(environment=data.plex, auth=zowe_auth)
    if data.member is not None:
        path = f'{data.dataset}({data.member})'
        result = pzowe.get_dataset_member_content(member_path=path)
    elif data.mask is not None:
        result = pzowe.get_dataset_members_list(
            dataset_name=data.dataset,
            mask=data.mask,
            attribute='member', members_limit=50,
            demigration_awaiting='nowait')
    else:
        result = pzowe.get_dataset_content(dataset_name=data.dataset)

    return JSONResponse(status_code=200, content=result)
