import pytest
from fastapi import HTTPException

from sgs_caminho_critico.service.ReportService import ReportService


def test_pegar_relatorios_do_inventario_e_salvar_no_csv_success(mocker, mock_repo):
    # Mockar a variável de ambiente CSV_FILES
    mocker.patch('os.getenv', return_value='/path/to/csv')

    # Mockar o método fetch_and_save_records_to_csv do repositório JobsRepository
    mock_repo = mocker.patch(
        'sgs_caminho_critico.repository.JobsRepository.JobsRepository.fetch_and_save_records_to_csv')

    # Chamar o método que está sendo testado
    response = ReportService.pegar_relatorios_do_inventario_e_salvar_no_csv()

    # Verificar se o método fetch_and_save_records_to_csv foi chamado com o caminho correto
    mock_repo.assert_called_once_with('/path/to/csv\\edges_novo_cp.csv')

    # Verificar se o retorno está correto
    assert response == {"message": "Registros salvos no csv com sucesso!"}


def test_pegar_relatorios_do_inventario_e_salvar_no_csv_env_var_not_set(mocker):
    # Mockar a variável de ambiente CSV_FILES para retornar None
    mocker.patch('os.getenv', return_value=None)

    # Chamar o método que está sendo testado e verificar se a exceção é lançada
    with pytest.raises(HTTPException) as exc_info:
        ReportService.pegar_relatorios_do_inventario_e_salvar_no_csv()

    # Verificar se o status code e a mensagem de erro estão corretos
    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Variavel de ambiente 'CSV_FILES' não encontrada."
