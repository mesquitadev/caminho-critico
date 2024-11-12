from fastapi import APIRouter

from sgs_caminho_critico.service.FluxoService import FluxoService

fluxo_router = APIRouter()
fluxo_service = FluxoService()


@fluxo_router.get("/update-status", response_model=dict, response_description="Processa dados do CSV e retorna em JSON")
def processar_fluxos():
    return fluxo_service.atualizar_status_fluxo()


@fluxo_router.get("/get-status", response_model=dict, response_description="Processa dados do CSV e retorna em JSON")
def retornar_status_fluxo():
    return fluxo_service.get_status_fluxos()


@fluxo_router.get("/get-status/{id_fluxo}", response_model=dict,
                  response_description="Busca status de um fluxo específico")
def retornar_status_fluxo_por_id(id_fluxo: str):
    return fluxo_service.get_status_fluxo_by_id(id_fluxo)
