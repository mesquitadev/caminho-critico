import os
import threading
import time
import networkx as nx
import csv
from datetime import datetime, date, timedelta

import requests
import urllib3
from fastapi import HTTPException


def read_csv_file(file_name, delimiter=','):
    records = []
    with open(file_name, 'r') as file:
        csvreader = csv.DictReader(file, delimiter=delimiter)
        for row in csvreader:
            records.append((row['idfr_sch'], row['idfr_job_exct']))
    return records


def worker(grafo, records, start, end):
    for i in range(start, end):
        origem, destino = records[i]
        grafo.add_edge(origem, destino)


def construir_grafo(records, num_threads=6):
    print('Construindo grafo...')
    start_time = time.time()

    grafo = nx.DiGraph()
    threads = []
    chunk_size = len(records) // num_threads

    for i in range(num_threads):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i != num_threads - 1 else len(records)
        thread = threading.Thread(target=worker, args=(grafo, records, start, end))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"Tempo de processamento: {processing_time:.2f} segundos")

    return grafo


def show_loading_message():
    while getattr(threading.current_thread(), "do_run", True):
        print("Carregando...", end="\r")
        time.sleep(0.5)


def encontrar_caminho(grafo, rotina_inicial, rotina_destino):
    loading_thread = threading.Thread(target=show_loading_message)
    loading_thread.start()
    try:
        caminhos = list(nx.all_simple_paths(grafo, source=rotina_inicial, target=rotina_destino, cutoff=10))
        return caminhos
    except nx.NetworkXNoPath:
        return None
    finally:
        loading_thread.do_run = False
        loading_thread.join()


def exibir_edges(caminho):
    edges = []
    for i in range(len(caminho) - 1):
        origem = caminho[i]
        destino = caminho[i + 1]
        edges.append((origem, destino))
    return edges


def remover_repetidos(caminhos):
    caminhos_unicos = set()
    for caminho in caminhos:
        caminhos_unicos.add(tuple(caminho))
    return [list(caminho) for caminho in caminhos_unicos]


def limpa_campos(field_value):
    if isinstance(field_value, str):
        return field_value.strip()
    else:
        return str(field_value)


def format_order_date(order_date):
    if not order_date:
        return ''
    if isinstance(order_date, str):
        try:
            return datetime.strptime(order_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return datetime.strptime(order_date, '%y%m%d').strftime('%Y-%m-%d')
    elif isinstance(order_date, (datetime, date)):
        return order_date.strftime('%Y-%m-%d')
    else:
        raise ValueError("order_date must be a string, datetime, or date object")


def map_mainstat_to_color_icon(mainstat, est_jobh, est_excd):
    if est_excd and mainstat != 'Ended Ok':
        return {'color': '#900', 'icon': 'times-circle'}
    if est_jobh and mainstat != 'Ended Ok':
        return {'color': '#900', 'icon': 'lock'}

    mapping = {
        'Executing': {'color': '#990', 'icon': 'spinner'},
        'Ended Ok': {'color': '#090', 'icon': 'check-circle'},
        'Abended': {'color': '#900', 'icon': 'bug'},
        'Status unknown': {'color': '#379', 'icon': 'question-circle'},
        'Disappeared': {'color': '#500', 'icon': 'question-circle'},
        'Não encontrado': {'color': '#779', 'icon': 'sync-slash'},
        'não schedulado': {'color': '#779', 'icon': 'sync-slash'}
    }
    return mapping.get(mainstat, {'color': '#379', 'icon': 'stopwatch'})


status_mapping = {
    "Ended OK": 7,
    "Ended Not OK": 8,
    "Wait User": 12,
    "Wait resource": 13,
    "Wait host": 14,
    "Wait workload": 15,
    "Wait Condition": 2,
    "Executing": 4,
    "Status unknown": 16,
    "Desconhecido": 0
}


# Desabilitar avisos de certificado SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Variáveis globais para armazenar o token e a hora da autenticação
token = None
token_expiration = datetime.min


def authenticate():
    global token, token_expiration
    auth_url = f"{os.getenv('CONTROL_M_SERVICES_API_URL')}/login/token"
    auth_data = {
        "grant_type": "",
        "username": os.getenv('CONTROL_M_SERVICES_USERNAME'),
        "password": os.getenv('CONTROL_M_SERVICES_PASSWORD'),
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        "accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(auth_url, headers=headers, data=auth_data, verify=False)
    if response.status_code == 200:
        token = response.json().get("access_token")
        token_expiration = datetime.now() + timedelta(minutes=30)
    else:
        raise HTTPException(status_code=response.status_code, detail="Erro ao autenticar na API do PCP")


def get_pcp_token():
    global token, token_expiration
    if token is None or token_expiration is None or datetime.now() >= token_expiration:
        authenticate()
    return token
