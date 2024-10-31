import os
import traceback
from datetime import datetime
from fastapi import HTTPException
import json
import requests
import logging
from sgs_caminho_critico.repository.JobsRepository import JobsRepository
from sgs_caminho_critico.utils import read_csv_file, construir_grafo, encontrar_caminho, remover_repetidos, \
    exibir_edges, limpa_campos, format_order_date, map_mainstat_to_color_icon, get_pcp_token


def set_node_status(nodes_data):
    held_nodes = [node for node in nodes_data if node.get('held')]
    deleted_nodes = [node for node in nodes_data if node.get('deleted')]
    abended_nodes = [node for node in nodes_data if node.get('mainstat') == 'Abended']
    running_nodes = [node for node in nodes_data if node.get('mainstat') == 'Running']

    if held_nodes:
        return 4  # Job(s) em Held

    if deleted_nodes:
        return 7  # Job(s) deletado(s)

    if len([node for node in nodes_data if node.get('mainstat') == 'Ended Ok']) == len(nodes_data):
        return 1  # Finalizado

    if abended_nodes:
        return 3  # Com abend(s)

    if nodes_data and nodes_data[0].get('mainstat') == 'Ended Ok':
        return 5  # Em execução

    if running_nodes:
        return 5  # Em execução

    return 2  # Aguardando início


def get_next_nodes(nodes_data, edges_data):
    ended_ok_nodes = [node for node in nodes_data if node.get('mainstat') == 'Ended Ok']
    abended_nodes = [node for node in nodes_data if node.get('mainstat') == 'Abended']
    held_nodes = [node for node in nodes_data if node.get('held')]
    deleted_nodes = [node for node in nodes_data if node.get('deleted')]

    if deleted_nodes:
        return {"message": "Job Deletado"}

    if held_nodes:
        return {"message": "Job Em Held"}

    if not ended_ok_nodes:
        return {"message": "Job Aguardando Inicio"}

    if abended_nodes:
        return {"message": "Job Com Abend"}

    if len(ended_ok_nodes) == len(nodes_data):
        return {"message": "Fluxo Concluído"}

    if not ended_ok_nodes:
        nodes_with_predecessors = {edge['target'] for edge in edges_data}
        nodes_without_predecessors = [node for node in nodes_data if node['id'] not in nodes_with_predecessors]
        return {"nodes": nodes_without_predecessors}

    next_nodes = []
    added_node_ids = set()
    for node in ended_ok_nodes:
        successors = [edge['target'] for edge in edges_data if edge['source'] == node['id']]
        for successor in successors:
            if successor not in added_node_ids:
                next_node = next((n for n in nodes_data if n['id'] == successor and n.get('mainstat') != 'Ended Ok'),
                                 None)
                if next_node:
                    next_nodes.append(next_node)
                    added_node_ids.add(successor)

    mapped_nodes = [
        {
            'id': limpa_campos(node['id']),
            'title': f"{limpa_campos(node['member_name'])} - {limpa_campos(node['sub_appl'])}",
            'mainStat': limpa_campos(node['mainstat']),
            'subTitle': f"{limpa_campos(node['ambiente'])}:{limpa_campos(node['orderid'])}",
            'detail__pasta': limpa_campos(node['pasta']),
            'detail__runnumber': node['run_number'],
            'detail__odate': format_order_date(node['odate']),
            'detail__held': limpa_campos(node['held']),
            'detail__deleted': limpa_campos(node['deleted']),
            'icon': map_mainstat_to_color_icon(node['mainstat'], node['held'], node['deleted'])['icon'],
            'color': map_mainstat_to_color_icon(node['mainstat'], node['held'], node['deleted'])['color'],
        } for node in next_nodes
    ]

    return {"nodes": mapped_nodes}


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
        response = requests.post(api_url, json=payload, headers=headers, verify=False)
        jobs_data = response.json().get("data", {})
        # Extract the specific message
        hold_state_message = jobs_data if len(jobs_data) > 1 else None
        print(F"response {response.json().get('error')}")
        return hold_state_message
    except requests.exceptions.RequestException as e:
        return f"Error executing PCP command: {e}"


class GraphService:
    def __init__(self):
        self.repo = JobsRepository()

    def processar_dados(self, rotina_inicial: str, rotina_destino: str) -> dict:
        try:
            file_name = os.getenv('CSV_FILES') + 'edges_novo_cp.csv'
            if not os.path.exists(file_name):
                raise HTTPException(
                    status_code=404,
                    detail=f"Arquivo {file_name} nao encontrado, favor rodar o endpoint de atualização."
                )

            records = read_csv_file(file_name)
            grafo = construir_grafo(records)
            caminhos = encontrar_caminho(grafo, rotina_inicial, rotina_destino)
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

                result = {
                    'nodes': [
                        {
                            'id': limpa_campos(node['id']),
                            'title': f"{limpa_campos(node['member_name'])} - {limpa_campos(node['sub_appl'])}",
                            'mainStat': limpa_campos(node['mainstat']),
                            'subTitle': f"{limpa_campos(node['ambiente'])}:{limpa_campos(node['orderid'])}",
                            'detail__pasta': limpa_campos(node['pasta']),
                            'detail__runnumber': node['run_number'],
                            'detail__odate': format_order_date(node['odate']),
                            'detail__held': limpa_campos(node['held']),
                            'detail__deleted': limpa_campos(node['deleted']),
                            'icon': map_mainstat_to_color_icon(node['mainstat'], node['held'], node['deleted'])['icon'],
                            'color': map_mainstat_to_color_icon(node['mainstat'], node['held'], node['deleted'])[
                                'color'],
                        } for node in nodes_data
                    ],
                    'edges': [
                        {
                            'id': str(edge['id']),
                            'source': str(edge['source']),
                            'target': str(edge['target']),
                            'mainStat': edge['mainstat'],
                            'secondaryStat': edge['secondarystat']
                        } for edge in edges_data
                    ]
                }
            else:
                result = {'nodes': [], 'edges': []}

            return result
        except Exception as e:
            error_message = {
                "error": str(e),
                "trace": traceback.format_exc()
            }
            raise HTTPException(status_code=500, detail=json.dumps(error_message, indent=4))

    def processar_fluxos(self) -> dict:
        try:
            file_name = os.getenv('CSV_FILES') + 'edges_novo_cp.csv'
            if not os.path.exists(file_name):
                raise HTTPException(
                    status_code=404,
                    detail=f"Arquivo {file_name} nao encontrado, favor rodar o endpoint de atualização."
                )
            # Inicio da Execução
            start_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            records = read_csv_file(file_name)
            grafo = construir_grafo(records)
            fluxos = self.repo.buscar_fluxos()
            current_date = datetime.now().strftime('%Y-%m-%d')
            # Dicionario pra armazenar as mensagens de cada fluxo
            fluxo_messages = {}
            fluxo_status = {}
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
                    # Define o tempo final da execução
                    end_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # Atualizar o campo obs_job na tabela JOB_EXEA_CTM
                    for node in result.get('nodes', []):
                        orderid = node.get('subTitle')[-5:]
                        ambiente = node.get('subTitle').split(':')[0]
                        if orderid:
                            obs = buscar_dados_job_pcp_comandos(orderid, ambiente)
                        else:
                            obs = "Não schedulado"
                        # Coleta mensagens de cada fluxo
                        if id_fluxo not in fluxo_messages:
                            fluxo_messages[id_fluxo] = []
                        fluxo_messages[id_fluxo].append(obs)
                        # Atualiza status
                        self.repo.update_obs_job(orderid, obs)
                    # Atualizar o status do fluxo na tabela ACPT_EXEA_FLX
                    # Determine the status of the nodes
                    status = set_node_status(nodes_data)
                    if id_fluxo in fluxo_messages:
                        dados_insert = self.repo.update_status_fluxo(id_fluxo, status, start_timestamp, end_timestamp)
                        self.repo.insert_obs_acpt_exea_flx(id_fluxo, dados_insert[0],
                                                           ":".join(fluxo_messages[id_fluxo]))

                    # Store the status and nodes of the flow
                    if 'message' in result:
                        fluxo_status[id_fluxo] = {"status": result['message']}
                    elif not result['nodes']:
                        fluxo_status[id_fluxo] = {"status": "Nenhum node encontrado"}
                    else:
                        fluxo_status[id_fluxo] = {"status": "Fluxo em andamento", "nodes": result['nodes']}
                else:
                    fluxo_status[id_fluxo] = {"status": "Nenhum caminho encontrado"}

            return {"fluxos": fluxo_status}

        except Exception as e:
            error_message = {
                "error": str(e),
                "trace": traceback.format_exc()
            }
            raise HTTPException(status_code=500, detail=json.dumps(error_message, indent=4))
