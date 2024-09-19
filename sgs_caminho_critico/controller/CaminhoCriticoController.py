import os
import threading
import time
import networkx as nx
import csv
import psycopg2
import json
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter
import logging

caminhos_router = APIRouter()


class PostgresRepository:
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def fetch_nodes_data(self, node_ids):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            select
            'stopwatch' as icon, '#377' as color, 'wait' as mainstat,
            sa.idfr_sch as id, sa.nm_mbr as title, sa.sub_apl as subtitle, sa.pas_pai as detail__pasta, sa.nm_svdr as detail__amb
            from batch.sch_agdd sa
            where idfr_sch in %s
            """
            cursor.execute(query, (tuple(node_ids),))
            return cursor.fetchall()

    def fetch_edges(self, node_ids):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = ("\n"
                     "            select \n"
                     "            ROW_NUMBER() OVER ()  as id,\n"
                     "            source as source,\n"
                     "            target as target,\n"
                     "            mainstat,\n"
                     "            secondarystat\n"
                     "            from\n"
                     "            (select je.idfr_sch as source, je.idfr_job_exct as target, 'FORCE'"
                     " as  mainstat, '' as secondarystat from batch.job_exct je \n"
                     "            union\n"
                     "            select sccs.idfr_sch as source, scce.idfr_sch as target, 'COND'"
                     " as mainstat, c.nm_cnd as secondarystat from batch.sch_crlc_cnd_said sccs "
                     "inner join batch.sch_crlc_cnd_entd scce on sccs.idfr_cnd = scce.idfr_cnd\n"
                     "            inner join batch.cnd c on sccs.idfr_cnd = c.idfr_cnd \n"
                     "            where sccs.cmdo_cnd = 'A' and scce.dt_cnd <> 'PREV') as res\n"
                     "            where res.source IN %s and res.target IN %s\n"
                     "            ")
            cursor.execute(query, (tuple(node_ids), tuple(node_ids)))
            return cursor.fetchall()

    def fetch_and_save_records_to_csv(self, csv_file_path):
        # Configurar o log
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        # Verificar se o arquivo CSV existe e apagar se necessário
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            logging.info(f'Arquivo {csv_file_path} apagado antes de atualizar.')

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            select je.idfr_sch, je.idfr_job_exct from batch.job_exct je
            union
            select sccs.idfr_sch, scce.idfr_sch from batch.sch_crlc_cnd_said sccs
            inner join batch.sch_crlc_cnd_entd scce on sccs.idfr_cnd = scce.idfr_cnd
            inner join batch.cnd c on sccs.idfr_cnd = c.idfr_cnd
            where sccs.cmdo_cnd = 'A'
            """
            cursor.execute(query)
            records = cursor.fetchall()

        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['idfr_sch', 'idfr_job_exct']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record)


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


def construir_grafo(records, num_threads=4):
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


def get_node_color(grafo, root_node, origin_color, others_color):
    colors = []
    for node in grafo:
        if node == root_node:
            colors.append(origin_color)
        else:
            colors.append(others_color)
    return colors


def remover_repetidos(caminhos):
    caminhos_unicos = set()
    for caminho in caminhos:
        caminhos_unicos.add(tuple(caminho))
    return [list(caminho) for caminho in caminhos_unicos]


@caminhos_router.get("/graph/fields/")
def main(rotina_inicial: str, rotina_destino: str):
    db_config = {
        'dbname': 'pcp',
        'user': 'user_gprom63',
        'password': 'magic123',
        'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
        'port': '5432'
    }
    output_file = os.getenv('CSV_FILES') + 'result.json'
    file_name = os.getenv('CSV_FILES') + '/edges_novo_cp.csv'
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
        repo = PostgresRepository(**db_config)
        repo.connect()
        nodes_data = repo.fetch_nodes_data(nodes)
        edges_data = repo.fetch_edges(nodes)
        repo.disconnect()

        result = {
            'nodes': nodes_data,
            'edges': [
                {
                    'id': edge['id'],
                    'source': edge['source'],
                    'target': edge['target'],
                    'mainstat': edge['mainstat'],
                    'secondarystat': edge['secondarystat']
                } for edge in edges_data
            ]
        }
    else:
        result = {'nodes': [], 'edges': []}

    # Salvar o resultado em um arquivo JSON
    with open(output_file, 'w') as json_file:
        json.dump(result, json_file, indent=4)

    return result


@caminhos_router.get("/save_records_to_csv/")
def save_records_to_csv():
    db_config = {
        'dbname': 'pcp',
        'user': 'user_gprom63',
        'password': 'magic123',
        'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
        'port': '5432'
    }
    csv_file_path = os.getenv('CSV_FILES') + '/edges_novo_cp.csv'
    repo = PostgresRepository(**db_config)
    repo.connect()
    repo.fetch_and_save_records_to_csv(csv_file_path)
    repo.disconnect()
    return {"message": "Registros salvos no csv com sucesso!"}

# if __name__ == '__main__':
#     file_name = 'edges_novo_cp.csv'
#     rotina_inicial = '67958'
#     rotina_destino = '69884'
#     db_config = {
#         'dbname': 'pcp',
#         'user': 'user_gprom63',
#         'password': 'magic123',
#         'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
#         'port': '5432'
#     }
#     output_file = 'result.json'
#     result = main(file_name, rotina_inicial, rotina_destino, db_config, output_file)
#     print(result)
