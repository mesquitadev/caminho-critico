from utils import read_csv_file, remove_duplicates_from_list, is_character_a2z
from graph_generator import build_edges

all_edges = []
itens_entrada = []
itens_saida = []
no_origem_anterior = []
entrada = read_csv_file('br_in.csv', ',')
saida = read_csv_file('br_out.csv', ',')


def get_item_by_node(node_label, list_name, i, tipo='+'):
    if i == 1:
        itens = [it for it in list_name if node_label == it[i]]
    else:
        itens = [it for it in list_name if node_label == it[i] and it[3] == '+']
    itens = remove_duplicates_from_list(itens)
    return itens


def monta_grafo(no_inicial, grupo, edges, no_destino, mapa):
    new_origin = []
    if no_inicial:
        no_origem = get_item_by_node(no_inicial, saida, 0)
    else:
        no_origem = []

    if no_origem and grupo:
        for no in no_origem:
            group_node = no[4] if is_character_a2z(no[4]) is not None else no[4][1:]
            no[4] = group_node
            if grupo == group_node:
                new_origin.append(no)
        no_origem = new_origin

    # captura as condições dos nós de entrada
    for v in no_origem:
        cond_inicial = v[1]  # captura condições para busca no outro arquivo
        no_destino = get_item_by_node(cond_inicial, entrada, 1)
        edges = build_edges(no_inicial, no_destino)
        if edges and edges not in all_edges:
            mapa.add_edges_from(edges)
            all_edges.append(edges)
            if no_destino and no_destino[0] not in no_origem_anterior:
                no_origem_anterior.append(no_destino[0])
        else:
            continue
        # edges = []
        # if no_destino and no_destino[0] not in no_origem_anterior:
        #     no_origem_anterior.append(no_destino[0])
    # draw_graph(mapa, node_size=2000, font_size=8)
    for no_inicio in no_origem_anterior:
        # cond_inicial = no_inicio[1]
        no_origem_anterior.pop(0)
        no_origem = get_item_by_node(no_inicio[0], saida, 0)
        for no_org in no_origem:
            no_inicio = no_org[0]
            if no_inicio and no_inicio == no_inicial:
                continue
            # no_inicio = no_inicio[0] if no_inicio else None
            cond_inicial = no_org[1]  # captura condições para busca no outro arquivo
            no_destino = get_item_by_node(cond_inicial, entrada, 1)
            edges = build_edges(no_inicio, no_destino)
            if edges and edges[0] not in all_edges:
                mapa.add_edges_from(edges)
                all_edges.append(edges)
            else:
                continue
            # edges = []
        # draw_graph(mapa, node_size=2000, font_size=8)

        no_inicial = no_destino[0][0] if no_destino else []
        monta_grafo(no_inicial, grupo, edges, no_destino, mapa)


def get_edges():
    return all_edges


def get_itens_entrada():
    return itens_entrada


def get_itens_saida():
    return itens_saida

def get_graph_csv_table_records_from_list(lista):
    csv_list_edges = []
    csv_nodes = []
    for par in lista:
        elm = f'({par[0][0]},f"{par[0][0]}-{par[0][1]}",{par[0][1]})'
        if elm not in csv_list_edges:
            edge_line = f'{par[0][0]}-{par[0][1]}'
            csv_list_edges.append((par[0][0],edge_line,par[0][1]))
        if par[0][0] not in csv_nodes:
            csv_nodes.append(par[0][0])
        if par[0][1] not in csv_nodes:
            csv_nodes.append(par[0][1])
    return csv_list_edges, csv_nodes


def get_graph_table_records_from_list(lista):
    list_edges = []
    nodes = []
    for par in lista:
        elm = (par[0][0],f'{par[0][0]}-{par[0][1]}',par[0][1])
        if elm not in list_edges: # (par[0][0],f'{par[0][0]}-{par[0][1]}',par[0][1])
            list_edges.append(elm)
        elm = (par[0][0],par[0][0])
        if elm not in nodes:
            nodes.append(elm)
        elm = (par[0][1], par[0][1])
        if elm not in nodes:
            nodes.append(elm)
    return list_edges, nodes

def get_insert_sql_from_list(lista):
    csv_list_edges = []
    csv_nodes = []
    nodes_insert = []
    for par in lista:
        if par[0][0] not in csv_nodes:
            csv_nodes.append(par[0][0])
        if par[0][1] not in csv_nodes:
            csv_nodes.append(par[0][1])
    for item in csv_nodes:
        nodes_insert.append(f'insert into nodes (name) values ("{item}");')
    for par in lista:
        elm = f'("{par[0][0]}",f"{par[0][0]}-{par[0][1]}","{par[0][1]}")'
        if elm not in csv_list_edges:
            edge_line = f'{par[0][0]}-{par[0][1]}'
            csv_list_edges.append(
                f'insert into edges (id, source, target) values ("{par[0][0]}","{edge_line}","{par[0][1]}");')

    return csv_list_edges, nodes_insert

