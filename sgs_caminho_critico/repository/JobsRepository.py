import csv
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sgs_caminho_critico.config.Database import SessionLocal


class JobsRepository:
    def __init__(self):
        self.db: Session = SessionLocal()

    def fetch_nodes_data(self, node_ids):
        query = text("""
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
                je.est_jobh AS held,
                je.est_excd AS deleted,
                COALESCE(TO_CHAR(je.dt_mvt, 'YYYY-MM-DD'), '') AS odate
            FROM batch.sch_agdd sa
            LEFT JOIN batch.job_exea_ctm je ON sa.idfr_sch = je.idfr_sch
            LEFT JOIN batch.tip_est_job tej ON je.idfr_est_job = tej.idfr_est_job
            WHERE sa.idfr_sch IN :node_ids
        """)
        result = self.db.execute(query, {'node_ids': tuple(node_ids)})
        return [dict(row._mapping) for row in result]

    def fetch_edges(self, node_ids):
        query = text("""
            SELECT
                ROW_NUMBER() OVER () AS id,
                source,
                target,
                mainstat,
                secondarystat
            FROM (
                SELECT
                    je.idfr_sch AS source,
                    je.idfr_job_exct AS target,
                    'FORCE' AS mainstat,
                    '' AS secondarystat
                FROM batch.job_exct je
                UNION
                SELECT
                    sccs.idfr_sch AS source,
                    scce.idfr_sch AS target,
                    'COND' AS mainstat,
                    c.nm_cnd AS secondarystat
                FROM batch.sch_crlc_cnd_said sccs
                INNER JOIN batch.sch_crlc_cnd_entd scce ON sccs.idfr_cnd = scce.idfr_cnd
                INNER JOIN batch.cnd c ON sccs.idfr_cnd = c.idfr_cnd
                WHERE sccs.cmdo_cnd = 'A' AND scce.dt_cnd <> 'PREV'
            ) AS res
            WHERE EXISTS (
                SELECT 1
                FROM batch.sch_agdd sa
                WHERE sa.idfr_sch = res.source
                AND sa.idfr_sch IN :node_ids
            )
            AND EXISTS (
                SELECT 1
                FROM batch.sch_agdd sa
                WHERE sa.idfr_sch = res.target
                AND sa.idfr_sch IN :node_ids
            )
        """)
        result = self.db.execute(query, {'node_ids': tuple(node_ids)})
        return [dict(row._mapping) for row in result]

    def fetch_and_save_records_to_csv(self, csv_file_path):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
            logging.info(f'Arquivo {csv_file_path} apagado antes de atualizar.')

        query = text("""
            SELECT
                je.idfr_sch,
                je.idfr_job_exct
            FROM
                batch.job_exct je
            UNION ALL
            SELECT
                sccs.idfr_sch,
                scce.idfr_sch
            FROM
                batch.sch_crlc_cnd_said sccs
            INNER JOIN
                batch.sch_crlc_cnd_entd scce
                ON sccs.idfr_cnd = scce.idfr_cnd
            INNER JOIN batch.cnd c
                ON sccs.idfr_cnd = c.idfr_cnd
            WHERE sccs.cmdo_cnd = 'A'
        """)
        result = self.db.execute(query)
        records = result.fetchall()

        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['idfr_sch', 'idfr_job_exct']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                writer.writerow(record._mapping)

    def fetch_sch_agdd_data(self):
        query = text("""
            SELECT idfr_sch, nm_SVDR, pas_PAI, nm_MBR, sub_apl
            FROM batch.sch_agdd
        """)
        result = self.db.execute(query)
        records = result.fetchall()

        cleaned_records = [
            {key: value.strip() if isinstance(value, str) else value for key, value in record._mapping.items()}
            for record in records
        ]

        return cleaned_records

    def insert_job_exea_ctm_data(self, job_exea_ctm_data):
        query = text("""
        INSERT INTO batch.job_exea_ctm (
            idfr_sch,
            idfr_exea,
            dt_mvt,
            obs_job,
            nr_exea,
            flx_atu,
            est_jobh,
            est_excd,
            idfr_est_job,
            dt_atl
        ) VALUES (
            :idfr_sch,
            :idfr_exea,
            :dt_mvt,
            :obs_job,
            :nr_exea,
            :flx_atu,
            :est_jobh,
            :est_excd,
            :idfr_est_job,
            :dt_atl
        )
        """)
        self.db.execute(query, job_exea_ctm_data)
        self.db.commit()

    def fetch_existing_job_exea_ctm_data(self, idfr_sch_list):
        if not idfr_sch_list:
            return []
        query = text("""
            SELECT
                idfr_sch,
                idfr_exea,
                nr_exea,
                idfr_est_job
            FROM
                batch.job_exea_ctm
            WHERE
                idfr_sch IN :idfr_sch_list
        """)
        result = self.db.execute(query, {'idfr_sch_list': tuple(idfr_sch_list)})
        return result.fetchall()

    def delete_job_exea_ctm_data(self, idfr_sch_list):
        query = text("""
            DELETE FROM
                batch.job_exea_ctm
            WHERE
                idfr_sch IN :idfr_sch_list
        """)
        self.db.execute(query, {'idfr_sch_list': tuple(idfr_sch_list)})
        self.db.commit()
