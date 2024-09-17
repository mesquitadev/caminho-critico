from fastapi import FastAPI

from sgs_caminho_critico.controller.CaminhoCriticoController import caminhos_router

app = FastAPI()

app.include_router(caminhos_router, prefix="/api/caminhos", tags=["Graph"])
