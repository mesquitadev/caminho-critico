import json
import threading
import time
import networkx as nx
from sgs_caminho_critico.repository.RotinaRepository import RotinaRepository


class CaminhoCriticoService:
    def __init__(self, db_config):
        self.db_config = db_config

    def construir_grafo(self, records):
        grafo = nx.DiGraph()
        for record in records:
            grafo.add_edge(record['source'], record['target'])
        return grafo

    def show_loading_message(self):
        while getattr(threading.current_thread(), "do_run", True):
            print("Carregando...", end="\r")
            time.sleep(0.5)

    def encontrar_caminho(self, grafo, rotina_inicial, rotina_destino):
        loading_thread = threading.Thread(target=self.show_loading_message)
        loading_thread.start()
        try:
            caminhos = list(nx.all_simple_paths(grafo, source=rotina_inicial, target=rotina_destino, cutoff=10))
            return caminhos
        except nx.NetworkXNoPath:
            return None
        finally:
            loading_thread.do_run = False
            loading_thread.join()

    def exibir_edges(self, caminho):
        edges = []
        for i in range(len(caminho) - 1):
            origem = caminho[i]
            destino = caminho[i + 1]
            edges.append((origem, destino))
        return edges

    def remover_repetidos(self, caminhos):
        caminhos_unicos = set()
        for caminho in caminhos:
            caminhos_unicos.add(tuple(caminho))
        return [list(caminho) for caminho in caminhos_unicos]

    def fetch_nodes_data(self, nodes):
        repo = RotinaRepository()
        query = f"SELECT * FROM your_table_name WHERE id IN ({','.join(map(str, nodes))})"
        result = repo.execute_manual_select(query)
        repo.close()
        return result

    def processar_caminhos(self, file_name, rotina_inicial, rotina_destino):
        records = self.read_csv_file(file_name)
        grafo = self.construir_grafo(records)
        caminhos = self.encontrar_caminho(grafo, rotina_inicial, rotina_destino)
        if caminhos:
            caminhos_unicos = self.remover_repetidos(caminhos)
            nodes = set()
            edges = []
            for caminho in caminhos_unicos:
                nodes.update(caminho)
                edges.extend(self.exibir_edges(caminho))
            nodes = list(nodes)

            nodes_data = self.fetch_nodes_data(nodes)

            result = {'nodes': nodes_data,
                      'edges': [{'source': origem, 'target': destino} for origem, destino in edges]}
        else:
            result = {'nodes': [], 'edges': []}

        return result
