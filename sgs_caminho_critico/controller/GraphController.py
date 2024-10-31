from fastapi import APIRouter
from sgs_caminho_critico.service.GraphService import GraphService

router = APIRouter()
graph_service = GraphService()


@router.get("/graph/data", response_model=dict, response_description="Processa dados do CSV e retorna em JSON")
def processar_dados_retornar_json(rotina_inicial: str, rotina_destino: str):
    return graph_service.processar_dados(rotina_inicial, rotina_destino)


@router.get("/graph/data/next", response_model=dict, response_description="Processa dados do CSV e retorna em JSON")
def processar_fluxos():
    return graph_service.processar_fluxos()
