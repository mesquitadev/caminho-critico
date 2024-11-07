import os
import traceback
from datetime import datetime

import requests
from fastapi import HTTPException

from sgs_caminho_critico.dto.request import JobStatusRequest
from sgs_caminho_critico.repository.JobsRepository import JobsRepository
from sgs_caminho_critico.utils import status_mapping, get_pcp_token, format_timestamp


class JobsService:

    def __init__(self):
        self.repo = JobsRepository()

    def atualizar_status_jobs(self, request: JobStatusRequest) -> dict:
        try:
            # Obter o token da PCP Comandos
            access_token = get_pcp_token()
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

            print(f"jobs_data: {jobs_data}")
            # Buscar IDs dos jobs na tabela SCH_AGDD
            sch_agdd_data = self.repo.fetch_sch_agdd_data()

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
                            'hr_inc_exea_job': format_timestamp(job['startTime']) if job['startTime'] else None,
                            'hr_fim_exea_job': format_timestamp(job['endTime']) if job['endTime'] else None
                        })

            # Fetch existing records from the database
            existing_records = self.repo.fetch_existing_job_exea_ctm_data([job['idfr_sch'] for job in job_exea_ctm_data])
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
                self.repo.delete_job_exea_ctm_data([job['idfr_sch'] for job in records_to_delete])

            # Insert new records
            if records_to_insert:
                self.repo.insert_job_exea_ctm_data(records_to_insert)

            return {"status": "success", "message": "Dados dos jobs atualizados com sucesso",
                    "updated_jobs": job_exea_ctm_data}
        except Exception as e:
            error_message = {
                "status": "error",
                "trace": traceback.format_exc(),
                "message": "Erro ao atualizar os dados dos jobs",
                "error_message": str(e)
            }
            raise HTTPException(status_code=500, detail=error_message)
