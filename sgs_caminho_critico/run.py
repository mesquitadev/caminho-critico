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

from sgs_caminho_critico.controller.CaminhoCriticoController import caminhos_router

app = FastAPI()

app.include_router(caminhos_router, prefix="/api/caminhos", tags=["Graph"])
