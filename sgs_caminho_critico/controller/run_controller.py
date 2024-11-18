from fastapi import APIRouter
from sgs_caminho_critico import __version__
run_router = APIRouter()


@run_router.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


@run_router.get("/version", status_code=200)
def get_version():
    return {"version": __version__}
