import csv
import json
import re
import os
from os.path import exists
from datetime import date, timedelta, datetime


def csv_to_dict(path, filename, key_):
    filename = f'{path}\\{filename}'
    d = {}
    file = open(filename)
    for i in csv.DictReader(file):
        d[dict(i)[key_]] = dict(i)
    return d


def is_dict_key(dic, key):
    return True if key in dic.keys() else False


def get_no_duplicates_list(lista):
    return sorted(set(lista))


def remove_trailing_spaces(string: str, direction: str):
    if direction == 'r':
        return string.rstrip(" ")
    elif direction == 'l':
        return string.lstrip(" ")
    else:
        return string.lstrip(" ").rstrip(" ")


def create_condex_file_from_list(lista_, nome_, path_):
    with open(f'{path_}\\{nome_}', "w") as cdex:
        end_line = lista_[-1]
        for content in lista_:
            content = f'{content}\n' if content != end_line else content
            cdex.writelines(content)
    cdex.close()


def is_path_file_exists(path_plus_file):
    return os.path.isfile(path_plus_file)


def combine_condin_condex_files(input_files, output_file, path_):
    input_files = [f'{path_}\\{arq}' for arq in input_files]
    output_file = f'{path_}\\{output_file}'

    if not is_path_file_exists(input_files[0]) or not is_path_file_exists(input_files[1]):
        raise FileExistsError

    if os.path.isfile(output_file):
        os.remove(output_file)
    # if os.path.isfile(output_file):
    #     os.remove(output_file)
    fout = open(output_file, "a+")
    num_linha = 1
    for input_file in input_files:
        with open(input_file, "r") as fin:
            for line in fin:
                if line != '':  # evita linha em branco
                    if num_linha == 1:
                        fout.write(line[:-1])  # evita \n na primeira linha
                    else:
                        if line[-1] == '\n':
                            fout.write('\n' + line[:-1])
                        else:
                            fout.write('\n' + line[:])  # evita cortar o último caracter da última linha
                    num_linha += 1
    fin.close()
    fout.close()
    if is_path_file_exists(input_files[1]):
        os.remove(input_files[1])


def create_condex_lists(path: str, csv_source: str, previas_jcl: str,
                        delimiter: str):
    file_name = f'{path}\\{csv_source}'
    if not is_file_exists(path, previas_jcl) or not is_file_exists(path, csv_source):
        raise FileNotFoundError

    in_ = []
    out_ = []

    prev_jcl_base = csv_to_dict(path=path, filename=previas_jcl, key_="previa")

    # montagem das condições externas no padrão das internas
    with open(file_name, 'r', encoding="utf-8") as file:
        csvreader = csv.reader(file, delimiter=delimiter)
        for row in csvreader:
            # elimina jobs arroba
            line1 = remove_trailing_spaces(row[0], 'x')
            if line1.find('@') != -1:
                continue
            line2 = remove_trailing_spaces(row[1], 'x')
            if line2.find('@') != -1:
                continue

            if is_dict_key(prev_jcl_base, line1):  # troca jobname por jcl
                line1 = prev_jcl_base[line1]['jcl'].upper()

            # monta lista de condições externas
            in_.append(f'{line2},FRC_{line1}-FRC_{line2},ODAT,,,GRUPO')
            out_.append(f'{line1},FRC_{line1}-FRC_{line2},ODAT,+,GRUPO')

    # remove duplicados na lista de condicoes externas
    in_ = get_no_duplicates_list(in_)
    out_ = get_no_duplicates_list(out_)
    return in_, out_


# testa se a data do mapa já expirou
def is_date_limit_out_of_bounds(limit_days, file_date_str):
    new_final_date = date.today() + timedelta(days=2)
    file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
    return (new_final_date - file_date).days > limit_days


# gera json de configuração de tempo limite dos mapas por rotina e tipo
def create_json_from_csv(path, file_name):
    csv_config = f'{path}{file_name}.csv'
    json_config = f'{path}{file_name}.json'
    json_array = [*csv.DictReader(open(csv_config, encoding='utf-8'))]
    with open(json_config, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(json_array, indent=4))
    jsonf.close()


# retorna json a partir do cfg json
def get_json_file_contents(path, file_name):
    f = open(f'{path}{file_name}.json')
    data = json.load(f)
    f.close()
    return data


def remove_files_by_pattern(dir_path, pattern, file_new):
    list_of_files_with_error = []
    for parent_dir, dir_names, filenames in os.walk(dir_path):
        for filename in filenames:
            if pattern.findall(filename) and filename != file_new:
                # se arquivo expirou prossegue, senão continue
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


def make_file_names(json_file_names):
    file_names = []
    for file in json_file_names:
        file_names.append(get_file_name(file.mapa.value, file.tipo.value, file.plex.value, file.grupo.value))
    return file_names


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


def is_file_exists(path, json_graph_filename):
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
        if elm and len(elm[0][0]) > 1 and len(elm[0][1]) > 1:
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
                # print(f'generated_edges has an element not equal {item}')
                for it in item:
                    generated_edges_no_duplicates.append([it])
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
    generated_edges = remove_duplicates_from_list(remove_duplicate_edges(generated_edges, lista=True))  # remove extra)
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
    # print(f'json puro {result}')
    return result


def remove_duplicates_from_list(dup_list: list):
    no_dup_list = []
    for elm in dup_list:
        if elm not in no_dup_list:
            no_dup_list.append(elm)
    return no_dup_list


def remove_single_letter_from_list(dup_list: list):
    no_dup_list = []
    for elm in dup_list:
        if elm not in no_dup_list and len(elm.title) > 1:
            no_dup_list.append(elm)
    return no_dup_list


def jsonify_parent_son(generated_edges):
    dicio_nodes = []
    generated_edges = remove_duplicates_from_list(remove_duplicate_edges(generated_edges, lista=True))
    for elm in generated_edges:
        nodes = {'parent': elm[0][0], 'son': elm[0][1]}
        dicio_nodes.append(nodes)
    result = {"mapa": dicio_nodes}
    return result
