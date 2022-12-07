import os
import re
import networkx as nx
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

from antecessores import monta_grafo_ant
from descendentes import monta_grafo
from utils import jsonify_nodes_edges, read_csv_file, save_graph_to_file, get_file_name, \
    exists_json_file, get_json_content, remove_files_by_matching_pattern, remove_empty_elements
import aiofiles

app = FastAPI()


@app.post("/uploadfiles/")
async def create_upload_files(files: list[UploadFile]):
    try:
        for file in files:
            async with aiofiles.open(os.getenv('CSV_FILES') + file.filename, "wb") as f:
                content = await file.read()
                await f.write(content)
    except Exception as e:
        return JSONResponse(status_code=500, content={'erro': format(e)})


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


@app.get('/api/graph/data')
def fetch_graph_data(rotina=None, grupo=None, tipo=1, ambiente='br'):
    edges = []
    no_inicial = rotina.upper()
    all_edges = []
    no_origem_anterior = []
    itens_entrada = []
    itens_saida = []
    # if grupo is not None:
    #     if is_char_a2z(grupo[0]) is None:
    #         group = grupo[1:].upper()
    #     else:
    #         group = grupo
    # else:
    #     group = 'ng'
    group = 'ng' if grupo is None else 'ng'  # -> retirei grupo até ver como a lógica vai lidar com isso else grupo
    # if grupo is None:
    #     group = 'ng'
    # else:
    #     group = grupo

    path = os.getenv('CSV_FILES')

    arq_in = ambiente + '_in.csv' if ambiente else None
    arq_out = ambiente + '_out.csv' if ambiente else None

    entrada = read_csv_file(f'{path}{arq_in}', ',') if arq_in else None
    saida = read_csv_file(f'{path}{arq_out}', ',') if arq_out else None
    if entrada is None or saida is None:
        print('Ambiente não fornecido')
        exit(1)

    if tipo == '1':
        json_file_name = get_file_name(routine=no_inicial, graph_type=tipo, plex=ambiente, group=group)
        if exists_json_file(path, json_file_name):
            return get_json_content(path, json_file_name)
        else:
            end_part = '\\d{8,8}'
            extension = ".json"
            file2_remove = re.compile(f"({json_file_name[:-15]})({end_part}{extension})")
            remove_files_by_matching_pattern(path, file2_remove)
            mapa = nx.Graph()
            group = ''  # if group == 'ng' else group -> retirado grupo aqui até ver como lógica vai lidar com isso
            monta_grafo(no_inicial, group, edges, itens_entrada, mapa, entrada, saida, all_edges, no_origem_anterior)
            graph_json = jsonify_nodes_edges(remove_empty_elements(all_edges))
            save_graph_to_file(graph_json, path, json_file_name)
            return graph_json
    else:  # antecedentes
        group = ''  # if group == 'ng' else group -> retirado grupo aqui até ver como lógica vai lidar com isso
        json_file_name = get_file_name(routine=no_inicial, graph_type=tipo, plex=ambiente, group=group)
        if exists_json_file(path, json_file_name):
            return get_json_content(path, json_file_name)
        else:
            end_part = '\\d{8,8}'
            extension = ".json"
            file2_remove = re.compile(f"({json_file_name[:-15]})({end_part}{extension})")
            remove_files_by_matching_pattern(path, file2_remove)
            mapa = nx.Graph()
            monta_grafo_ant(no_origem=no_inicial, edges=edges, no_destino=itens_saida, mapa=mapa, entrada=entrada,
                            saida=saida, all_edges=all_edges, no_origem_anterior=no_origem_anterior)
            graph_json = jsonify_nodes_edges(remove_empty_elements(all_edges))
            save_graph_to_file(graph_json, path, json_file_name)
            return graph_json
