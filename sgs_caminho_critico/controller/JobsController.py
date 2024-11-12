from fastapi import APIRouter

from sgs_caminho_critico.dto.request import JobStatusRequest
from sgs_caminho_critico.service.JobsService import JobsService

jobs_router = APIRouter()
jobs_service = JobsService()


@jobs_router.post("/update-status", response_model=dict,
                  response_description="Captura e atualiza o status dos jobs", status_code=200)
def capturar_e_atualizar_status_jobs(request: JobStatusRequest):
    return jobs_service.atualizar_status_jobs(request)
