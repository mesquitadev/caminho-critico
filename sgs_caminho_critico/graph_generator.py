import matplotlib
import matplotlib.pyplot as plt
import networkx as nx


def get_node_color(grafo, root_node, origin_color, others_color):
    colors = []
    for node in grafo:
        if node == root_node:
            colors.append(origin_color)  # green
        else:
            colors.append(others_color)  # orange
    return colors


def draw_graph(root_node_label, grafo, node_size, font_size, origin_color, others_color, font_color='black', save=False,
               seed=3113794652):
    plt.style.use('ggplot')
    matplotlib.use('tkagg')
    pos = nx.spring_layout(grafo, seed=seed)
    color_map = get_node_color(grafo, root_node_label, origin_color, others_color)
    nx.draw(G=grafo, pos=pos, with_labels=True, font_weight='normal', node_size=node_size,
            arrows=True, arrowstyle='->', arrowsize=10, width=2, font_size=font_size,
            node_color=color_map, font_color=font_color)
    plt.show()
    if save:
        plt.savefig("mapa.png")


# def remove_duplicate_itens_from_list(itens_saida):
#     aux = []
#     for it_saida in itens_saida:
#         if it_saida not in aux:
#             aux.append(it_saida)
#     return aux


#
# def do_it():
#     g = Grafo(edg, True)
#     mapa = nx.Graph()
#     mapa.add_edges_from(edg)
#     print(g.get_arestas())
#     print(g)
#     print(mapa)
#     draw_graph(mapa, node_size=4000, font_size=9)


def build_edges(no_origem, lista):
    edges = []
    # next_origin = []
    for elm in lista:
        edges.append((no_origem, elm[0]))
        # edges.append((no_origem, elm[0] if elm[3] == '' else elm[0] + '&' if elm[3] == 'And' else '|'))
        # if elm[0] not in next_origin:
        #     next_origin.append(elm[0])
    return edges  # , next_origin
