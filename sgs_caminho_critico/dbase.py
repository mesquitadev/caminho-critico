import csv
import json

import db2 as db2
# import ibm-db2
# import ibm_db_dbi as db
from pyparsing import unicode


def conectar(connection_string: str):
    try:
        connection_response = db.connect(connection_string, '', '')
        print(connection_response)
        return connection_response
    except Exception as e:
        print(e)


def list_tables(conn):
    tabelas = []
    if conn is not None:
        for t in conn.tables():
            tabelas.append(t)
    return tabelas


def get_records(conn, sql, quantity=None, params=None):
    # print(sql)
    lista = {}
    if conn:
        cur = conn.cursor()

        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)

        if quantity:
            result = cur.fetchmany(quantity)
        else:
            result = cur.fetchmany()

        if result:
            i = 1
            for registro in result:
                print(f'{i} - ', end="")
                for campo in registro:
                    print(f'{campo} ', end="")
                print()
                lista[registro[0]] = registro[1]
                i += 1
        cur.close()
        conn.close()
        print(lista)
        return lista

def getJCL(lista, search):
    return lista[search]

def set_file_from_dict(file_name, dictionario):
    with open(file_name, 'w') as file:
        file.write(json.dumps(dictionario))  # use `json.loads` to do the reverse

def count_records(conn, sql):
    if conn:
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchmany()
        if result:
            for registro in result:
                qty = registro[0]
                print(f'{qty} registros')
        cur.close()
        conn.close()


def ler_csv(filename: str):
    with open(filename, encoding='ISO-8859-1') as file:
        content = file.readlines()
    header = content[:1]
    rows = content[1:]
    print(header)
    print(rows)
    # lines = pd.read_csv(filename,encoding="utf-8")  # encoding="ISO-8859-1"
    # print(lines.values)


def read_file(file_name):  # dialect=csv.excel, **kwargs
    with open(file_name, 'r') as f: # ,  encoding="utf-8"
        reader = csv.reader(f)
        [row for row in reader if row is not None ]
