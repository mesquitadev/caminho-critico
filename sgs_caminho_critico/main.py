import json

import psycopg2
from psycopg2.extras import RealDictCursor

from sgs_caminho_critico.utils import read_csv_file, encontrar_caminho, construir_grafo


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
            sa.idfr_sch as id, sa.nm_mbr as title, sa.sub_apl as subtitle,
             sa.pas_pai as detail__pasta, sa.nm_svdr as detail__amb
            from batch.sch_agdd sa where idfr_sch in %s
            """
            cursor.execute(query, (tuple(node_ids),))
            return cursor.fetchall()


def worker(grafo, records, start, end):
    for i in range(start, end):
        origem, destino = records[i]
        grafo.add_edge(origem, destino)


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


def main(file_name, rotina_inicial, rotina_destino, db_config, output_file):
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

        # Conectar ao banco de dados e buscar dados dos nós
        repo = PostgresRepository(**db_config)
        repo.connect()
        nodes_data = repo.fetch_nodes_data(nodes)
        repo.disconnect()

        result = {'nodes': nodes_data, 'edges': [{'source': origem, 'target': destino} for origem, destino in edges]}
    else:
        result = {'nodes': [], 'edges': []}

    # Salvar o resultado em um arquivo JSON
    with open(output_file, 'w') as json_file:
        json.dump(result, json_file, indent=4)

    return result


if __name__ == '__main__':
    file_name = 'edges_novo_cp.csv'
    rotina_inicial = '67958'
    rotina_destino = '69884'
    db_config = {
        'dbname': 'pcp',
        'user': 'user_gprom63',
        'password': 'magic123',
        'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
        'port': '5432'
    }
    output_file = 'result.json'
    result = main(file_name, rotina_inicial, rotina_destino, db_config, output_file)
    print(result)
