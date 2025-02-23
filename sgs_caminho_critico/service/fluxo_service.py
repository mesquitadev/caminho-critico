import os
import traceback
from datetime import datetime
from fastapi import HTTPException
import json
import requests
import logging
from sgs_caminho_critico.repository.jobs_repository import JobsRepository
from sgs_caminho_critico.utils import read_csv_file, construir_grafo, encontrar_caminho, remover_repetidos, \
    exibir_edges, get_pcp_token, format_timestamp, \
    get_next_nodes, set_node_status, map_status, concatenar_data_hora, determinar_data


def buscar_dados_job_pcp_comandos(orderid, ambiente):
    access_token = get_pcp_token()
    api_url = f"{os.getenv('CONTROL_M_SERVICES_API_URL')}/run/waiting-info"
    payload = {
        "id": orderid,
        "server": ambiente,
        "user_personal_id": "c1333806"
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, verify=True)
        jobs_data = response.json().get("data", {})
        # Extract the specific message
        hold_state_message = jobs_data if len(jobs_data) > 1 else None
        print(F"response {response.json().get('error')}")
        return hold_state_message
    except requests.exceptions.RequestException as e:
        return f"Error executing PCP command: {e}"


class FluxoService:
    def __init__(self):
        self.repo = JobsRepository()

    def atualizar_status_fluxo(self) -> dict:
        try:
            file_name = os.getenv('CSV_FILES') + os.path.sep + 'edges_novo_cp.csv'
            if not os.path.exists(file_name):
                raise FileNotFoundError(f"Arquivo {file_name} não encontrado, favor rodar o endpoint de atualização.")

            records = read_csv_file(file_name)
            grafo = construir_grafo(records)
            fluxos = self.repo.buscar_fluxos()

            current_date = datetime.now().strftime('%Y-%m-%d')
            fluxo_messages = {}

            for fluxo in fluxos:
                id_fluxo, source, target = fluxo
                logging.info(f"Executando fluxo: {source}, fluxo: {target}")
                # Verifica se os nós fonte e destino estão no grafo
                if str(source) not in grafo or str(target) not in grafo:
                    logging.warning(f"Nó fonte {source} ou nó destino {target} não encontrado no grafo.")
                    continue

                caminhos = encontrar_caminho(grafo, str(source), str(target))
                if caminhos:
                    caminhos_unicos = remover_repetidos(caminhos)
                    nodes = set()
                    edges = []
                    for caminho in caminhos_unicos:
                        nodes.update(caminho)
                        edges.extend(exibir_edges(caminho))
                    nodes = list(nodes)

                    # Conectar ao banco de dados e buscar dados dos nós e edges
                    nodes_data = self.repo.fetch_nodes_data(nodes)
                    edges_data = self.repo.fetch_edges(nodes)
                    # Filtrar nós pela data corrente
                    nodes_data = [node for node in nodes_data if node['odate'] == current_date]
                    result = get_next_nodes(nodes_data, edges_data)

                    # Atualizar o campo obs_job na tabela JOB_EXEA_CTM
                    for node in result.get('nodes', []):
                        sub_title = node.get('subTitle')
                        orderid = sub_title[-5:] if sub_title else None
                        ambiente = sub_title.split(':')[0] if sub_title else None
                        if orderid:
                            obs = buscar_dados_job_pcp_comandos(orderid, ambiente)
                        else:
                            obs = "Não schedulado"
                        if id_fluxo not in fluxo_messages:
                            fluxo_messages[id_fluxo] = []
                        fluxo_messages[id_fluxo].append(obs)
                        self.repo.update_obs_job(orderid, obs)

                    held_nodes = any(node.get('held') for node in nodes_data)
                    deleted_nodes = any(node.get('deleted') for node in nodes_data)
                    abended_nodes = any(node.get('mainstat') == 'Abended' for node in nodes_data)
                    if nodes_data:
                        source_node = next((node for node in nodes_data if node['id'] == source), None)
                        target_node = next((node for node in nodes_data if node['id'] == target), None)

                        start_time = format_timestamp(source_node.get('start_time')) if source_node and source_node.get(
                            'start_time') else None
                        end_time = format_timestamp(target_node.get('end_time')) if target_node and target_node.get(
                            'end_time') else None
                    else:
                        start_time = None
                        end_time = None

                    # Ensure start_time and end_time are None if they are empty strings
                    start_time = start_time if start_time else None
                    end_time = end_time if end_time else None

                    # Verificar se o fluxo está atrasado
                    fluxo_data = self.repo.buscar_fluxo_por_id(id_fluxo)
                    in_atr = False
                    if fluxo_data:
                        current_time = datetime.now()
                        hr_inc_flx = fluxo_data[1]  # Assuming this is in 'HH:MM:SS' format
                        hr_fim_flx = fluxo_data[2]  # Assuming this is in 'HH:MM:SS' format
                        # Extrair a hora de hr_inc_flx e hr_fim_flx
                        hora_inc_flx = hr_inc_flx.seconds // 3600
                        hora_fim_flx = hr_fim_flx.seconds // 3600

                        # Determinar a data correta para hr_inc_flx e hr_fim_flx
                        data_inc_flx = determinar_data(hora_inc_flx)
                        data_fim_flx = determinar_data(hora_fim_flx)

                        # Concatenate data_inc_flx and data_fim_flx with hr_inc_flx and hr_fim_flx
                        if hr_inc_flx:
                            hr_inc_flx = concatenar_data_hora(data_inc_flx, str(hr_inc_flx))
                        if hr_fim_flx:
                            hr_fim_flx = concatenar_data_hora(data_fim_flx, str(hr_fim_flx))

                        if start_time is None and (current_time > hr_inc_flx):
                            in_atr = True
                        elif start_time and start_time > datetime.strptime(str(hr_inc_flx), '%Y-%m-%d %H:%M:%S'):
                            in_atr = True

                        if end_time is None and (current_time > hr_fim_flx):
                            in_atr = True
                        elif end_time and end_time > hr_fim_flx:
                            in_atr = True

                    # Atualizar o status do fluxo na tabela ACPT_EXEA_FLX
                    status = set_node_status(start_time, end_time)
                    dados_insert = self.repo.update_status_fluxo(
                        id_fluxo,
                        status,
                        start_time,
                        end_time,
                        abended_nodes,
                        deleted_nodes,
                        held_nodes,
                        in_atr
                    )
                    self.repo.insert_obs_acpt_exea_flx(id_fluxo, dados_insert[0],
                                                       ":".join(fluxo_messages.setdefault(id_fluxo, [])))

            return {"message": "Fluxos atualizados com sucesso!"}

        except Exception as e:
            self.repo.db.rollback()  # Rollback the transaction
            error_message = {
                "error": str(e),
                "trace": traceback.format_exc()
            }
            raise HTTPException(status_code=500, detail=json.dumps(error_message, indent=4))
        finally:
            self.repo.db.close()  # Ensure the database session is closed

    def get_status_fluxos(self):
        try:
            fluxos = self.repo.buscar_status_fluxos()
            status_list = [
                {
                    "id_fluxo": fluxo["idfr_flx_rtin_bch"],
                    "status": map_status(fluxo["idfr_est_flx"])
                }
                for fluxo in fluxos
            ]
            return {"fluxos": status_list}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_status_fluxo_by_id(self, id_fluxo: str):
        try:
            fluxo = self.repo.buscar_status_fluxo_por_id(id_fluxo)
            if not fluxo:
                error_message = {
                    "message": "Fluxo não encontrado",
                }
                return error_message

            fluxo = {
                "id_fluxo": fluxo[0],  # Accessing the first element of the tuple
                "status": map_status(fluxo[1])  # Accessing the second element of the tuple
            }
            return fluxo
        except Exception as e:
            error_message = {
                "error": str(e),
                "trace": traceback.format_exc()
            }
            raise HTTPException(status_code=500, detail=error_message)
