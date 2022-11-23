from antecessores import monta_grafo_ant, get_itens_saida_ant,get_itens_entrada_ant
from descendentes import monta_grafo, get_edges, get_itens_entrada, get_graph_table_records_from_list, \
    get_graph_csv_table_records_from_list, get_insert_sql_from_list
from graph_generator import draw_graph
import networkx as nx

from utils import is_character_a2z, jsonify_nodes_edges


# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,ACLD847A

if __name__ == '__main__':
    # sys.setrecursionlimit(10**6)
    edges = []
    no_inicial = input('Digite o no inicial: ').upper()
    grupo = input('Informe o grupo da schedule, em caso de prévias, ou apenas tecle enter ').upper()
    tipo_grafo = input('Tipo do grafo [1 - sucessores, 2 - antecessores] ')

    if tipo_grafo == '1':  # mapa com sucessores
        if grupo and is_character_a2z(grupo[0]) is None:
            grupo = grupo[1:]

        mapa = nx.Graph()
        monta_grafo(no_inicial, grupo, edges, get_itens_entrada(), mapa)
        edges_gerados = get_edges()
        print(f'{jsonify_nodes_edges(get_edges())}')

        if edges_gerados:
            print(f'edges: {edges_gerados}')
            # edges_to_db, nodes_to_db = get_graph_table_records_from_list(edges_gerados)
            # edges_to_db, nodes_to_db = get_insert_sql_from_list(edges_gerados)
            draw_graph(root_node_label=no_inicial, grafo=mapa, node_size=2000, font_size=8,
                       origin_color='olive', others_color='blue', font_color='whitesmoke')
        else:
            print(f'A rotina {no_inicial} não passa condição para outras rotinas')

    else: # mapa com antecessores
        if grupo and is_character_a2z(grupo[0]) is None:
            grupo = grupo[1:]

        mapa = nx.Graph()
        monta_grafo_ant(no_inicial, edges, get_itens_saida_ant(), mapa)  # itens_saida

        # gerar executavel
        edges_gerados = get_edges()
        if edges_gerados:
            print(f'edges: {edges_gerados}')
            # edges_to_db, nodes_to_db = get_graph_table_records_from_list(edges_gerados)
            # edges_to_db, nodes_to_db = get_insert_sql_from_list(edges_gerados)
            draw_graph(root_node_label=no_inicial, grafo=mapa, node_size=2000, font_size=8,
                       origin_color='olive', others_color='blue', font_color='whitesmoke')
        else:
            print(f'A rotina {no_inicial} não passa condição para outras rotinas')