from __future__ import generators

import os
from datetime import datetime, date

import ibm_db_dbi as db
import mysql.connector
from mysql.connector import Error

from sgs_caminho_critico.utils import get_date_minus_added_time


class DbConnect:

    def __init__(self, ambiente):
        self.location = {'BR': 'BDB2P04',
                         'B2': 'BDB2P04',
                         'B3': 'BDB2P04',
                         'HM': 'BDB2H01'}
        self.hosts = {'BR': ['gwdb2.bb.com.br', '50100'],
                      'B2': ['gwdb2.bb.com.br', '50100'],
                      'B3': ['gwdb2.bb.com.br', '50100'],
                      'HM': ['bdb2h01.plexhom.bb.com.br', '446']}
        self.amb = ambiente
        self.database = self.location[self.amb]
        self.hostname = self.hosts[self.amb][0]
        self.port = self.hosts[self.amb][1]
        self.lib = {'BR': 'BRCTMP1.JCL.PCP',
                    'B2': 'B2CTMP1.JCL.PCP',
                    'B3': 'B3CTMP1.JCL.PCP',
                    'HM': 'HMCTMP1.JCL.PCP'}
        self.ctm_user = {'DS': {'user': 'DST', 'amb': 'DSA'},
                         'HM': {'user': 'BRH', 'amb': 'HOM'},
                         'BR': {'user': 'BRP', 'amb': 'BSB'},
                         'B2': {'user': 'B2P', 'amb': 'BS2'},
                         'B3': {'user': 'B3P', 'amb': 'BS3'}}

    def connect_db2(self):
        try:
            connection_string = self.get_connection_string()
            connection_response = db.connect(connection_string, '', '')
            return connection_response
        except Exception as e:
            print(e)
            return e

    @staticmethod
    def connect_mysql(host, database, user, pwd):
        connection = None
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

    @staticmethod
    def get_cursor(connection):
        return connection.cursor()
        # cursor.execute("select database();")
        # record = cursor.fetchone()
        # print("Conectado ao banco: ", record)

    @staticmethod
    def close_connection(connection):
        connection.close()

    @staticmethod
    def close_cursor(cursor_):
        cursor_.close()

    @staticmethod
    def insert_many_records(connection, sql, records_to_insert):
        cursor = None
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

    @staticmethod
    def get_records(conn, sql, quantity=None, params=None):
        records = []
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
                    records.append(registro)
                    # records[registro[0].lstrip().rstrip()] = registro[1].lstrip().rstrip()
                    i += 1
            cur.close()
            conn.close()
            return records

    @staticmethod
    def get_db_curs(conn, sql):
        if conn:
            cur = conn.cursor()
            cur.execute(sql)
            return cur

    @staticmethod
    def get_dif_datas_from_previa(registro):
        data_abend = registro[2].strftime("%Y%m%d")
        data_hoje = datetime.today().strftime("%Y%m%d")
        return (datetime.strptime(data_hoje, "%Y%m%d") - datetime.strptime(data_abend, "%Y%m%d")).days

    @staticmethod
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

    def get_prepared_previas_sql(self):
        # biblioteca = f"'{self.lib[self.amb]}'"  , cd_ctp
        ateh = datetime.now().strftime('%Y-%m-%d')
        de = get_date_minus_added_time(date.today(), 'Y', 1)
        sql = f"select distinct nm_job as previa, nm_mbr_job as jcl  " \
              f"from {self.location[self.amb]}.DB2OPP.ABN " \
              f"where cd_tip_job = 'JOB' " \
              f"and date(ts_abn) between '{de}' and '{ateh}' " \
              f"order by nm_job"
        # f"and NM_BBL_JOB = {biblioteca} " \
        # and cd_ctp = '{self.amb}' " \
        return sql

    def get_prepared_conditions_sql(self):
        ambiente = self.amb.upper()
        sql = f"""
                select
                           distinct
                              a.nm_rtin_rsp_opr as previa,
                              b.nm_mbr_job as jcl,
                              a.nm_cnd as condicao

                FROM
                    DB2IIT.OPR_RLZD_CND  as a,
                    BDB2P04.DB2OPP.ABN as b
                where
                a.cd_usu_rsp_opr = '{self.ctm_user[ambiente]['user']}'
                and a.nm_amb_prct = '{self.ctm_user[ambiente]['amb']}'
                and b.cd_ctp = '{ambiente}'  -- varia com plex
                and b.NM_BBL_JOB = '{ambiente}CTMP1.JCL.PCP' -- varia com plex
                and b.nm_mbr_job    <> 'CTMEDEL'
                and b.cd_tip_job = 'JOB'
                and b.nr_idfc_fase = '99'
                and b.nm_job = a.nm_rtin_rsp_opr
                and a.nm_cnd not like'%###%'
                and date(a.dt_atl) between '{get_date_minus_added_time(data=date.today(), time_type='Y', added_value=1)}'
                and '{date.today()}'
                AND A.CD_TIP_OPR = 'A'  -- adição de condições
            """
        return sql

    def get_connection_string(self):
        return f'DATABASE={self.database};' \
               f'HOSTNAME={self.hostname};' \
               f'PORT={self.port};' \
               f'UID={os.getenv("DB2_USER")};' \
               f'PWD={os.getenv("DB2_PWD")};'

    @staticmethod
    def result_iterator(cursor, arraysize=1000):
        """
            utiliza fetchmany e consome menos memória
        """
        result_set = []
        while True:
            results = cursor.fetchmany(arraysize)
            if not results:
                break
            result_set.append(results)
        return result_set

    def get_curs_records(self, curs):
        registros = []
        for result in self.result_iterator(curs):
            registros.append(result)
        return registros
