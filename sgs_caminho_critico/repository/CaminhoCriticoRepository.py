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
                SELECT
                    'stopwatch' AS icon, 
                    '#377' AS color,
                    COALESCE(tej.nm_est_job, 'não schedulado') AS mainstat,
                    sa.idfr_sch AS id, 
                    sa.nm_mbr AS member_name,
                    sa.sub_apl AS sub_appl, 
                    sa.pas_pai AS pasta, 
                    sa.nm_svdr AS ambiente,
                    je.idfr_exea AS orderid,  
                    je.nr_exea AS run_number,
                    je.dt_mvt AS odate
                FROM batch.sch_agdd sa
                LEFT JOIN batch.job_exea_ctm je ON sa.idfr_sch = je.idfr_sch
                LEFT JOIN batch.tip_est_job tej ON je.idfr_est_job = tej.idfr_est_job
                WHERE sa.idfr_sch IN %s
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

    # Método para buscar dados da tabela SCH_AGDD
    def fetch_sch_agdd_data(self):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
        SELECT idfr_sch, nm_SVDR, pas_PAI, nm_MBR, sub_apl
        FROM batch.sch_agdd
        """
            cursor.execute(query)
            records = cursor.fetchall()

            # Remove leading and trailing spaces from each field in each record
            cleaned_records = [
                {key: value.strip() if isinstance(value, str) else value for key, value in record.items()}
                for record in records
            ]

            return cleaned_records

    # Método para inserir dados na tabela JOB_EXEA_CTM
    def insert_job_exea_ctm_data(self, job_exea_ctm_data):
        with self.connection.cursor() as cursor:
            query = ("\n"
                     "            INSERT INTO batch.job_exea_ctm (idfr_sch, idfr_exea, dt_mvt, obs_job, \n"
                     "            nr_exea, flx_atu, est_jobh, est_excd, idfr_est_job, dt_atl)\n"
                     "            VALUES (%(idfr_sch)s, %(idfr_exea)s, %(dt_mvt)s, %(obs_job)s, \n"
                     "            %(nr_exea)s, %(flx_atu)s, %(est_jobh)s, %(est_excd)s, %(idfr_est_job)s, %(dt_atl)s)\n"
                     "            ")
            cursor.executemany(query, job_exea_ctm_data)
            self.connection.commit()

    def fetch_existing_job_exea_ctm_data(self, idfr_sch_list):
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
        SELECT idfr_sch, idfr_exea, nr_exea, idfr_est_job
        FROM batch.job_exea_ctm
        WHERE idfr_sch IN %s
        """
            cursor.execute(query, (tuple(idfr_sch_list),))
            return cursor.fetchall()

    def delete_job_exea_ctm_data(self, idfr_sch_list):
        with self.connection.cursor() as cursor:
            query = """
        DELETE FROM batch.job_exea_ctm
        WHERE idfr_sch IN %s
        """
            cursor.execute(query, (tuple(idfr_sch_list),))
            self.connection.commit()
