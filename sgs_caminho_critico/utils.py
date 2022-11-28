import csv
import json
import re


def is_char_a2z(character):
    # test char and return None if false
    pattern = re.compile("[A-Za-z]+")
    return pattern.fullmatch(character)


def read_csv_file(file_name, delimiter=','):
    return_list = []
    with open(file_name, 'r') as file:
        csvreader = csv.reader(file, delimiter=delimiter)
        for row in csvreader:
            return_list.append(row)
    return return_list


def get_node_index_from_dicio(dicio, nodes, elm):
    return list(filter((elm).__ne__,
                       [int(dicio[i]['id']) if nodes['title'] == dicio[i]['title'] else -1 for i in range(len(dicio))]))


def remove_list_duplicate(list_with_duplicates):
    list_no_duplicates = []
    for item in list_with_duplicates:
        if item not in list_no_duplicates:
            list_no_duplicates.append(item)
    return list_no_duplicates


def is_all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)


def remove_value_if_different(the_list, val):
    return [value for value in the_list if value != val]


def save_graph_to_file(graph_json, routine, graph_code, plex, group):
    graph_type = 'direct' if graph_code == '1' else 'reverse'
    json_graph_filename = f'{routine}_{graph_type}_{plex}_{group}'
    json_object = json.dumps(graph_json)
    with open(json_graph_filename, "w") as jsonfile:
        jsonfile.write(json_object)


def remove_duplicate_tuples(duplicated_list):
    if duplicated_list and is_all_equal(duplicated_list):
        return [duplicated_list[0]]
    else:
        return [duplicated_list]


def remove_duplicate_edges(generated_edges, list=False):
    generated_edges_no_duplicates = []
    for item in generated_edges:
        if len(item) > 1:
            if is_all_equal(item):
                if list:
                    generated_edges_no_duplicates.append([item[0]])
                else:
                    generated_edges_no_duplicates.append(item[0])
            else:
                print(f'generated_edges has an element not equal {item}')
                for it in item:
                    generated_edges_no_duplicates.append(it)
        else:
            generated_edges_no_duplicates.append(item)
    return generated_edges_no_duplicates


def insert_nodes(id_origem, id_value, empty_value, zero_value, value_passed, value_failed):
    return {"id": str(id_origem), "title": id_value, "subTitle": empty_value, "mainStat": id_value,
            "secondaryStat": zero_value, "arc__failed": value_failed, "arc__passed": value_passed}


def insert_edges(id_edge, id_origem, id_destino, empty_value="", zero_value=0):
    return {"id": str(id_edge), "source": str(id_origem), "target": str(id_destino), "mainStat": zero_value}


def generate_valid_json(test_case):
    results = []
    for x in test_case:
        result_details = {"\"case_id\"": "\"" + str(x) + "\"", "\"status_id\"": 1, "\"version\"": "\"1.0\"",
                          "\"comment\"": "\"Test\""}
        results.append(result_details)
    return json.dumps(results)


def jsonify_nodes_edges(generated_edges):
    dicio_nodes = []
    dicio_edges = []
    i = 1
    id_edge = 0
    generated_edges = remove_duplicate_edges(generated_edges, list=True)
    for elm in generated_edges:
        id_origem = i
        value_passed = 1.0
        value_failed = 0.0

        if id_origem == 1:
            value_passed = 0.0
            value_failed = 1.0

        nodes = insert_nodes(id_origem=id_origem, id_value=elm[0][0], empty_value="", zero_value="0",
                             value_passed=value_passed,
                             value_failed=value_failed)

        if dicio_nodes:
            pos_node_in_dicio_nodes = get_node_index_from_dicio(dicio=dicio_nodes, nodes=nodes, elm=-1)
            if not pos_node_in_dicio_nodes:
                dicio_nodes.append(nodes)
            else:
                id_origem = pos_node_in_dicio_nodes[0]
                i -= 1
        else:
            dicio_nodes.append(nodes)

        i += 1
        id_destino = i
        nodes = insert_nodes(id_origem=id_destino, id_value=elm[0][1], empty_value="", zero_value=0,
                             value_passed=value_passed,
                             value_failed=value_failed)  # id_origem
        i += 1
        if dicio_nodes:
            pos_node_in_dicio_nodes = get_node_index_from_dicio(dicio=dicio_nodes, nodes=nodes, elm=-1)
            if not pos_node_in_dicio_nodes:  # [0] == -1:
                dicio_nodes.append(nodes)
            else:
                id_destino = pos_node_in_dicio_nodes[0]
        else:
            dicio_nodes.append(nodes)

        edges = insert_edges(id_edge=id_edge, id_origem=id_origem, id_destino=id_destino, empty_value="", zero_value=0)
        dicio_edges.append(edges)
        id_edge += 1
    result = {"edges": dicio_edges,
              "nodes": dicio_nodes
              }
    print(f'json puro {result}')
    return result
