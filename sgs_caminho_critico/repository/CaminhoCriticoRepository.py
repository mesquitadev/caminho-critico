import csv
import os

import psycopg2
from psycopg2.extras import RealDictCursor
import logging


class CaminhoCriticoRepository:
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

    def connect(self):
        self.connection = psycopg2.connect(
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def fetch_nodes_data(self, node_ids):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            select
            'stopwatch' as icon, '#377' as color, 'wait' as mainstat,
            sa.idfr_sch as id, sa.nm_mbr as title, sa.sub_apl as subtitle, sa.pas_pai as detail__pasta, sa.nm_svdr as detail__amb
            from batch.sch_agdd sa
            where idfr_sch in %s
            """
            cursor.execute(query, (tuple(node_ids),))
            return cursor.fetchall()

    def fetch_edges(self, node_ids):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = ("\n"
                     "            select \n"
                     "            ROW_NUMBER() OVER ()  as id,\n"
                     "            source as source,\n"
                     "            target as target,\n"
                     "            mainstat,\n"
                     "            secondarystat\n"
                     "            from\n"
                     "            (select je.idfr_sch as source, je.idfr_job_exct as target, 'FORCE'"
                     " as  mainstat, '' as secondarystat from batch.job_exct je \n"
                     "            union\n"
                     "            select sccs.idfr_sch as source, scce.idfr_sch as target, 'COND'"
                     " as mainstat, c.nm_cnd as secondarystat from batch.sch_crlc_cnd_said sccs "
                     "inner join batch.sch_crlc_cnd_entd scce on sccs.idfr_cnd = scce.idfr_cnd\n"
                     "            inner join batch.cnd c on sccs.idfr_cnd = c.idfr_cnd \n"
                     "            where sccs.cmdo_cnd = 'A' and scce.dt_cnd <> 'PREV') as res\n"
                     "            where res.source IN %s and res.target IN %s\n"
                     "            ")
            cursor.execute(query, (tuple(node_ids), tuple(node_ids)))
            return cursor.fetchall()

    def fetch_and_save_records_to_csv(self, csv_file_path):
        # Configurar o log
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        # Verificar se o arquivo CSV existe e apagar se necessário
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            logging.info(f'Arquivo {csv_file_path} apagado antes de atualizar.')

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
            select je.idfr_sch, je.idfr_job_exct from batch.job_exct je
            union
            select sccs.idfr_sch, scce.idfr_sch from batch.sch_crlc_cnd_said sccs
            inner join batch.sch_crlc_cnd_entd scce on sccs.idfr_cnd = scce.idfr_cnd
            inner join batch.cnd c on sccs.idfr_cnd = c.idfr_cnd
            where sccs.cmdo_cnd = 'A'
            """
            cursor.execute(query)
            records = cursor.fetchall()

        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['idfr_sch', 'idfr_job_exct']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record)
