import mysql.connector
from mysql.connector import Error

'''
select n.name as origem , m.name as destino
from edges e
left outer join nodes n
on e.source = n.id
left outer join nodes m
on e.target = m.id
'''


def connect(host, database, user, pwd):
    try:
        connection = mysql.connector.connect(host=host,
                                             database=database,
                                             user=user,
                                             password=pwd)
        if connection.is_connected():
            db_info = connection.get_server_info()
            print("Connectado ao MySQL Server versão ", db_info)
    except Error as e:
        print("Error ao conectar ao MySQL", e)
        return None
    finally:
        if connection.is_connected():
            return connection
        else:
            return None
            # cursor.close()
            # connection.close()
            # print("MySQL conexão fechada")


def get_cursor(connection):
    return connection.cursor()
    # cursor.execute("select database();")
    # record = cursor.fetchone()
    # print("Conectado ao banco: ", record)


def close_connection(connection):
    connection.close()


def close_cursor(cursor):
    cursor.close()


def insert_many_records(connection, sql, records_to_insert):
    try:
        # records_to_insert = [(4, 'HP Pavilion Power', 1999, '2019-01-11'),
        #                      (5, 'MSI WS75 9TL-496', 5799, '2019-02-27'),
        #                      (6, 'Microsoft Surface', 2330, '2019-07-23')]
        cursor = connection.cursor
        cursor.executemany(sql, records_to_insert)
        connection.commit()
        return cursor.rowcount
    except mysql.connector.Error as error:
        print(f"Falha ao inserir registros {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão encerrada!")


def get_record(connection, cursor, sql, parm):
    try:
        cursor.execute(f'{sql};')
        return cursor.fetchone() if parm == 1 else cursor.fetchall()
    except mysql.connector.Error as error:
        print(f"Falha ao consultar registros {error}")
    finally:
        if connection.is_connected():
            connection.close()
            print("Conexão encerrada!")


def create_tables(connection, cursor):
    try:
        sql_nodes = """CREATE TABLE nodes (
                       id varchar(12) NOT NULL,
                       name varchar(60) NOT NULL,
                       PRIMARY KEY (id)) """
        cursor.connection.cursor()
        cursor.execute(f'{sql_nodes};')

        sql_edges = """CREATE TABLE edges (
                       id varchar(12) NOT NULL,
                       source varchar(60) NOT NULL,
                       target varchar(60) NOT NULL,
                       PRIMARY KEY (id)) """
        cursor.connection.cursor()
        cursor.execute(f'{sql_edges};')
    except mysql.connector.Error as error:
        print(f"Falha ao criar a tabela no MySQL: {error}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexão encerrada")


def delete_all_records(connection, cursor, sql, parm):
    print(parm)
    try:
        cursor.execute(f'{sql};')
        connection.commit()
    except mysql.connector.Error as error:
        print(f"Falha ao deletar todos os registros {error}")
    finally:
        if connection.is_connected():
            connection.close()
            print("Conexão encerrada!")
