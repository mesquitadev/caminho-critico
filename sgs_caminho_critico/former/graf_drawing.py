import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
from Graph import Grafo

nodes = ['BICD020', 'ANCD010', 'CTMD015',
         'ANCD010', 'TRFD010',
         'CAVD005', 'APDD012', 'AGED960',
         'BICD015']
edg = [('BICD020', 'ANCD010'), ('BICD020', 'CTMD015'),
       ('ANCD010', 'TRFD010'), ('ANCD010', 'CTMD015'),
       ('BICD020', 'CAVD005'), ('CTMD015', 'CTMD015'),
       ('APDD012', 'AGED960'), ('AGED960', 'TRFD010'),
       ('TRFD010', 'CAVD005'), ('BICD015', 'BICD020'),
       ('CTMD015', 'BICD015'), ('ANCD010', 'BICD020'),
       ('TRFD010', 'ANCD010')]


def draw_graph(grafo, node_size, font_size, save=False):
    plt.style.use('ggplot')
    matplotlib.use('tkagg')
    nx.draw(grafo, with_labels=True, font_weight='normal', node_size=node_size,
            arrows=True, arrowstyle='->', arrowsize=10, width=2, font_size=font_size)
    plt.show()
    if save:
        plt.savefig("mapa.png")


def do_it():
    g = Grafo(edg, True)
    mapa = nx.Graph()
    mapa.add_edges_from(edg)
    print(g.get_arestas())
    print(g)
    print(mapa)
    draw_graph(mapa, node_size=4000, font_size=9)


def build_edges(no_origem, lista):
    edges = []
    for elm in lista:
        edges.append((no_origem, elm[0]))
    return edges
