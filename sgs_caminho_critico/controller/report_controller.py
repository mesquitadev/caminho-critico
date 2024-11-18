from fastapi import APIRouter
from sgs_caminho_critico.service.report_service import ReportService

report_router = APIRouter()
report_service = ReportService()


@report_router.get("/generate")
def pegar_relatorios_do_inventario_e_salvar_no_csv():
    return report_service.pegar_relatorios_do_inventario_e_salvar_no_csv()
