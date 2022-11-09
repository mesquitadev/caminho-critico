from gera_descendentes import monta_grafo, get_edges, get_itens_entrada
from graf_drawing import draw_graph
import networkx as nx

from utils import is_character_a2z

# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,ACLD847A

if __name__ == '__main__':
    # sys.setrecursionlimit(10**6)
    edges = []
    no_inicial = input('Digite o no inicial: ').upper()
    grupo = input('Informe o grupo da schedule, em caso de prévias, ou apenas tecle enter ').upper()

    if grupo and is_character_a2z(grupo[0]) is None:
        grupo = grupo[1:]

    mapa = nx.Graph()
    monta_grafo(no_inicial, grupo, edges, get_itens_entrada(), mapa)

    # gerar executavel
    edges_gerados = get_edges()
    if edges_gerados:
        print(f'edges: {edges_gerados}')
        draw_graph(no_inicial, mapa, node_size=2000, font_size=8, origin_color='green', others_color='violet', font_color='white')
    else:
        print(f'A rotina {no_inicial} não passa condição para outras rotinas')
