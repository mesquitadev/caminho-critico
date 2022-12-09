import csv
import json
import re
import os
from os.path import exists
from datetime import date, timedelta, datetime


# testa se a data do mapa já expirou
def is_date_limit_out_of_bounds(limit_days, file_date_str):
    new_final_date = date.today() + timedelta(days=2)
    file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
    return (new_final_date - file_date).days > limit_days


# gera json de configuração de tempo limite dos mapas por rotina e tipo
def write_cfg_json(path):
    csv_config = path + 'config_files.csv'
    json_config = path + 'config_files.json'
    json_array = [*csv.DictReader(open(csv_config, encoding='utf-8'))]
    with open(json_config, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(json_array, indent=4))
    jsonf.close()


# retorna json a partir do cfg json
def get_cfg_json_contents_list(json_name):
    f = open(json_name)
    data = json.load(f)
    f.close()
    return data


def remove_files_by_matching_pattern(dir_path, pattern):
    list_of_files_with_error = []
    for parent_dir, dir_names, filenames in os.walk(dir_path):
        for filename in filenames:
            if pattern.findall(filename):
                try:
                    os.remove(os.path.join(parent_dir, filename))
                except OSError:
                    print("Error while deleting file : ", os.path.join(parent_dir, filename))
                    list_of_files_with_error.append(os.path.join(parent_dir, filename))
    return list_of_files_with_error


# def remove_file_pattern(file_pattern):
#     file_list = glob.glob(file_pattern)
#     for file_path in file_list:
#         try:
#             os.remove(file_path)
#         except OSError:
#             print(f"Erro ao excluir arquivo {file_path}")


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
    return list(filter(elm.__ne__,
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


def get_file_name(routine, graph_type, plex, group):
    group = group if group is not None else 'ng'
    data = date.today()
    return f'{routine.lower()}_{plex}_{graph_type}_{group}_{data}.json'


def save_graph_to_file(graph_json, path, json_graph_filename):
    json_object = json.dumps(graph_json)
    result = False
    try:
        with open(f'{path}{json_graph_filename}', "w") as jsonfile:
            jsonfile.write(json_object)
        result = True
    except IOError as e:
        print(f'Erro ao salvar o arquivo json {json_graph_filename}: {e}')
    finally:
        return result


def exists_json_file(path, json_graph_filename):
    return exists(f'{path}{json_graph_filename}')


def get_json_file(routine, graph_type, plex, group=None):
    data = date.today()
    path = os.getenv('CSV_FILES')
    return exists(f'{path}{routine.lower()}_{graph_type}_{plex}_{group}_{data}.json')


def get_json_content(path, json_file_name):
    # try:
    with open(f'{path}{json_file_name}', 'r') as openfile:
        return json.load(openfile)
    # except IOError as e:
    #     print(f'json file not found {e}')


def remove_duplicate_tuples(duplicated_list):
    if duplicated_list and is_all_equal(duplicated_list):
        return [duplicated_list[0]]
    else:
        return [duplicated_list]


def remove_empty_elements(dicio):
    list_ = []
    for elm in dicio:
        if elm:
            list_.append(elm)
    return list_


def remove_duplicate_edges(generated_edges, lista=False):
    generated_edges_no_duplicates = []
    for item in generated_edges:
        if len(item) > 1:
            if is_all_equal(item):
                if lista:
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
    print(empty_value)
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
    generated_edges = remove_duplicate_edges(generated_edges, lista=True)
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
