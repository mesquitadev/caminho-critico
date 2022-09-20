import csv

import networkx as netx
import matplotlib.pyplot as plot


class Grafo():

    def __init__(self):
        # transformar as duas listas abaixo numa lista de pares [(destino,origem), ...]
        self.cond_in = []
        self.cond_out = []
        self.rotinas = []
        self.condicoes = []
        self.grafo = []
        self.grafo_conds = []
        self.list_for_graph = []

    def prepare_list(self, list_of_lists, cols_to_remove):
        # list_of_lists = [elem for elem in list_of_lists if elem[3] != '-']
        for elm in list_of_lists:
            for col in cols_to_remove:
                del (elm[col])
        return list_of_lists

    def read_csv(self, file_name, mode='r'):
        # stru file condin
        # Member Name,Condition Name,Condition Date,And\Or,Parentheses
        # stru file condout
        # Member Name,Condition Name,Condition Date,Sign(+/-)
        content = []
        with open(file_name, mode) as csvfile:
            csvreader = csv.reader(csvfile)
            for conteudo in csvreader:
                if conteudo[3] != '-':
                    content.append(conteudo)
        return content

    def print_graph(self, list):
        graph = netx.DiGraph()
        graph.add_edges_from(list)

        pos = netx.spring_layout(graph)
        """ This will implement a graph based on force directed algorithm (best way to showcase a graph like this with minimal
         crossings and overall good looking) if you don't care much about the graph label positions"""

        netx.draw_networkx_edges(graph, pos, edgelist=graph.edges(), edge_color="blue", node_size=6, arrowsize=10,
                                 min_source_margin=12, min_target_margin=12)
        netx.draw_networkx_labels(graph, pos, font_size=10, font_color="black")
        plot.show()

    def condin_g(self, rotina: list) -> list:
        for rot in rotina:
            # if self.grafo and rot in self.grafo:
            #     continue
            # procura pela rotina nas condições de entrada
            origem_fonte_in = self.get_routine_from_list_of_lists(self.cond_in, rot)
            # procura rotinas correspondentes às condições, nas condições de saída
            if origem_fonte_in:
                rotinas_destino = self.get_routines_by_conditions(self.cond_out, origem_fonte_in)
                # monta a lista [(destino,origem)...]
                self.make_graph(rotinas_destino, origem_fonte_in)
            else:
                rotina = list(filter(rot.__ne__, rotina))  # remover o vértice sumidouro
                rotinas_destino = []
                list_for_graph_size = len(self.list_for_graph) - 1
                for elm in rotina:
                    for i in range(list_for_graph_size, 0, -1):
                        if elm not in rotinas_destino and elm == self.list_for_graph[i][1]:
                            rotinas_destino.append(self.list_for_graph[i][0])
                    # else:
                    #     break

                    # x = self.list_for_graph
        return rotinas_destino
        # if origem_fonte_in:
        #     for item in self.fonte_in:
        #         if item[0] == rot:
        #             self.condicoes.append(item[1])
        #             self.fonte_in = list(filter(item.__ne__, self.fonte_in))
        #             self.grafo.append(self.rotinas[-1])  # rot
        #             self.grafo_conds.append(self.condicoes[-1])
        #     return True
        # else:
        #     return origem_fonte_in

    def search_value_in_list_of_lists(self, lista, valor):
        return [(lista.index(x), x.index(valor)) for x in lista if valor in x[1]]

    def get_value_from_list_of_lists(self, lista, valor):
        return [x for x in lista if valor in x[1]]

    def get_routine_from_list_of_lists(self, lista, valor):
        return [x for x in lista if valor in x[0]]

    def get_routines_by_conditions(self, lista, conds):
        return [x[0] for cond in conds for x in lista if cond[1] == x[1]]

    def make_graph(self, destino, origem):
        if origem:
            origem = origem[0][0]
        else:
            return
        for x in destino:
            self.list_for_graph.append((x, origem))

    def condout_g(self, condin: list) -> list:
        for cond in condin:
            for item in self.cond_out:
                if item[1] in self.grafo_conds:
                    continue
                destino = self.get_value_from_list_of_lists(self.cond_out, cond)  # item[1]
                if destino:
                    for item_found in destino:
                        self.rotinas.append(item_found[0])
                        self.cond_out = list(filter(item_found.__ne__, self.cond_out))

                break

    def combinacao_g(self, rot):
        rot = self.condin_g(rot)
        if not rot:
            return

        self.combinacao_g(rot)
