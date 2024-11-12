import os
import pytest
import tempfile
from unittest.mock import patch

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from sgs_caminho_critico.config import settings
from sgs_caminho_critico.service.FluxoService import FluxoService
from sgs_caminho_critico.repository.JobsRepository import JobsRepository


@pytest.fixture(autouse=True)
def settings_mock():
    settings.pgre_dsn = 'postgresql://user_gprom63:magic123@silo01.postgresql.bdh.desenv.bb.com.br:5432/pcp'


@pytest.fixture
def session():
    # Criar o engine do SQLAlchemy usando a variável DATABASE_URL
    engine = create_engine(
        settings.sqlite_dsn,
        poolclass=StaticPool
    )
    # Criar uma sessão do SQLAlchemy
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    # Fechar a sessão após os testes
    session.close()


@pytest.fixture
def fluxo_service(session, mock_repo):
    # Patch the SessionLocal to return the mock session
    with patch('sgs_caminho_critico.config.Database.SessionLocal', return_value=session):
        service = FluxoService()
        service.repo = mock_repo  # Use the mock repository
        return service


@pytest.fixture
def fluxos_mock():
    return [
        (8, 87310, 87400), (6, 87310, 87400), (7, 19930, 19983),
        (13, 150003, 150008), (9, 150003, 150008), (14, 67958, 69884),
        (15, 26328, 37378), (16, 14767, 15256), (17, 14762, 73050),
        (18, 5733, 75426), (19, 538, 481), (20, 52945, 35986), (21, 5733, 75426)
    ]


@pytest.fixture
def mock_repo(mocker, fluxos_mock):
    repo = mocker.Mock(spec=JobsRepository)
    repo.buscar_fluxos.return_value = fluxos_mock
    repo.buscar_status_fluxos.return_value = [
        {'idfr_flx_rtin_bch': 13, 'idfr_est_flx': 'Finalizado'},
        {'idfr_flx_rtin_bch': 6, 'idfr_est_flx': 'Aguardando Inicio'},
        {'idfr_flx_rtin_bch': 7, 'idfr_est_flx': 'Aguardando Inicio'},
        {'idfr_flx_rtin_bch': 8, 'idfr_est_flx': 'Aguardando Inicio'}
    ]
    repo.buscar_fluxo_por_id.return_value = (13, '2023-01-01 00:00:00', '2023-01-01 12:00:00')
    repo.fetch_nodes_data.return_value = []
    repo.fetch_edges.return_value = []
    repo.update_obs_job.return_value = None
    repo.update_status_fluxo.return_value = [None]
    repo.insert_obs_acpt_exea_flx.return_value = None

    # Mock the db attribute
    mock_db = mocker.Mock()
    mock_db.rollback.return_value = None
    mock_db.close.return_value = None
    repo.db = mock_db

    return repo


@pytest.fixture
def mock_status_fluxos():
    mock_fluxos = [{'idfr_flx_rtin_bch': 13, 'idfr_est_flx': 'Finalizado'},
                   {'idfr_flx_rtin_bch': 6, 'idfr_est_flx': 'Aguardando Inicio'},
                   {'idfr_flx_rtin_bch': 7, 'idfr_est_flx': 'Aguardando Inicio'},
                   {'idfr_flx_rtin_bch': 8, 'idfr_est_flx': 'Aguardando Inicio'}
                   ]
    return mock_fluxos


@pytest.fixture(autouse=True)
def mock_csv_file(monkeypatch):
    # Obter o diretório do projeto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    # Criar um diretório temporário dentro da pasta do projeto
    temp_dir = tempfile.mkdtemp(dir=project_dir)
    csv_file_path = os.path.join(temp_dir, 'edges_novo_cp.csv')
    with open(csv_file_path, 'w') as temp_file:
        # Escrever o conteúdo no arquivo temporário
        temp_file.write(
            "idfr_sch,idfr_job_exct\n"
            "23,40879\n"
            "36,35\n"
            "37,40879\n"
            "40,45\n"
            "41,45\n"
            "42,45\n"
            "43,45\n"
            "71,37\n"
            "88,90\n"
            "89,90\n"
            "108,109\n"
            "137,136\n"
            "140,141\n"
            "151,150\n"
            "188,187\n"
            "191,190\n"
            "203,50034\n"
            "150003,150004\n"
            "150003,150005\n"
            "150004,150006\n"
            "150005,150006\n"
            "150006,150007\n"
            "150007,150008\n"
        )

    # Set the CSV_FILES environment variable to the directory of the temporary file
    monkeypatch.setenv('CSV_FILES', temp_dir)
    # Mock the os.path.exists function to return True
    monkeypatch.setattr(os.path, 'exists', lambda x: x == csv_file_path)

    # Mock the read_csv_file function to read the existing file
    def mock_read_csv_file(file_name):
        if file_name == csv_file_path:
            with open(file_name, 'r') as f:
                return [line.strip().split(',') for line in f.readlines()[1:]]
        else:
            raise FileNotFoundError(f"Arquivo {file_name} não encontrado.")

    monkeypatch.setattr('sgs_caminho_critico.utils.read_csv_file', mock_read_csv_file)

    yield temp_dir

    # Apagar o arquivo temporário após a conclusão dos testes
    os.remove(csv_file_path)
    os.rmdir(temp_dir)


@pytest.fixture
def mock_control_m_services_api_url(monkeypatch):
    # Set the CONTROL_M_SERVICES_API_URL environment variable
    monkeypatch.setenv('CONTROL_M_SERVICES_API_URL', 'http://api.url')
