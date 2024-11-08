import os
import pytest


@pytest.fixture(autouse=True)
def fluxos_mock():
    mock_fluxos = [{'idfr_flx_rtin_bch': 13, 'idfr_est_flx': 'Finalizado'},
                   {'idfr_flx_rtin_bch': 6, 'idfr_est_flx': 'Aguardando Inicio'},
                   {'idfr_flx_rtin_bch': 7, 'idfr_est_flx': 'Aguardando Inicio'},
                   {'idfr_flx_rtin_bch': 8, 'idfr_est_flx': 'Aguardando Inicio'}
                   ]
    return mock_fluxos


@pytest.fixture(autouse=True)
def fluxo_mock():
    fluxo = [{13}, {2}]
    return fluxo


@pytest.fixture
def mock_csv_file(monkeypatch):
    # Obter o caminho do diretório a partir da variável de ambiente
    csv_files_dir = os.getenv('CSV_FILES')
    csv_file_path = os.path.join(csv_files_dir, 'edges_novo_cp.csv')
    # Criar o arquivo CSV no diretório obtido
    with open(csv_file_path, 'w') as csv_file:
        csv_file.write("source,target\n1,2\n2,3\n3,4")
        # Mockar a função os.path.exists para retornar True
        monkeypatch.setattr(os.path, 'exists', lambda x: x == csv_file_path)

        # Mockar a função read_csv_file para ler o arquivo criado
        def mock_read_csv_file(file_name):
            with open(file_name, 'r') as f:
                return [line.strip().split(',') for line in f.readlines()[1:]]

        monkeypatch.setattr('sgs_caminho_critico.service.FluxoService.read_csv_file', mock_read_csv_file)
        return csv_file_path


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch, tmpdir):
    monkeypatch.setenv('DB_USER', 'test_user')
    monkeypatch.setenv('DB_PASSWORD', 'test_password')
    monkeypatch.setenv('DB_HOST', 'test_host')
    monkeypatch.setenv('DB_NAME', 'test_db')
    monkeypatch.setenv('DB_PORT', '5432')
    monkeypatch.setenv('CSV_FILES', '/csv_files/')
