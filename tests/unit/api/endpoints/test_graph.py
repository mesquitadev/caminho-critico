import pytest
import requests
from fastapi import HTTPException
from sgs_caminho_critico.service.graph_service import GraphService, buscar_dados_job_pcp_comandos


def test_processar_dados_success(mock_csv_file, mocker):
    # Mockar os métodos utilitários
    mocker.patch('sgs_caminho_critico.utils.read_csv_file', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.construir_grafo', return_value={})
    mocker.patch('sgs_caminho_critico.utils.encontrar_caminho', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.remover_repetidos', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.exibir_edges', return_value=[])

    # Mockar os métodos do repositório JobsRepository

    mock_repo = mocker.patch('sgs_caminho_critico.repository.JobsRepository.JobsRepository.fetch_nodes_data',
                             return_value=[])
    mock_repo = mocker.patch('sgs_caminho_critico.repository.JobsRepository.JobsRepository.fetch_edges',
                             return_value=[])
    # Instanciar o serviço
    graph_service = GraphService()
    # Chamar o método que está sendo testado
    response = graph_service.processar_dados('150003', '150008')

    # Verificar se o retorno está correto
    assert response == {'nodes': [], 'edges': []}


def test_processar_dados_file_not_found(mock_csv_file, mocker):
    # Mockar os.path.exists para retornar False
    mocker.patch('os.path.exists', return_value=False)

    # Instanciar o serviço
    graph_service = GraphService()

    # Chamar o método que está sendo testado e verificar se a exceção é lançada
    with pytest.raises(HTTPException) as exc_info:
        graph_service.processar_dados('rotina_inicial', 'rotina_destino')

    # Verificar se o status code e a mensagem de erro estão corretos
    assert exc_info.value.status_code == 500


def test_buscar_dados_job_pcp_comandos_success(mocker, mock_control_m_services_api_url):
    # Mockar o método get_pcp_token
    mocker.patch('sgs_caminho_critico.utils.get_pcp_token', return_value='fake_token')

    # Mockar a resposta do requests.post
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'data': {'some_key': 'some_value'}}
    mocker.patch('requests.post', return_value=mock_response)

    # Chamar a função que está sendo testada
    response = buscar_dados_job_pcp_comandos('orderid', 'ambiente')

    # Verificar se o retorno está correto
    assert response is None


def test_buscar_dados_job_pcp_comandos_request_exception(mocker, mock_control_m_services_api_url):
    # Mockar o método get_pcp_token
    mocker.patch('sgs_caminho_critico.utils.get_pcp_token', return_value='fake_token')

    # Mockar uma exceção do requests.post
    mocker.patch('requests.post', side_effect=requests.exceptions.RequestException('Error'))

    # Chamar a função que está sendo testada e verificar se a exceção é levantada
    with pytest.raises(requests.exceptions.RequestException):
        buscar_dados_job_pcp_comandos('orderid', 'ambiente')
