import csv


def read_csv_file(file_name, delimiter=','):
    in_cond_list = []
    with open(file_name, 'r') as file:
        csvreader = csv.reader(file, delimiter=delimiter)
        for row in csvreader:
            in_cond_list.append(row)
    return in_cond_list

# no inicial procuro na saida e capturo condicao
# procuro condicao na cond entrada  e pego a rotina
