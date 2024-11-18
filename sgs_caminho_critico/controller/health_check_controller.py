from fastapi import APIRouter

from sgs_caminho_critico.schemas.health_check import HealthCheck

health_check_router = APIRouter()


@health_check_router.get("/live", tags=["HealthCheck"])
async def health_live() -> HealthCheck:
    return HealthCheck(status="OK")


@health_check_router.get("/ready", tags=["HealthCheck"])
async def health_ready() -> HealthCheck:
    return HealthCheck(status="OK")
