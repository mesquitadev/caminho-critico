from gera_descendentes import monta_grafo, get_edges, get_itens_entrada
from graf_drawing import draw_graph
import networkx as nx


# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,ACLD847A

if __name__ == '__main__':
    # sys.setrecursionlimit(10**6)
    edges = []
    no_inicial = input('Digite o no inicial: ').upper()
    mapa = nx.Graph()
    monta_grafo(no_inicial, edges, get_itens_entrada(), mapa)  # itens_saida

    # gerar executavel
    print(f'edges: {get_edges()}')
    draw_graph(no_inicial, mapa, node_size=2000, font_size=8)
