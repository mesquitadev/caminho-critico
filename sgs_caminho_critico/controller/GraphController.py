import os

from fastapi import APIRouter, HTTPException
import json

from sgs_caminho_critico.repository.CaminhoCriticoRepository import CaminhoCriticoRepository
from sgs_caminho_critico.utils import read_csv_file, construir_grafo, encontrar_caminho, remover_repetidos, exibir_edges

router = APIRouter()


@router.get("/graph/fields", response_model=dict, response_description="Retorna os campos utilizados no grafo")
def get_graph_fields():
    try:
        edges_fields = [
            {"field_name": "id", "type": "string"},
            {"field_name": "source", "type": "string"},
            {"field_name": "target", "type": "string"},
            {"field_name": "mainStat", "type": "string"},
            {"field_name": "secondaryStat", "type": "string"}
        ]

        nodes_fields = [
            {"field_name": "id", "type": "string"},
            {"field_name": "title", "type": "string"},
            {"field_name": "mainStat", "type": "string"},
            {"field_name": "subTitle", "type": "string"},
            {
                "color": "red",
                "displayName": "Failed",
                "field_name": "arc__failed",
                "type": "number",
            },
            {
                "color": "green",
                "displayName": "Passed",
                "field_name": "arc__passed",
                "type": "number",
            },
            {
                "displayName": "Pasta",
                "field_name": "detail__pasta",
                "type": "string"
            },
            {
                "displayName": "Ambiente",
                "field_name": "detail__amb",
                "type": "string"
            }

        ]

        result = {
            "edges_fields": edges_fields,
            "nodes_fields": nodes_fields
        }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/graph/data", response_model=dict, response_description="Processa dados do CSV e retorna em JSON")
def processar_dados_retornar_json(rotina_inicial: str, rotina_destino: str):
    try:
        db_config = {
            'dbname': 'pcp',
            'user': 'user_gprom63',
            'password': 'magic123',
            'host': 'silo01.postgresql.bdh.desenv.bb.com.br',
            'port': '5432'
        }
        output_file = os.getenv('CSV_FILES') + 'result.json'
        file_name = os.getenv('CSV_FILES') + 'edges_novo_cp.csv'
        if not os.path.exists(file_name):
            raise HTTPException(status_code=404,
                                detail=f"Arquivo {file_name} nao encontrado, favor rodar o endpoint de atualização.")

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
            repo = CaminhoCriticoRepository(**db_config)
            repo.connect()
            nodes_data = repo.fetch_nodes_data(nodes)
            edges_data = repo.fetch_edges(nodes)
            repo.disconnect()

            result = {
                'nodes': [
                    {
                        'id': str(node['id']).strip() if isinstance(node['id'], str) else str(node['id']),
                        'title': node['title'].strip() if isinstance(node['title'], str) else node['title'],
                        'mainStat': node['mainstat'].strip() if isinstance(node['mainstat'], str) else node['mainstat'],
                        'subTitle': node['subtitle'].strip() if isinstance(node['subtitle'], str) else node['subtitle'],
                        'detail__pasta': node['detail__pasta'].strip() if isinstance(node['detail__pasta'], str) else
                        node['detail__pasta'],
                        'detail__amb': node['detail__amb'].strip() if isinstance(node['detail__amb'], str) else node[
                            'detail__amb'],
                        'icon': node['icon'].strip() if isinstance(node['icon'], str) else node['icon'],
                        'color': node['color'].strip() if isinstance(node['color'], str) else node['color'],

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

        # Salvar o resultado em um arquivo JSON para cache
        with open(output_file, 'w') as json_file:
            json.dump(result, json_file, indent=4)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
