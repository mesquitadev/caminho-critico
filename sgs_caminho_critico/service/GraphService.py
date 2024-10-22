import os
import traceback
from fastapi import HTTPException
import json
from sgs_caminho_critico.repository.JobsRepository import JobsRepository
from sgs_caminho_critico.utils import read_csv_file, construir_grafo, encontrar_caminho, remover_repetidos, \
    exibir_edges, limpa_campos, format_order_date, map_mainstat_to_color_icon


class GraphService:
    @staticmethod
    def processar_dados(rotina_inicial: str, rotina_destino: str) -> dict:
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
                repo = JobsRepository()
                nodes_data = repo.fetch_nodes_data(nodes)
                edges_data = repo.fetch_edges(nodes)

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
                            'color': map_mainstat_to_color_icon(node['mainstat'], node['held'], node['deleted'])['color'],
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
