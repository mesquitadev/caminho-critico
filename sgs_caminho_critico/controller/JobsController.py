import urllib3
from fastapi import APIRouter, HTTPException
import requests
from datetime import datetime, timedelta
from sgs_caminho_critico.repository import CaminhoCriticoRepository

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
    response = requests.post(auth_url, headers=headers, data=auth_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        token_expiration = datetime.now() + timedelta(minutes=30)
    else:
        raise HTTPException(status_code=response.status_code, detail="Erro ao autenticar na API Control-M Services")


def get_token():
    global token, token_expiration
    if token is None or datetime.now() >= token_expiration:
        authenticate()
    return token


@jobs_router.get("/get-status", response_model=dict, response_description="Captura e atualiza o status dos jobs")
def capturar_e_atualizar_status_jobs():
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
        data = {
            "jobname": "A*",
            "keyBB": "c1333806",
            "limit": 10,
            "orderDateFrom": "240926",
            "orderDateTo": "240926",
            "server": "PLEXDES"
        }

        # Fazer a requisição para a API Control-M Services
        response = requests.post(api_url, headers=headers, json=data, verify=False)
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

        # Preparar dados para inserção na tabela JOB_EXEA_CTM
        job_exea_ctm_data = []
        for job in jobs_data:
            for sch_job in sch_agdd_data:
                if (job['ctm'] == sch_job['nm_SVDR'] and
                        job['folder'] == sch_job['pas_PAI'] and
                        job['name'] == sch_job['nm_MBR'] and
                        job['subApplication'] == sch_job['sub_apl']):
                    job_exea_ctm_data.append({
                        'idfr_sch': sch_job['idfr_sch'],
                        'idfr_exea': job['jobId'][-5:],
                        'dt_mov': job['orderDate'],
                        'obs_job': '',
                        'nr_exea': job['numberOfRuns'],
                        'flx_atu': True,
                        'est_jobh': job['held'],
                        'est_excd': job['deleted'],
                        'idfr_est_job': 'regra_a_ser_definida',
                        'dt_atl': datetime.now()
                    })

        # Gravar os dados na tabela JOB_EXEA_CTM
        repo.insert_job_exea_ctm_data(job_exea_ctm_data)
        repo.disconnect()

        return {"status": "success", "message": "Dados dos jobs atualizados com sucesso"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
