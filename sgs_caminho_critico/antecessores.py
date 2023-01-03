from graph_generator import build_edges_predecessors
from utils import remove_list_duplicate


def get_item_by_node_ant(node_label, list_name, i, tipo='+'):
    if i == 1:
        itens = [it for it in list_name if node_label == it[i] and it[3] == tipo]
    else:
        itens = [it for it in list_name if node_label == it[i]]  # and it[3] == tipo
    itens = remove_list_duplicate(itens)
    return itens


def get_input_condition_by_routine(node_label, input_file):
    return get_item_by_node_ant(node_label=node_label, list_name=input_file, i=0)


def get_target_routines_by_cond(condition, output_file):
    return get_item_by_node_ant(node_label=condition, list_name=output_file, i=1)


def monta_grafo_antv2(no_inicial, edges, origem, mapa, entrada, saida, all_edges, edges_count,
                      equal_edges, repeated_conds, empty_edges):  # itens_saida
    destino = get_input_condition_by_routine(no_inicial, entrada)  # itens_entrada  # entrada  # 0
    # captura as condições dos nós de entrada
    for v in destino:  # itens_entrada
        cond_inicial = v[1]  # captura condições para busca no outro arquivo
        origem = get_target_routines_by_cond(cond_inicial, saida)  # itens_saida # saida
        edges = build_edges_predecessors(no_inicial, origem)  # itens_saida
        if edges in all_edges:
            repeated_conds += 1
            # limita em caso de inúmeras prévias evita estouro recursão
            if repeated_conds > 500:
                break
            else:
                continue
        if not edges:
            empty_edges += 1
            continue
        mapa.add_edges_from(edges)
        all_edges.append(edges)
        edges_count += 1
        edges = []
    for no_inicio in origem:  # itens_saida
        if no_inicio[0] == no_inicial:
            equal_edges += 1
            continue
        monta_grafo_antv2(no_inicio[0], edges, origem, mapa, entrada, saida, all_edges,
                          edges_count, equal_edges, repeated_conds, empty_edges)  # itens_saida


def monta_grafo_ant(no_origem, edges, no_destino, mapa, entrada, saida, all_edges, no_origem_anterior):
    if no_origem:
        no_origem = get_item_by_node_ant(no_origem, entrada, 0)  # itens_entrada  # entrada  # 0
    else:
        no_origem = []
    print(edges, no_destino)
    # captura as condições dos nós de entrada
    for v in no_origem:  # itens_entrada
        cond_inicial = v[1]  # captura condições para busca no outro arquivo
        no_destino = get_item_by_node_ant(cond_inicial, saida, 1)  # no_origem # saida
        edges = build_edges_predecessors(no_origem[0][0], no_destino)
        all_edges.append(edges)
        mapa.add_edges_from(edges)
        edges = []
        # draw_graph(root_node_label=no_origem, grafo=mapa, node_size=2000, font_size=8,
        #            origin_color='olive', others_color='blue', font_color='whitesmoke')
        if no_destino and no_destino[0][0] in no_origem[0][0]:
            continue
            # no_origem_anterior.append(no_destino[0])
        # draw_graph(mapa, node_size=2000, font_size=8)
        # for no_origem in itens_entrada:  # itens_proximos:
        # cond_inicial = no_inicio[1]
        # no_origem_anterior.pop(0)
        # no_origem = get_item_by_node_ant(no_inicio[0], saida, 0)
        # for no_org in no_origem:
        #     no_inicio = no_org[0]
        #     if no_inicio and no_inicio[0] == no_origem:
        #         continue
        # no_inicio = no_inicio[0] if no_inicio else None
        # cond_inicial = no_org[1]  # captura condições para busca no outro arquivo
        # no_destino = get_item_by_node(cond_inicial, entrada, 1)  # no_origem # saida
        # edges.append(build_edges(no_inicio, no_destino))  # no_origem
        # mapa.add_edges_from(edges)
        # all_edges.append(edges)
        # edges = []
        # draw_graph(mapa, node_size=2000, font_size=8)

        for no in no_destino:
            monta_grafo_ant(no, edges, no_destino, mapa, entrada, saida, all_edges, no_origem_anterior)
            # monta_grafo_ant(no, edges, no_destino, mapa)  # no_origem

# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,
