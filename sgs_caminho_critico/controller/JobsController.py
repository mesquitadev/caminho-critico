import json
import os
import traceback
import urllib3
from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime, timedelta

from pydantic import BaseModel

from sgs_caminho_critico.repository.CaminhoCriticoRepository import CaminhoCriticoRepository

# Desabilitar avisos de certificado SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

jobs_router = APIRouter()

# Variáveis globais para armazenar o token e a hora da autenticação
token = None
token_expiration = None


def authenticate():
    global token, token_expiration
    auth_url = "https://pcp-comandos-he.pcp.desenv.bb.com.br/login/token"
    auth_data = {
        "grant_type": "",
        "username": "Magic",
        "password": "magic",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(auth_url, headers=headers, data=auth_data, verify=False)
    if response.status_code == 200:
        token = response.json().get("access_token")
        token_expiration = datetime.now() + timedelta(minutes=30)
    else:
        raise HTTPException(status_code=response.status_code, detail="Erro ao autenticar na API do PCP")


def get_token():
    global token, token_expiration
    if token is None or datetime.now() >= token_expiration:
        authenticate()
    return token


status_mapping = {
    "Ended OK": 7,
    "Ended Not OK": 8,
    "Wait User": 12,
    "Wait resource": 13,
    "Wait host": 14,
    "Wait workload": 15,
    "Wait Condition": 2,
    "Executing": 4,
    "Status unknown": 16,
    "Desconhecido": 0
}


class JobStatusRequest(BaseModel):
    jobname: str
    keyBB: str
    limit: int
    orderDateFrom: str
    orderDateTo: str
    server: str


@jobs_router.post("/update-status", response_model=dict, response_description="Captura e atualiza o status dos jobs")
async def capturar_e_atualizar_status_jobs(request: JobStatusRequest):
    try:
        # Obter o token atualizado
        access_token = get_token()

        # Configurações da API Control-M Services
        api_url = "https://pcp-comandos-he.pcp.desenv.bb.com.br/run/run-jobs-status"
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

        # Conectar ao banco de dados
        db_config = {
            'dbname': 'pcp',
            'user': 'user_gprom63',
            'password': 'magic123',
            'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
            'port': '5432'
        }
        repo = CaminhoCriticoRepository(**db_config)
        repo.connect()

        # Buscar IDs dos jobs na tabela SCH_AGDD
        sch_agdd_data = repo.fetch_sch_agdd_data()
        # Salvar o resultado em um arquivo JSON para cache
        with open(os.getenv('CSV_FILES') + 'file.json', 'w') as json_file:
            json.dump(jobs_data, json_file, indent=4)

        # Preparar dados para inserção na tabela JOB_EXEA_CTM
        job_exea_ctm_data = []
        for job in jobs_data:
            print(f'id_job {json.dumps(job, indent=4)}')
            for sch_job in sch_agdd_data:
                if (
                        job['ctm'] == sch_job['nm_svdr'] and
                        job['folder'] == sch_job['pas_pai'] and
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
                        'dt_atl': datetime.now().isoformat()
                    })

        # Fetch existing records from the database
        existing_records = repo.fetch_existing_job_exea_ctm_data([job['idfr_sch'] for job in job_exea_ctm_data])

        # Prepare data for insertion, update, or deletion
        records_to_insert = []
        records_to_update = []

        for new_job in job_exea_ctm_data:
            match_found = False
            for existing_job in existing_records:
                if (new_job['idfr_sch'] == existing_job['idfr_sch'] and
                        new_job['idfr_exea'] == existing_job['idfr_exea']):
                    match_found = True
                    if (new_job['nr_exea'] != existing_job['nr_exea']
                            or new_job['idfr_est_job'] != existing_job['idfr_est_job']):
                        records_to_update.append(new_job)
                    break
            if not match_found:
                records_to_insert.append(new_job)

        # Delete records that need to be updated
        if records_to_update:
            repo.delete_job_exea_ctm_data([job['idfr_sch'] for job in records_to_update])

        # Insert new and updated records
        if records_to_insert or records_to_update:
            repo.insert_job_exea_ctm_data(records_to_insert + records_to_update)

        repo.disconnect()

        return {"status": "success", "message": "Dados dos jobs atualizados com sucesso",
                "updated_jobs": job_exea_ctm_data}

    except Exception as e:
        error_message = f"Erro: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_message)
