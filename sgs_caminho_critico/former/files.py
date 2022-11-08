import csv


def read_csv_file(file_name, delimiter=','):
    in_cond_list = []
    with open(file_name, 'r') as file:
        csvreader = csv.reader(file, delimiter=delimiter)
        for row in csvreader:
            in_cond_list.append(row)
    return in_cond_list


def get_item_by_node(node_label, list_name, i):
    itens = [it for it in list_name if node_label in it[i]]
    return itens
