from descendentes import get_item_by_node
from utils import read_csv_file, remove_duplicates_from_list
from graph_generator import build_edges, draw_graph
import networkx as nx
import sys

itens_entrada = []
itens_saida = []
no_origem = []
entrada = read_csv_file('br_in.csv', ',')
saida = read_csv_file('br_out.csv', ',')



def get_itens_saida_ant():
    return itens_saida

def get_itens_entrada_ant():
    return itens_entrada

def get_item_by_node_ant(node_label, list_name, i, tipo='+'):
    if i == 1:
        itens = [it for it in list_name if node_label == it[i] and it[3] == tipo]
    else:
        itens = [it for it in list_name if node_label == it[i] ] # and it[3] == tipo
    itens = remove_duplicates_from_list(itens)
    return itens


def monta_grafo_ant(no_origem, edges, no_destino, mapa):  # no_origem
    if no_origem:
        no_origem = get_item_by_node_ant(no_origem,entrada, 0)  # itens_entrada  # entrada  # 0
    else:
        no_origem = []
    # captura as condições dos nós de entrada
    for v in no_origem:  # itens_entrada
        cond_inicial = v[1]  # captura condições para busca no outro arquivo
        no_destino = get_item_by_node_ant(cond_inicial, saida, 1)  # no_origem # saida
        edges=build_edges(no_origem[0][0], no_destino)
        mapa.add_edges_from(edges)
        edges = []
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
        monta_grafo_ant(no, edges, no_destino, mapa)  # no_origem


# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,

# if __name__ == '__main__':
#
#     mapa = nx.Graph()
#     monta_grafo_ant(no_inicial, edges, itens_saida, mapa)  # itens_saida
#
#     # gerar executavel
#     # python .\setup.py build
#     print(f'edges: {all_edges}')
#     draw_graph(mapa, node_size=2000, font_size=8)
