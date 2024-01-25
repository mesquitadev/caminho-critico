import os
import re
import time
from enum import Enum

import aiofiles
import networkx as nx
from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

from sgs_caminho_critico.antecessores import monta_grafo_antv2
from sgs_caminho_critico.ctm import Ctm, get_data_report
from sgs_caminho_critico.db import DbConnect
from sgs_caminho_critico.descendentes import monta_grafo
from sgs_caminho_critico.pzowe import Pzowe
from sgs_caminho_critico.utils import jsonify_nodes_edges, read_csv_file, save_graph_to_file, get_file_name, \
    is_file_exists, get_json_content, remove_files_by_pattern, remove_empty_elements, \
    jsonify_parent_son, create_forcejcl_dict, cria_csv_frc_jcl, combina_csvs_condicoes_ctm_e_force_jcl, \
    download_file_by_url, cria_csv_cond_jcl, get_condjcl_file_name, complex_list2csv, \
    get_added_cond_via_jcl_line, get_previas_jcl, create_force_cond_via_fts_lists, csv2dict

app = FastAPI()


class Arquivo(Enum):
    PREVIAS_JCL = 'previas_jcl.csv'
    TRAB_CONDS_ENTRADA = '_in.csv'
    TRAB_CONDS_SAIDA = '_out.csv'
    CONDS_VIA_JCL = '_cond_via_jcl.csv'
    FORCE_JCL_ENTRADA = '_frc_in.csv'
    FORCE_JCL_SAIDA = '_frc_out.csv'
    CONDS_ENTRADA_CTM = '_cond_in.csv'
    CONDS_SAIDA_CTM = '_cond_out.csv'
    CONDS_FRC_FTS_IN = '_fts_in.csv'
    CONDS_FRC_FTS_OUT = '_fts_out.csv'


@app.post("/api/run/uploadfiles/")
async def upload_useful_files(files: list[UploadFile]):
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


@app.get('/api/run/health')
def check_api_health():
    return "API is working well! "


@app.get('/api/graph/data')
def fetch_graph_data(rotina=None, grupo=None, tipo=1, ambiente='br'):
    edges = []
    no_inicial = rotina.upper()
    all_edges = []
    no_origem_anterior = []
    itens_entrada = []
    # itens_saida = []
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
        edges_count = 0
        equal_edges = 0
        repeated_conds = 0
        empty_edges = 0
        # group = ''  # if group == 'ng' else group -> retirado grupo aqui até ver como lógica vai lidar com isso
        mapa = nx.Graph()
        monta_grafo_antv2(no_inicial=no_inicial, edges=edges, origem=itens_entrada, mapa=mapa, entrada=entrada,
                          saida=saida, all_edges=all_edges, edges_count=edges_count, equal_edges=equal_edges,
                          repeated_conds=repeated_conds, empty_edges=empty_edges)
        # monta_grafo_ant(no_origem=no_inicial, edges=edges, no_destino=itens_saida, mapa=mapa, entrada=entrada,
        #                 saida=saida, all_edges=all_edges, no_origem_anterior=no_origem_anterior)

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


@app.get("/api/run/report/")
async def get_condition_ctm_report(report, ambiente):
    ctm = Ctm(ambiente.upper())
    ctm.logon()
    fmt = 'csv'

    data = get_data_report(name=report, fmt_rel=fmt, filter_name='Control-M Server Name', filter_value=ctm.plex)
    arquivo = f'{ambiente.lower()}{report}.{fmt}'
    report_data = ctm.roda_relatorio(data)
    if 'errors' not in report_data:
        id_report = report_data['reportId']
        retorno = await ctm.status_relatorio(id_report)
        download_file_by_url(retorno['url'], f'{os.getenv("CSV_FILES")}\\{arquivo}')
        return f'Relatório {arquivo} gerado com sucesso!'
    else:
        return 'No report generated!'


@app.post('/api/run/combina_condicoes_ctm_condicoes_via_jcl')
def combina_condicoes_ctm_condicoes_via_jcl(ambiente, delimiter=';'):
    try:
        pz = Pzowe()
        amb = ambiente.upper()
        force_cnd_fts_file = None
        if pz.is_logged(amb):
            hlq = pz.hlq[amb][0]
            frc_part_file = os.getenv('FRC_DTSET')
            cond_part_file = os.getenv('FRCFTS_DTSET')
            frc_file = f'{hlq}.{frc_part_file}'
            force_cnd_fts_file = get_condjcl_file_name(hlq=hlq, cnd_part_file=cond_part_file)
            # le datasets force via jcl e condicoes via jcl utilizando zowe
            lista_arq_force_jcl = pz.get_dataset_contents(frc_file)
            lst_arq_fts_force_cond_jcl = pz.get_dataset_contents(force_cnd_fts_file)
        else:
            lista_arq_force_jcl = None
            lst_arq_fts_force_cond_jcl = None

        # arquivos úteis
        csv_cond_entrada = f'{ambiente}{Arquivo.TRAB_CONDS_ENTRADA.value}'
        csv_cond_saida = f'{ambiente}{Arquivo.TRAB_CONDS_SAIDA.value}'
        csv_tmp_cond_saida = f'tmp_{csv_cond_saida}'
        lista_arq_force_jcl = lista_arq_force_jcl[1].split('\n') \
            if lista_arq_force_jcl is not None and lista_arq_force_jcl[0] == 'ok' else None
        lst_arq_fts_force_cond_jcl = lst_arq_fts_force_cond_jcl[1].split('\n')[0:-1] \
            if lst_arq_fts_force_cond_jcl is not None and lst_arq_fts_force_cond_jcl[0] == 'ok' else None
        path = os.getenv('CSV_FILES')
        path = path[:-1] if path[-1] == ';' else path
        path = path + "\\" if path[-1] != "\\" else path
        csv_condicoes_jcl = f'{ambiente}{Arquivo.CONDS_VIA_JCL.value}'.lower()  # obtida por query
        csv_forcejcl_entrada = f'{ambiente}{Arquivo.FORCE_JCL_ENTRADA.value}'.lower()
        csv_forcejcl_saida = f'{ambiente}{Arquivo.FORCE_JCL_SAIDA.value}'.lower()
        csv_cond_entrada_ctm = f'{ambiente}{Arquivo.CONDS_ENTRADA_CTM.value}'.lower()
        csv_cond_saida_ctm = f'{ambiente}{Arquivo.CONDS_SAIDA_CTM.value}'.lower()
        arq_previas_jcl = Arquivo.PREVIAS_JCL.value.lower()
        # arq_fts_in = Arquivo.CONDS_FRC_FTS_IN
        # arq_fts_out = Arquivo.CONDS_FRC_FTS_OUT

        # gera arquivo de condições via jcl
        cria_csv_cond_jcl(path=path, filename=csv_condicoes_jcl, lista=lista_arq_force_jcl, mode="w")

        # dicionário de prévias onde a chave é a prévia
        prev_jcl_base = csv2dict(path=path, filename=arq_previas_jcl, key_="previa")
        # gera listas de force via jcl
        lista_frc_jcl_entrada, lista_frc_jcl_saida = create_forcejcl_dict(csv_source=lista_arq_force_jcl,
                                                                          prev_jcl_base=prev_jcl_base,
                                                                          delimiter=delimiter)
        # gera listas de force e cond via fts
        if lst_arq_fts_force_cond_jcl:
            fts_in, fts_out = create_force_cond_via_fts_lists(list_fts=lst_arq_fts_force_cond_jcl,
                                                              previas_dict=prev_jcl_base,
                                                              fts_dataset=force_cnd_fts_file)
        # gera csv de force via jcl
        cria_csv_frc_jcl(lista_frc_jcl_entrada, csv_forcejcl_entrada, path_=path, mode="w")
        cria_csv_frc_jcl(lista_frc_jcl_saida, csv_forcejcl_saida, path_=path, mode="w")

        # combina arquivos de condições do ctm e via jcl, gerando arquivo de trabalho do algoritmo
        combina_csvs_condicoes_ctm_e_force_jcl([csv_cond_entrada_ctm, csv_forcejcl_entrada],
                                               csv_cond_entrada, path_=path)
        combina_csvs_condicoes_ctm_e_force_jcl([csv_cond_saida_ctm, csv_forcejcl_saida],
                                               csv_tmp_cond_saida, path_=path)
        combina_csvs_condicoes_ctm_e_force_jcl([csv_tmp_cond_saida, csv_condicoes_jcl],
                                               csv_cond_saida, path_=path, file_nb=0)
        return f'Arquivos {csv_cond_entrada} e {csv_cond_saida} gerados com sucesso'
    except FileNotFoundError or FileExistsError:
        return 'Algum arquivo está faltando para gerar os arquivos base'


@app.get('/api/run/build_added_conds_by_jcl_csv')
def build_added_conds_by_jcl_csv(amb):
    ambiente = amb.upper()
    inicio = time.time()
    dbcon = DbConnect(ambiente)
    conn = dbcon.connect_db2()
    if conn:
        sql = dbcon.get_prepared_conditions_sql()
        cur = dbcon.get_db_curs(conn, sql)
        registros = dbcon.get_curs_records(cur)
        complex_list2csv(os.getenv('CSV_FILES'), f'{amb}_cond_via_jcl.csv', registros,
                         get_added_cond_via_jcl_line, 1, 2, mode='w')
        fim = time.time()
        t_gasto = fim - inicio
    else:
        return 'Não foi possível conectar ao banco de dados de condições via jcl'
    return f"Gerado arquivo csv com {len(registros) * 1000} registros de condições via jcl com sucesso em " \
           f"{t_gasto / 60: .2f} minutos!"


@app.get('/api/run/build_previas_jcl_csv')
def build_previas_jcl_csv(amb):
    ambiente = amb.upper()
    inicio = time.time()
    dbcon = DbConnect(ambiente)
    conn = dbcon.connect_db2()
    if conn:
        sql = dbcon.get_prepared_previas_sql()
        cur = dbcon.get_db_curs(conn, sql)
        registros = dbcon.get_curs_records(cur)
        complex_list2csv(os.getenv('CSV_FILES'), 'previas_jcl.csv', registros, get_previas_jcl, 0, 2, mode='w',
                         header=True, header_content='previas,jcl')
        fim = time.time()
        t_gasto = fim - inicio
    else:
        return 'Não foi possível conectar ao banco de dados de condições via jcl'
    return f"Gerado arquivo csv com {len(registros) * 1000} registros de prévias com sucesso em " \
           f"{t_gasto / 60: .2f} minutos!"
