import os

import networkx as nx
from fastapi import FastAPI, UploadFile
from descendentes import monta_grafo
from utils import jsonify_nodes_edges, is_char_a2z, read_csv_file, upload_file
import aiofiles
app = FastAPI()


@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    for file in files:
        async with aiofiles.open(os.getenv('CSV_FILES')+file.filename, "wb") as f:
            content = await file.read()
            await f.write(content)


@app.get('/api/graph/fields')
def fetch_graph_fields():
    nodes_fields = [{"field_name": "id", "type": "string"},
                    {"field_name": "title", "type": "string"},
                    {"field_name": "subTitle", "type": "string"},
                    {"field_name": "mainStat", "type": "string"},
                    {"field_name": "secondaryStat", "type": "number"},
                    {"color": "red", "displayName": "Failed", "field_name": "arc__failed", "type": "number"},
                    {"color": "green", "displayName": "Passed", "field_name": "arc__passed", "type": "number"},
                    {"displayName": "Role", "field_name": "detail__role", "type": "string"}
                    ]
    edges_fields = [
        {"field_name": "id", "type": "string"},
        {"field_name": "source", "type": "string"},
        {"field_name": "target", "type": "string"},
        {"field_name": "mainStat", "type": "number"}
    ]
    result = {"edges_fields": edges_fields,
              "nodes_fields": nodes_fields}
    return result


@app.get('/api/health')
def check_health():
    return "API is working well! "


@app.get('/api/graph/upload')
def upload_graph_data(ambiente='br'):
    upload_file(ambiente)


@app.get('/api/graph/data')
def fetch_graph_data(rotina=None, grupo=None, tipo=1, ambiente='br'):
    edges = []
    no_inicial = rotina.upper()
    all_edges = []
    no_origem_anterior = []
    itens_entrada = []

    if grupo and is_char_a2z(grupo[0]) is None:
        group = grupo[1:].upper()
    else:
        group = ''

    pasta = os.getenv('CSV_FILES')

    arq_in = ambiente + '_in.csv' if ambiente else None
    arq_out = ambiente + '_out.csv' if ambiente else None

    entrada = read_csv_file(f'{pasta}{arq_in}', ',') if arq_in else None
    saida = read_csv_file(f'{pasta}{arq_out}', ',') if arq_out else None
    if entrada is None or saida is None:
        print('Ambiente não fornecido')
        exit(1)

    if tipo == '1':
        mapa = nx.Graph()
        monta_grafo(no_inicial, group, edges, itens_entrada, mapa, entrada, saida, all_edges, no_origem_anterior)
        return jsonify_nodes_edges(all_edges)
    else:
        return None


def fetch_graph_data_old():
    nodes = [{"id": "1", "title": "Service1", "subTitle": "instance:#2", "detail__role": "load",
              "arc__failed": 0.7, "arc__passed": 0.3, "mainStat": "qaz"},
             {"id": "2", "title": "Service2", "subTitle": "instance:#2", "detail__role": "transform",
              "arc__failed": 0.5, "arc__passed": 0.5, "mainStat": "qaz"},
             {"id": "3", "title": "Service3", "subTitle": "instance:#3", "detail__role": "extract",
              "arc__failed": 0.3, "arc__passed": 0.7, "mainStat": "qaz"},
             {"id": "4", "title": "Service3", "subTitle": "instance:#1", "detail__role": "transform",
              "arc__failed": 0.5, "arc__passed": 0.5, "mainStat": "qaz"},
             {"id": "5", "title": "Service4", "subTitle": "instance:#5", "detail__role": "transform",
              "arc__failed": 0.5, "arc__passed": 0.5, "mainStat": "qaz"}]
    edges = [{"id": "1", "source": "1", "target": "2", "mainStat": 53},
             {"id": "2", "source": "2", "target": "3", "mainStat": 53},
             {"id": "2", "source": "1", "target": "4", "mainStat": 5},
             {"id": "3", "source": "3", "target": "5", "mainStat": 70},
             {"id": "4", "source": "2", "target": "5", "mainStat": 100}]
    result = {"edges": edges, "nodes": nodes}
    return result
