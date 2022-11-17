import os
import sys
import time
from datetime import date
from files import get_item_by_node
from graph_generator import build_edges
from critico import get_treated_schedule_content, get_particionado, build_critical_path
from dbase import getJCL, get_records, conectar
from grafo import Grafo
from graph_class import Graffo
from former.zowe import Pzowe

sys.setrecursionlimit(10 ** 6)


# import hbase

def monta_grafo(no_inicial, edges, itens_saida, mapa, entrada, saida):
    itens_entrada = get_item_by_node(no_inicial, entrada, 0)

    # captura as condições dos nós de entrada
    for v in itens_entrada:
        cond_inicial = v[1]
        itens_saida = get_item_by_node(cond_inicial, saida, 1)
        edges = build_edges(no_inicial, itens_saida)
        mapa.add_edges_from(edges)
        edges = []
    for no_inicial in itens_saida:
        monta_grafo(no_inicial[0], edges, itens_saida, mapa, entrada, saida)


def get_table_data():
    global username, password, dbase, host, user
    username = os.getenv('DB2_USER')
    password = os.getenv('DB2_PWD')
    database = os.getenv('DATABASE')
    hostname = os.getenv('HOSTNAME')
    port = os.getenv('PORT')
    dbase = f'DATABASE={database}'
    host = f'HOSTNAME={hostname}'
    porta = f'PORT={port}'
    user = f'UID={username}'
    passw = f'PWD={password}'
    sql2 = 'select nm_job as previa, nm_mbr_job as jcl ,  dt_mvt as data ' \
           'from BDB2P04.DB2OPP.ABN ' \
           'where dt_mvt  = ? and cd_tip_job = ? and nr_idfc_fase = ? and cd_ctp = ?' \
           ' and NM_BBL_JOB = ? and NM_JOB NOT LIKE  ? and NM_JOB NOT LIKE  ? and NM_JOB NOT LIKE  ?' \
           ' and NM_JOB NOT LIKE  ? and NM_JOB <> NM_MBR_JOB and length(RTRIM(NM_JOB)) > ?' \
           ' order by nm_job'
    data_iso = date.today().strftime("%Y-%m-%d")
    tipo_job = 'JOB'
    fase = '99'
    ambiente = 'BR'
    biblioteca = 'BRCTMP1.JCL.PCP'
    mask1 = 'DB2%'
    mask2 = '*%'
    mask3 = '%%%#%'
    mask4 = '%%%@%'
    size = 7
    params = (data_iso, tipo_job, fase, ambiente, biblioteca, mask1, mask2, mask3, mask4, size)
    connection_string = dbase + ';' + host + ';' + porta + ';' + 'PROTOCOL=TCPIP;' + user + ';' + passw + ';'
    conn = conectar(connection_string)
    if conn is not None:
        previas = get_records(conn, sql2, 500, params)
    print(getJCL(previas, 'DEBD927'))


if __name__ == '__main__':
    pzowe = Pzowe()
    # rodadas de sucesso:
    # ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,
    t_inicio = time.time()
    grafo = Grafo()
    grafo.cond_in = grafo.read_csv('br_in.csv', 'r')
    grafo.cond_in = grafo.prepare_list(grafo.cond_in, [2, 2, 2])
    grafo.cond_out = grafo.read_csv('br_out.csv', 'r')
    grafo.cond_out = grafo.prepare_list(grafo.cond_out, [2])
    target_routine = input('Digite a rotina de BR para construir o mapa: ').upper()
    print(f'Criando mapa da rotina {target_routine}, este processo poderá demorar ...')
    grafo.combinacao_g([target_routine])
    arestas = grafo.list_for_graph
    print(arestas)
    t_fim = time.time()
    print(f'Tempo de execução {t_fim - t_inicio} segundos')
    # grafo como lista de dicionários
    graffo = Graffo(arestas, direcionado=True)
    print('Adjacencias ')
    print(graffo.adj)
    grafo.print_graph(grafo.list_for_graph)
    # chain = Chain()
    # chain.read_cond_type('br_in.csv','in', 'r')
    # chain.read_cond_type('br_out.csv', 'out', 'r')
    # chain.get_chain('SOLD010J')
    # rotinas = chain.routines

    exit(0)
    original_schedule_data = pzowe.getContentsDatasetMember(get_particionado('DNR'))

    if original_schedule_data[0] != 'erro':
        adequate_schedule_data = get_treated_schedule_content(original_schedule_data[1])
    else:
        print('Erro ao recuperar arquivo de condições!')
    # condicionais PCPEAF61   s3 pcpdrcb1
    routine = 'PCPEAF61'
    critical_path = build_critical_path(routine, adequate_schedule_data)
    # built_tree(cadeia)

    # teste recupera condições frc de uma dada rotina e insere '/' entre pai e filho de cada elemento da lsita
    # file_name = get_frc_cond_filename('BRP.PCP.FORCE.D', '.SS000108')
    # file_name =  'BRP.PCP.FORCE.D220830.SS000108'
    # external_conditions = get_raw_frc_conditions(pzowe, file_name)
    # conds_frc = built_tree(external_conditions, 'frc', 'CDCD0143')
    # print(conds_frc)

    # # teste impressão condições da schedule no formato esperado
    # cadeia = [['PCPDRCB1','/','PCPCINB2'],['PCPDRCB1','/','PCPCOUB2','/','PCPCTLB2','/','PCPE001','PCPEOT2']]
    # print_tree(cadeia)

    print()
    # PCPEAF61 condicionais e s3
    # pcpdrcb1 s3 sem condicionais várias
    # pcpeaf5d bbn- sem condicionais
    # pcpdsta3 uma condição  simples sem condicionais
