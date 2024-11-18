from fastapi import FastAPI
from sgs_caminho_critico import __version__
from sgs_caminho_critico.controller.fluxo_controller import fluxo_router
from sgs_caminho_critico.controller.graph_controller import router
from sgs_caminho_critico.controller.run_controller import run_router
from sgs_caminho_critico.controller.report_controller import report_router
from sgs_caminho_critico.controller.jobs_controller import jobs_router
from sgs_caminho_critico.controller.health_check_controller import health_check_router

app = FastAPI(
    title="API do Caminho Crítico",
    description="API para construir mapa de rotinas batch",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    redirect_slashes=False,
)

app.include_router(router, prefix="/api", tags=["Graph"])
app.include_router(run_router, prefix="/api/run", tags=["Run"])
app.include_router(report_router, prefix="/api/report", tags=["Report"])

app.include_router(jobs_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(fluxo_router, prefix="/api/fluxo", tags=["Fluxo"])

app.include_router(health_check_router, prefix="/", tags=["HealthCheck"])
