import matplotlib
import matplotlib.pyplot as plt
import networkx as nx


def get_node_color(grafo, root_node):
    colors = []
    for node in grafo:
        if node == root_node:
            colors.append('green')
        else:
            colors.append('orange')
    return colors


def draw_graph(root_node_label, grafo, node_size, font_size, save=False):
    plt.style.use('ggplot')
    matplotlib.use('tkagg')
    color_map = get_node_color(grafo, root_node_label)
    nx.draw(grafo, with_labels=True, font_weight='normal', node_size=node_size,
            arrows=True, arrowstyle='->', arrowsize=10, width=2, font_size=font_size,
            node_color=color_map, font_color='black')
    plt.show()
    if save:
        plt.savefig("mapa.png")


def remove_duplicate_itens_from_list(itens_saida):
    aux = []
    for it_saida in itens_saida:
        if it_saida not in aux:
            aux.append(it_saida)
    return aux


def get_item_by_node(node_label, list_name, i, tipo='+'):
    if i == 1:
        itens = [it for it in list_name if node_label == it[i]]
    else:
        itens = [it for it in list_name if node_label == it[i] and it[3] == '+']
    itens = remove_duplicate_itens_from_list(itens)
    return itens


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
