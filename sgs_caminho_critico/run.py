from fastapi import FastAPI

from sgs_caminho_critico.controller.CaminhoCriticoController import router

app = FastAPI(
    redirect_slashes=False,
)

app.include_router(router, prefix="/api", tags=["Graph"])
