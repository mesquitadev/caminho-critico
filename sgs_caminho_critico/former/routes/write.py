#!/usr/bin/env python3
# coding: utf-8
"""Armazena um conteudo no mainframe."""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from starlette.responses import JSONResponse
from former.agz_error_handlers import response_codes
from former.auth import multi_auth
from former.log import LogTransaction
from pzowe import Pzowe

router = APIRouter(
    prefix="/write",
    tags=["write"],
    dependencies=[Depends(multi_auth)],
    route_class=LogTransaction
)


class BaseModelStoreContent(BaseModel):
    plex: str
    dataset: str
    member: str = None
    content: str
    caps: bool = True
    user: str
    password: str


class BaseModelResponseData(BaseModel):
    status: str


@router.put(path="", response_model=BaseModelStoreContent,
            responses=response_codes)
def write_content(req: Request, data: BaseModelStoreContent):
    req.app.logger.info(f"Gravando conteudo em {data.dataset} {data.member}")
    zowe_auth = f'{data.user}:{data.password}'
    pzowe = Pzowe(environment=data.plex, auth=zowe_auth)

    result = pzowe.write_content(data.dataset, data.member,
                                 data.content, data.caps)
    detail = ""
    member_suffix = data.member if data.member is not None else ''
    if result.status_code == 204:
        result.status_code = 200
        detail = f"{data.dataset} {member_suffix} foi sobrescrito"

    if result.status_code == 201:
        detail = f"{data.dataset} {member_suffix} foi criado"

    return JSONResponse(status_code=result.status_code, content={"status": "success", "detail": detail})
