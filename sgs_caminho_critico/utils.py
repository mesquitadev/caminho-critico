import csv
import json
import os
import re
from datetime import date, timedelta, datetime
from os.path import exists

import requests
from dateutil.relativedelta import relativedelta


def format_condjcl_list(lista_: list[str]) -> list[str]:
    """
        recebe lista original da leitura do dataset de condições via jcl
        formata para poder inserir nos dados gerais de condição de saída
    """
    lista = []
    for elm in lista_:
        if elm == "":
            continue
        parts = elm.split(";")
        line = f'{parts[0].rstrip()},S3-{parts[0].rstrip()}-{parts[1].rstrip().lstrip()},ODAT,+,GRUPO'
        lista.append(line)
    return lista


def list2string(lista, sep):
    return sep.join(lista)


def get_diff_between_dates(date1: date, date2: date):
    """
        retorna diferença entre duas datas ex.: date(2016,12,30)
    """
    delta = date2 - date1
    return delta.days


def get_date_plus_added_time(data: date, time_type: str, added_value: int) -> date:
    """
        retorna data mais quantidade de meses ou anos cfe M ou Y
        params
        date data como em date(ano, mes, dia)
        time_type: como em M ou Y
        added_value: quantidade numérica
    """
    returned_data: date = date(1, 1, 1)
    # data = date.split('-')
    # data_date = date(data.year,data.month,data.day)
    if time_type == 'M':
        returned_data = date(data.year, data.month, data.day) + relativedelta(months=added_value)
    elif time_type == 'Y':
        returned_data = date(data.year, data.month, data.day) + relativedelta(years=added_value)
    return returned_data


def get_date_minus_added_time(data: date, time_type: str, added_value: int) -> date:
    """
        retorna data mais quantidade de meses ou anos cfe M ou Y
        params
        date data como em date(ano, mes, dia)
        time_type: como em M ou Y
        added_value: quantidade numérica
    """
    returned_data: date = date(1, 1, 1)
    if time_type == 'M':
        returned_data = date(data.year, data.month, data.day) - relativedelta(months=added_value)
    elif time_type == 'Y':
        returned_data = date(data.year, data.month, data.day) - relativedelta(years=added_value)
    return returned_data


def get_current_date_type(date_type: str):
    months = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    if date_type == 'D':
        return str(datetime.now().strftime('%d'))
    elif date_type == 'M':
        return months[int(datetime.now().strftime('%m')) - 1]
    elif date_type == 'DT':
        return f"{str(datetime.now().strftime('%Y'))}-" \
               f"{str(datetime.now().strftime('%m'))}-" \
               f"{str(datetime.now().strftime('%d'))}"
    else:
        return str(datetime.now().strftime('%y'))


def list2csv(path, filename, lista_, mode='a+'):
    with open(f'{path}{filename}', mode) as f:
        end_line = lista_[-1]
        for content in lista_:
            content = f'{content}\n' if content != end_line else content
            f.writelines(content)


def complex_list2csv(path, filename, lista_, func, begin, end, mode='a+'):
    with open(f'{path}\\{filename}', mode) as f:
        end_line = lista_[-1]
        for content in lista_:
            treated_content = func(content, begin, end)
            treated_content = f'{treated_content}' if treated_content != end_line else treated_content
            f.writelines(treated_content)


def get_added_cond_via_jcl_line(list_: list, begin: int, end: int) -> str:
    retorno = ""
    for item in list_:
        it = list(item[begin:end + 1])
        it[0] = remove_trailing_spaces(it[0], 'r')
        it[1] = remove_trailing_spaces(it[1], 'r')
        retorno += f"{','.join(it)},ODAT,+,GRUPO\n"
    return retorno


def get_condjcl_file_name(hlq: str, cnd_part_file: str) -> str:
    cnd_file = f'{hlq}.{cnd_part_file[1:-1]}'
    mes = get_current_date_type('M')
    ano = get_current_date_type('Y')
    time_def = f'{mes}{ano}'
    cnd_file_list = cnd_file.split('.')
    cnd_file_list[4] = time_def
    return list2string(cnd_file_list, '.')


def cria_csv_cond_jcl(path, filename, lista, mode):
    """
        Cria arquivo de condições via jcl
    """
    lst = format_condjcl_list(lista)
    list2csv(path, filename, lst, mode)


def csv2dict(path, filename, key_):
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


def cria_csv_frc_jcl(lista_, nome_, path_, mode="w"):
    list2csv(path_, nome_, lista_, mode)


def is_path_file_exists(path_plus_file):
    return os.path.isfile(path_plus_file)


def build_added_conds_by_jcl_file(conds_list: list):
    # here
    pass


def combina_csvs_condicoes_ctm_e_force_jcl(input_files, output_file, path_, file_nb=1):
    input_files = [f'{path_}{arq}' for arq in input_files]
    output_file = f'{path_}{output_file}'

    if not is_path_file_exists(input_files[0]) or not is_path_file_exists(input_files[1]):
        raise FileExistsError

    if os.path.isfile(output_file):
        os.remove(output_file)
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
    if is_path_file_exists(input_files[file_nb]):
        os.remove(input_files[file_nb])


def cria_lista_frc_jcl(path: str, csv_source: str, previas_jcl: str,
                       delimiter: str = ";"):
    # file_name = f'{path}{csv_source}'
    if not is_file_exists(path, previas_jcl):  # or not is_file_exists(path, csv_source):
        raise FileNotFoundError

    in_ = []
    out_ = []

    prev_jcl_base = csv2dict(path=path, filename=previas_jcl, key_="previa")

    # montagem das condições externas no padrão das internas
    # with open(file_name, 'r', encoding="utf-8") as file:
    #     csvreader = csv.reader(file, delimiter=delimiter)
    for elm in csv_source:
        if elm == '':  # elimina último registro em branco do arquivo
            continue
        row = elm.split(delimiter)
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
    csv_config = f'{path}\\{file_name}.csv'
    json_config = f'{path}\\{file_name}.json'
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


def insert_edges(id_edge, id_origem, id_destino, zero_value=0):  # retirado empty_value=""
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

        edges = insert_edges(id_edge=id_edge, id_origem=id_origem, id_destino=id_destino, zero_value=0)
        dicio_edges.append(edges)
        id_edge += 1
    result = {"edges": dicio_edges,
              "nodes": dicio_nodes
              }
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


def is_text_in_line(line, text):
    return text in line


def find_content_in_list(lista: list, valor: str) -> int:
    # procura string em uma lista de elementos e retorna o elemento onde ela existe ou -1 caso contrário
    try:
        posicao = [(lista.index(x)) for x in lista if valor in x]
        if len(posicao) > 0:
            return posicao[0]
        else:
            return -1
    except IndexError:
        return -1


def find_content_in_list_interval(lista: list, valor: str, begin: int, end: int):
    # procura string em um intervalo de lista retorna o índice ou -1 caso contrário
    if begin == -1 or end == -1:
        return -1
    posicao = [i for i in range(begin, end + 1, 1) if valor in lista[i] and '//*' not in lista[i]]
    return -1 if not posicao else sorted(posicao)[0]


def find_content_in_list_of_dict(lista: list, key1, key2: str, valor: str) -> int:
    # procura string em uma lista de dicionarios e retorna se o elemento existe ou -1 caso contrário
    try:
        list_content = lista[key1] if key1 != '' else lista
        for elm in list_content:
            if valor == elm[key2] if key2 != '' else elm:
                return 1
    except IndexError:
        return -1
    return -1


def is_substring_on_string(linha: str, substring: str) -> bool:
    if substring in linha:
        return True
    else:
        return False


def position_of_substring_on_string(linha: str, substring: str) -> int:
    try:
        position = linha.find(substring)
        return position
    except IndexError:
        return -1


def download_file_by_url(url, file_name):
    response = requests.get(url, allow_redirects=True)
    with open(file_name, "wb") as file:
        file.write(response.content)
    return f'Relatório {file_name} gerado com sucesso'


def build_file_from_dict(file_name, dictionario):
    with open(file_name, 'w') as file:
        file.write(json.dumps(dictionario))  # use `json.loads` to do the reverse


def ler_csv(filename: str, encode: str):
    # 'ISO-8859-1'
    with open(filename, encoding=encode) as file:
        content = file.readlines()
    header = content[:1]
    rows = content[1:]
    print(header)
    print(rows)


def read_file(file_name):  # dialect=csv.excel, **kwargs
    with open(file_name, 'r') as f:  # ,  encoding="utf-8"
        reader = csv.reader(f)
    return [row for row in reader if row is not None]
