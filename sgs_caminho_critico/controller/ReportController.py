import os
from fastapi import APIRouter, HTTPException
from sgs_caminho_critico.repository.CaminhoCriticoRepository import CaminhoCriticoRepository

report_router = APIRouter()


@report_router.get("/generate")
def pegar_relatorios_do_inventario_e_salvar_no_csv():
    db_config = {
        'dbname': 'pcp',
        'user': 'user_gprom63',
        'password': 'magic123',
        'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
        'port': '5432'
    }
    csv_files_path = os.getenv('CSV_FILES')
    if not csv_files_path:
        raise HTTPException(status_code=500, detail="Variavel de ambiente 'CSV_FILES' não encontrada.")
    csv_file_path = os.path.join(csv_files_path, 'edges_novo_cp.csv')

    repo = CaminhoCriticoRepository(**db_config)
    repo.connect()
    repo.fetch_and_save_records_to_csv(csv_file_path)
    repo.disconnect()
    return {"message": "Registros salvos no csv com sucesso!"}
