import json
import os
import traceback
from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime

from pydantic import BaseModel

from sgs_caminho_critico.repository.JobsRepository import JobsRepository
from sgs_caminho_critico.utils import status_mapping, get_pcp_token

jobs_router = APIRouter()


class JobStatusRequest(BaseModel):
    jobname: str
    keyBB: str
    limit: int
    orderDateFrom: str
    orderDateTo: str
    server: str


def load_jobs_data():
    json_file_path = os.path.join(os.getcwd(), 'res2.json')
    print(f'json_file_path {json_file_path}')
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data.get('statuses', [])


@jobs_router.post("/update-status", response_model=dict, response_description="Captura e atualiza o status dos jobs")
async def capturar_e_atualizar_status_jobs(request: JobStatusRequest):
    try:
        # Obter o token atualizado
        access_token = get_pcp_token()
        print(f"token {access_token}")
        # Configurações da API Control-M Services
        api_url = f"{os.getenv('CONTROL_M_SERVICES_API_URL')}/run/run-jobs-status"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json"
        }

        # Fazer a requisição para a API Control-M Services
        response = requests.post(api_url, headers=headers, json=request.dict(), verify=False)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Erro ao acessar a API Control-M Services")

        jobs_data = response.json().get("data", {}).get("statuses", [])
        # Carregar dados dos jobs do arquivo JSON
        # jobs_data = load_jobs_data()

        repo = JobsRepository()

        # Buscar IDs dos jobs na tabela SCH_AGDD
        sch_agdd_data = repo.fetch_sch_agdd_data()
        # Salvar o resultado em um arquivo JSON para cache
        with open(os.getenv('CSV_FILES') + 'file.json', 'w') as json_file:
            json.dump(jobs_data, json_file, indent=4)

        # Preparar dados para inserção na tabela JOB_EXEA_CTM
        job_exea_ctm_data = []
        for job in jobs_data:
            for sch_job in sch_agdd_data:
                if (
                        (job['folder'] in ['UNKNWN', 'DUMMY'] or job['folder'] == sch_job['pas_pai']) and
                        job['ctm'] == sch_job['nm_svdr'] and
                        job['name'] == sch_job['nm_mbr'] and
                        job['subApplication'] == sch_job['sub_apl']):
                    job_exea_ctm_data.append({
                        'idfr_sch': sch_job['idfr_sch'],
                        'idfr_exea': job['jobId'][-5:],
                        'dt_mvt': datetime.strptime(job['orderDate'], '%y%m%d').strftime('%Y-%m-%d'),
                        'obs_job': '',
                        'nr_exea': job['numberOfRuns'],
                        'flx_atu': True,
                        'est_jobh': job['held'],
                        'est_excd': job['deleted'],
                        'idfr_est_job': status_mapping.get(job['status'], 0),
                        'dt_atl': datetime.now().isoformat(),
                        'hr_inc_exea_job': job.get('startTime', ''),
                        'hr_fim_exea_job': job.get('endTime', '')
                    })
        print(f'job_exea_ctm_data {job_exea_ctm_data}')

        # Fetch existing records from the database
        existing_records = repo.fetch_existing_job_exea_ctm_data([job['idfr_sch'] for job in job_exea_ctm_data])
        # Convert existing records to dictionaries
        existing_records_dicts = [dict(record._mapping) for record in existing_records]

        # Prepare data for deletion and insertion
        records_to_delete = []
        records_to_insert = []

        for new_job in job_exea_ctm_data:
            match_found = False
            for existing_job in existing_records_dicts:
                if (new_job['idfr_sch'] == existing_job['idfr_sch'] and
                        new_job['idfr_exea'] == existing_job['idfr_exea']):
                    match_found = True
                    records_to_delete.append(existing_job)
                    records_to_insert.append(new_job)
                    break
            if not match_found:
                records_to_insert.append(new_job)

        # Delete existing records
        if records_to_delete:
            repo.delete_job_exea_ctm_data([job['idfr_sch'] for job in records_to_delete])

        # Insert new records
        if records_to_insert:
            repo.insert_job_exea_ctm_data(records_to_insert)

        return {"status": "success", "message": "Dados dos jobs atualizados com sucesso",
                "updated_jobs": job_exea_ctm_data}

    except Exception as e:
        error_message = f"Erro: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_message)
