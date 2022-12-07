import networkx as nx

from antecessores import monta_grafo_ant
from descendentes import monta_grafo
from graph_generator import draw_graph
from utils import is_char_a2z, jsonify_nodes_edges, read_csv_file

# rodadas de sucesso:
# ACLD137,ACLD200,ACLDH07,ACLD250,ACLD775,DTII010,ACLD847A

if __name__ == '__main__':
    edges = []
    all_edges = []
    no_origem_anterior = []
    itens_entrada = []
    no_destino = ""
    no_inicial = input('Digite o no inicial: ').upper()
    grupo = input('Informe o grupo da schedule, em caso de prévias, ou apenas tecle enter ').upper()
    tipo_grafo = input('Tipo do grafo [1 - sucessores, 2 - antecessores] ')
    ambiente = input('Digite o plex: [br, b2, b3, hm] ').lower()
    entrada = read_csv_file('br_in.csv', ',')
    saida = read_csv_file('br_out.csv', ',')

    if grupo and is_char_a2z(grupo[0]) is None:
        grupo = grupo[1:]

    if tipo_grafo == '1':  # mapa com sucessores
        mapa = nx.Graph()
        monta_grafo(no_inicial, grupo, edges, itens_entrada, mapa, entrada, saida, all_edges, no_origem_anterior)
        edges_gerados = all_edges  # get_edges()
        print(f'{jsonify_nodes_edges(all_edges)}')  # get_edges()

        if edges_gerados:
            print(f'edges: {edges_gerados}')
            # edges_to_db, nodes_to_db = get_graph_table_records_from_list(edges_gerados)
            # edges_to_db, nodes_to_db = get_insert_sql_from_list(edges_gerados)
            draw_graph(root_node_label=no_inicial, grafo=mapa, node_size=2000, font_size=8,
                       origin_color='olive', others_color='blue', font_color='whitesmoke')
        else:
            print(f'A rotina {no_inicial} não passa condição para outras rotinas')

    else:  # mapa com antecessores
        if grupo and is_char_a2z(grupo[0]) is None:
            grupo = grupo[1:]

        mapa = nx.Graph()
        monta_grafo_ant(no_inicial, edges, no_destino, mapa, entrada, saida, all_edges, no_origem_anterior)

        # gerar executavel
        edges_gerados = all_edges  # get_edges()
        if edges_gerados:
            print(f'edges: {edges_gerados}')
            draw_graph(root_node_label=no_inicial, grafo=mapa, node_size=2000, font_size=8,
                       origin_color='olive', others_color='blue', font_color='whitesmoke')
        else:
            print(f'A rotina {no_inicial} não passa condição para outras rotinas')
