# from unittest import mock
#
# from sgs_caminho_critico.controller.FluxoController import processar_fluxos, retornar_status_fluxo, \
#     retornar_status_fluxo_por_id
# from sgs_caminho_critico.service.FluxoService import FluxoService
#
#
# def test_processar_fluxos(fluxos_mock, mock_csv_file):
#     response = processar_fluxos()
#     assert response == {"message": "Fluxos atualizados com sucesso!"}
#
#
# def test_retornar_status_fluxo(fluxos_mock, mocker):
#     fluxo_service = FluxoService()
#     repo_buscar_fluxos_mock = fluxo_service.repo.buscar_status_fluxos = mocker.Mock(return_value=fluxos_mock)
#
#     fluxos = fluxo_service.get_status_fluxos()
#     assert len(fluxos) > 0
#     assert len(fluxos_mock) > 0
#     assert repo_buscar_fluxos_mock.call_count == 1
#
#
# def test_retornar_status_fluxo_por_id(fluxo_mock):
#     fluxo_service = FluxoService()
#     fluxo_service.repo.buscar_status_fluxo_por_id = mock.MagicMock(return_value=fluxo_mock)
#     fluxo = fluxo_service.get_status_fluxo_by_id('13')
#     assert fluxo == fluxo_mock
#
#
# def test_retornar_status_fluxo_com_erro(fluxo_mock):
#     fluxo_service = FluxoService()
#     fluxo_service.repo.buscar_status_fluxo_por_id = mock.MagicMock(return_value=fluxo_mock)
#     fluxo = fluxo_service.get_status_fluxo_by_id('50')
#     print(f"flx {fluxo}")
#     assert fluxo == fluxo_mock
