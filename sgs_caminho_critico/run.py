from fastapi import FastAPI
from sgs_caminho_critico import __version__
from sgs_caminho_critico.controller.GraphController import router
from sgs_caminho_critico.controller.RunController import run_router
from sgs_caminho_critico.controller.ReportController import report_router

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
