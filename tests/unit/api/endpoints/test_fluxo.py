import pytest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError


def test_atualizar_status_fluxo_success(mock_csv_file, mocker, fluxo_service):
    mocker.patch('sgs_caminho_critico.utils.construir_grafo', return_value={})
    mocker.patch('sgs_caminho_critico.utils.encontrar_caminho', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.remover_repetidos', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.exibir_edges', return_value=[])
    mocker.patch('sgs_caminho_critico.utils.get_next_nodes', return_value={'nodes': []})
    mocker.patch('sgs_caminho_critico.service.FluxoService.buscar_dados_job_pcp_comandos',
                 return_value='Não schedulado')
    mocker.patch('sgs_caminho_critico.utils.set_node_status', return_value='status')

    # Chamar o método que está sendo testado
    response = fluxo_service.atualizar_status_fluxo()

    # Verificar se o retorno está correto
    assert response == {"message": "Fluxos atualizados com sucesso!"}


def test_atualizar_status_fluxo_operational_error(mock_csv_file, fluxo_service):
    # Mockar o método buscar_fluxos para lançar uma exceção OperationalError
    fluxo_service.repo.buscar_fluxos.side_effect = OperationalError("no such table: batch.CAD_FLX_RTIN_BCH",
                                                                    None, None)

    # Chamar o método que está sendo testado e verificar se a exceção é tratada corretamente
    with pytest.raises(HTTPException) as exc_info:
        fluxo_service.atualizar_status_fluxo()

    # Verificar se o retorno está correto
    assert exc_info.value.status_code == 500
    assert "no such table: batch.CAD_FLX_RTIN_BCH" in exc_info.value.detail


def test_get_status_fluxos_success(mock_csv_file, mocker, fluxo_service):
    # Mockar o método map_status
    mocker.patch('sgs_caminho_critico.utils.map_status', return_value='status')

    # Chamar o método que está sendo testado
    response = fluxo_service.get_status_fluxos()

    # Verificar se o retorno está correto
    assert len(response) == 1


def test_get_status_fluxos_operational_error(mock_csv_file, fluxo_service):
    # Mockar o método buscar_status_fluxos para lançar uma exceção OperationalError
    fluxo_service.repo.buscar_status_fluxos.side_effect = OperationalError("no such table: "
                                                                           "batch.CAD_FLX_RTIN_BCH",
                                                                           None, None)

    # Chamar o método que está sendo testado e verificar se a exceção é tratada corretamente
    with pytest.raises(HTTPException) as exc_info:
        fluxo_service.get_status_fluxos()

    # Verificar se o retorno está correto
    assert exc_info.value.status_code == 500
    assert "no such table: batch.CAD_FLX_RTIN_BCH" in exc_info.value.detail


def test_get_status_fluxo_by_id_success(mocker, fluxo_service):
    # Mockar o método map_status
    mocker.patch('sgs_caminho_critico.utils.map_status', return_value='Status desconhecido')

    # Mockar o retorno do método buscar_status_fluxo_por_id
    fluxo_service.repo.buscar_status_fluxo_por_id.return_value = (8, 'Finalizado')

    # Chamar o método que está sendo testado
    response = fluxo_service.get_status_fluxo_by_id(8)

    # Verificar se o retorno está correto
    assert response == {"id_fluxo": 8, "status": "Status desconhecido"}
