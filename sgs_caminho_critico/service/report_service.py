import os
from fastapi import HTTPException
from sgs_caminho_critico.repository.jobs_repository import JobsRepository


class ReportService:
    @staticmethod
    def pegar_relatorios_do_inventario_e_salvar_no_csv() -> dict:
        csv_files_path = os.getenv('CSV_FILES')
        if not csv_files_path:
            raise HTTPException(status_code=500, detail="Variavel de ambiente 'CSV_FILES' não encontrada.")
        csv_file_path = os.path.join(csv_files_path, 'edges_novo_cp.csv')

        repo = JobsRepository()
        repo.fetch_and_save_records_to_csv(csv_file_path)
        return {"message": "Registros salvos no csv com sucesso!"}
