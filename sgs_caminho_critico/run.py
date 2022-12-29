import os
import re
import networkx as nx
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

from antecessores import monta_grafo_ant
from descendentes import monta_grafo
from pzowe import Pzowe
from utils import jsonify_nodes_edges, read_csv_file, save_graph_to_file, get_file_name, \
    is_file_exists, get_json_content, remove_files_by_pattern, remove_empty_elements, \
    jsonify_parent_son, create_condex_lists, create_condex_file_from_list, combine_condin_condex_files
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
    group = 'ng' if grupo is None else 'ng'  # -> retirei grupo até ver como a lógica vai lidar com isso else grupo

    path = os.getenv('CSV_FILES')
    # cfg_file_name = 'cfg_file'

    arq_in = ambiente + '_in.csv' if ambiente else None
    arq_out = ambiente + '_out.csv' if ambiente else None

    entrada = read_csv_file(f'{path}{arq_in}', ',') if arq_in else None
    saida = read_csv_file(f'{path}{arq_out}', ',') if arq_out else None
    if entrada is None or saida is None:
        print('Ambiente não fornecido')
        exit(1)

    json_file_name = get_file_name(routine=no_inicial, graph_type=tipo, plex=ambiente, group=group)
    # create_json_from_csv(path, cfg_file_name)
    # parms_json = get_json_file_contents(path, cfg_file_name)  # não apagar
    # make_file_names(json_file_name) # gera nomes dos mapas sem a data  # não apagar
    end_part = '\\d{4,4}-\\d{2,2}-\\d{2,2}'
    extension = ".json"
    file2_remove = re.compile(f"({json_file_name[:-15]})({end_part}{extension})")
    remove_files_by_pattern(path, file2_remove, json_file_name)
    if is_file_exists(path, json_file_name):
        return get_json_content(path, json_file_name)

    if tipo == '1':
        mapa = nx.Graph()
        group = ''  # if group == 'ng' else group -> retirado grupo aqui até ver como lógica vai lidar com isso
        monta_grafo(no_inicial, group, edges, itens_entrada, mapa, entrada, saida, all_edges, no_origem_anterior)
    else:  # antecedentes
        # group = ''  # if group == 'ng' else group -> retirado grupo aqui até ver como lógica vai lidar com isso
        mapa = nx.Graph()
        monta_grafo_ant(no_origem=no_inicial, edges=edges, no_destino=itens_saida, mapa=mapa, entrada=entrada,
                        saida=saida, all_edges=all_edges, no_origem_anterior=no_origem_anterior)

    map_text_name = f'm_{json_file_name[:-19]}.json'.upper()

    if all_edges:
        graph_json = jsonify_nodes_edges(remove_empty_elements(all_edges))
        save_graph_to_file(graph_json, path, json_file_name)
        mapa_textual = jsonify_parent_son(all_edges)
        save_graph_to_file(mapa_textual, path, map_text_name)  # 'm_acld250_br_1.json'
        return graph_json
    else:
        json_alert = {"edges": [], "nodes": [{"id": "", "title": "MAPA", "subTitle": "", "mainStat": "ROTINA SEM",
                                              "secondaryStat": "", "arc__failed": 1.0, "arc__passed": 0.0}]}
        save_graph_to_file(json_alert, path, json_file_name)


@app.get('/api/graph/text')
def fetch_graph_text(rotina=None, tipo=1, ambiente='br'):
    path = os.getenv('CSV_FILES')
    map_name = f'm_{rotina}_{ambiente}_{tipo}.json'.upper()
    if is_file_exists(path, map_name):
        return get_json_content(path, map_name)


@app.post('/api/graph/unite_conds')
def combine_condex(previas_jcl, wrk_in_file, wrk_out_file, ambiente='br', delimiter=';'):
    try:
        pz = Pzowe()
        if pz.is_logged(ambiente.upper()):
            mf_frc_list = pz.get_dataset_contents(os.getenv('FRC_DTSET'))
        else:
            mf_frc_list = None
        # mf_frc_list = pz.get_dataset_contents(os.getenv('FRC_DTSET')) if pz.is_logged(ambiente.upper()) else None # arquivo de forces jcl
        mf_frc_list = mf_frc_list[1].split('\n') if mf_frc_list is not None and mf_frc_list[0] == 'ok' else None
        path = os.getenv('CSV_FILES')
        path = path[:-1] if path[-1] == ';' else path
        path = path + "\\" if path[-1] != "\\" else path
        condex_in_file = f'{ambiente}_ex_in.csv'.lower()  # br_ex_in.csv - tmp file apagar
        condex_out_file = f'{ambiente}_ex_out.csv'.lower()  # br_ex_out.csv - tmp file apagar
        condin_file = f'{ambiente}_cond_in.csv'.lower()  # "br_cond_in.csv" - relatório vindo ctm
        condout_file = f'{ambiente}_cond_out.csv'.lower()  # "br_cond_out.csv" - relatório vindo ctm
        # condex_file = condex_file.lower()  # condicoes_externas.csv, obtido do arquivo do thiago ===>> automatizar criação zowe
        previas_jcl = previas_jcl.lower()  # previas_jcl.csv obtido db2, manter esta base sempre

        # gera listas de condições externas era condex_file
        condex_in_lst, condex_out_lst = create_condex_lists(path=path, csv_source=mf_frc_list,
                                                            previas_jcl=previas_jcl, delimiter=delimiter)
        # gera arquivos de condições externas já formatados a partir da respectiva lista de condições externas
        create_condex_file_from_list(condex_in_lst, condex_in_file, path_=path)  # "br_in_ex.csv"
        create_condex_file_from_list(condex_out_lst, condex_out_file, path_=path)  # "br_out_ex.csv"
        # combina arquivos de condições internas e externas, gerando arquivo de trabalho do algoritmo
        combine_condin_condex_files([condin_file, condex_in_file], wrk_in_file, path_=path)  # wrk = br_in.csv
        combine_condin_condex_files([condout_file, condex_out_file], wrk_out_file, path_=path)  # wrk = br_out.csv
        return 'Arquivos gerados com sucesso'
    except FileNotFoundError or FileExistsError:
        return 'Algum arquivo está faltando para gerar os arquivos base'
