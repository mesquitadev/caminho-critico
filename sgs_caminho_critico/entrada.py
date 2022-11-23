from utils import read_csv_file
from graph_generator import build_edges, draw_graph, get_item_by_node
import networkx as nx


def monta_grafo(no_inicial, edges, itens_entrada, mapa): # itens_saida
    itens_saida = get_item_by_node(no_inicial, saida, 0)  # itens_entrada  # entrada  # 0
    # captura as condições dos nós de entrada
    for v in itens_saida:  # itens_entrada
        cond_inicial = v[1]  # captura condições para busca no outro arquivo
        itens_entrada = get_item_by_node(cond_inicial, entrada, 1) # itens_saida # saida
        edges = build_edges(no_inicial, itens_entrada) # itens_saida
        mapa.add_edges_from(edges)
        all_edges.append(edges)
        edges = []
    for no_inicio in itens_entrada:# itens_saida
        if no_inicio[0] == no_inicial: # so está indo até certa profundidade, verificar isso talvez aqui em itens_entrada esteja o erro vide logica com itens_saida
            continue
        monta_grafo(no_inicio[0], edges, itens_entrada, mapa) # itens_saida


# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,

if __name__ == '__main__':
    # sys.setrecursionlimit(10**6)
    all_edges = []
    itens_entrada = []
    itens_saida = []
    edges = []
    entrada = read_csv_file('br_in.csv', ',')
    saida = read_csv_file('br_out.csv', ',')
    no_inicial = input('Digite o no inicial: ').upper()
    mapa = nx.Graph()
    monta_grafo(no_inicial, edges, itens_entrada, mapa) # itens_saida

    # gerar executavel
    # python .\setup.py build
    print(f'edges: {all_edges}')
    draw_graph(mapa, node_size=2000, font_size=8)