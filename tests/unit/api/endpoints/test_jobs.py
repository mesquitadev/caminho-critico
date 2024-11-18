from unittest import mock

import pytest
from fastapi import HTTPException

from sgs_caminho_critico.service.jobs_service import JobsService
from sgs_caminho_critico.utils import status_mapping, format_timestamp


def test_atualizar_status_jobs_success(mocker, mock_control_m_services_api_url):
    # Mockar o método get_pcp_token
    mocker.patch('sgs_caminho_critico.utils.get_pcp_token', return_value='fake_token')

    # Mockar a resposta do requests.post
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "statuses": [
                {
                    "jobId": "job12345",
                    "folder": "UNKNWN",
                    "ctm": "ctm_server",
                    "name": "job_name",
                    "subApplication": "sub_app",
                    "orderDate": "230101",
                    "numberOfRuns": 1,
                    "held": False,
                    "deleted": False,
                    "status": "ENDED_OK",
                    "startTime": "20230101010101",
                    "endTime": "20230101020202"
                }
            ]
        }
    }
    mocker.patch('requests.post', return_value=mock_response)

    # Mockar os métodos do repositório JobsRepository
    mocker.patch('sgs_caminho_critico.repository.JobsRepository.JobsRepository.fetch_sch_agdd_data',
                 return_value=[
                     {
                         'idfr_sch': 1,
                         'pas_pai': 'UNKNWN',
                         'nm_svdr': 'ctm_server',
                         'nm_mbr': 'job_name',
                         'sub_apl': 'sub_app'
                     }
                 ])
    mock_repo = mocker.patch(
        'sgs_caminho_critico.repository.JobsRepository.JobsRepository.fetch_existing_job_exea_ctm_data',
        return_value=[])
    mock_repo = mocker.patch('sgs_caminho_critico.repository.JobsRepository.JobsRepository.delete_job_exea_ctm_data')
    mock_repo = mocker.patch('sgs_caminho_critico.repository.JobsRepository.JobsRepository.insert_job_exea_ctm_data')

    # Instanciar o serviço
    jobs_service = JobsService()

    # Criar um request mockado
    request = {
        "jobname": "PCPEFLX*",
        "keyBB": "F8711759",
        "limit": 50,
        "orderDateFrom": "241030",
        "orderDateTo": "241030",
        "server": "SYSPLEX1"
    }

    # Chamar o método que está sendo testado
    response = jobs_service.atualizar_status_jobs(request)

    # Verificar se o retorno está correto
    assert response == {"status": "success", "message": "Dados dos jobs atualizados com sucesso", "updated_jobs": [
        {
            'idfr_sch': 1,
            'idfr_exea': '12345',
            'dt_mvt': '2023-01-01',
            'obs_job': '',
            'nr_exea': 1,
            'flx_atu': True,
            'est_jobh': False,
            'est_excd': False,
            'idfr_est_job': status_mapping.get('ENDED_OK', 0),
            'dt_atl': mock.ANY,
            'hr_inc_exea_job': format_timestamp('20230101010101'),
            'hr_fim_exea_job': format_timestamp('20230101020202')
        }
    ]}


def test_atualizar_status_jobs_api_error(mocker, mock_control_m_services_api_url):
    # Mockar o método get_pcp_token
    mocker.patch('sgs_caminho_critico.utils.get_pcp_token', return_value='fake_token')

    # Mockar a resposta do requests.post com erro
    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mocker.patch('requests.post', return_value=mock_response)

    # Instanciar o serviço
    jobs_service = JobsService()

    # Criar um request mockado
    request = {
        "jobname": "PCPEFLX*",
        "keyBB": "F8711759",
        "limit": 50,
        "orderDateFrom": "241030",
        "orderDateTo": "241030",
        "server": "SYSPLEX1"
    }

    # Chamar o método que está sendo testado e verificar se a exceção é lançada
    with pytest.raises(HTTPException) as exc_info:
        jobs_service.atualizar_status_jobs(request)

    # Verificar se o status code e a mensagem de erro estão corretos
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail['message'] == "Erro ao atualizar os dados dos jobs"


def test_atualizar_status_jobs_exception(mocker, mock_control_m_services_api_url):
    # Mockar o método get_pcp_token
    mocker.patch('sgs_caminho_critico.utils.get_pcp_token', return_value='fake_token')

    # Mockar uma exceção do requests.post
    mocker.patch('requests.post', side_effect=Exception('Error'))

    # Instanciar o serviço
    jobs_service = JobsService()

    # Criar um request mockado
    request = {
        "jobname": "PCPEFLX*",
        "keyBB": "F8711759",
        "limit": 50,
        "orderDateFrom": "241030",
        "orderDateTo": "241030",
        "server": "SYSPLEX1"
    }
    # Chamar o método que está sendo testado e verificar se a exceção é lançada
    with pytest.raises(HTTPException) as exc_info:
        jobs_service.atualizar_status_jobs(request)

    # Verificar se o status code e a mensagem de erro estão corretos
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail['status'] == "error"
    assert exc_info.value.detail['message'] == "Erro ao atualizar os dados dos jobs"
    assert "Error" in exc_info.value.detail['error_message']
