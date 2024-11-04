import csv
import os
import logging
from datetime import datetime

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
                je.hr_inc_exea_job AS start_time,
                je.hr_fim_exea_job AS end_time,
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
            dt_atl,
            hr_inc_exea_job,
            hr_fim_exea_job
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
            :dt_atl,
            :hr_inc_exea_job,
            :hr_fim_exea_job
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

    def buscar_fluxos(self):
        query = text("""
            SELECT
                idfr_flx_rtin_bch,
                idfr_sch_inc_flx,
                idfr_sch_fim_flx
            FROM
                batch.CAD_FLX_RTIN_BCH
        """)
        result = self.db.execute(query)
        return result.fetchall()

    def update_obs_job(self, orderid, obs):
        query = text("""
            UPDATE batch.job_exea_ctm
            SET obs_job = :obs
            WHERE idfr_exea = CAST(:orderid AS VARCHAR)
        """)
        self.db.execute(query, {'obs': obs, 'orderid': orderid})
        self.db.commit()

    def update_status_fluxo(self, id_fluxo, idfr_est_flx, start_timestamp, end_timestamp, est_abn_flx, est_excd_flx,
                            est_jobh_flx):
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if the record exists
        check_query = text("""
            SELECT COUNT(*)
            FROM batch.ACPT_EXEA_FLX
            WHERE idfr_flx_rtin_bch = :idfr_flx_rtin_bch
            AND dt_inc_flx = :dt_inc_flx
        """)

        record_exists = self.db.execute(check_query, {
            'idfr_flx_rtin_bch': id_fluxo,
            'dt_inc_flx': current_date
        }).scalar()

        # Update if exists, otherwise insert
        if record_exists:
            update_query = text("""
                UPDATE batch.ACPT_EXEA_FLX
                SET
                    hr_inc_exea_flx = :hr_inc_exea_flx,
                    hr_fim_exea_flx = :hr_fim_exea_flx,
                    idfr_est_flx = :idfr_est_flx,
                    est_abn_flx = :est_abn_flx,
                    est_excd_flx = :est_excd_flx,
                    est_jobh_flx = :est_jobh_flx,
                    est_ati = 'true',
                    ts_ult_atl = :ts_ult_atl
                WHERE
                    idfr_flx_rtin_bch = :idfr_flx_rtin_bch
                    AND dt_inc_flx = :dt_inc_flx
            """)
            self.db.execute(update_query, {
                'idfr_flx_rtin_bch': id_fluxo,
                'dt_inc_flx': current_date,
                'hr_inc_exea_flx': start_timestamp,
                'hr_fim_exea_flx': end_timestamp,
                'idfr_est_flx': idfr_est_flx,
                'est_abn_flx': est_abn_flx,
                'est_excd_flx': est_excd_flx,
                'est_jobh_flx': est_jobh_flx,
                'ts_ult_atl': current_timestamp
            })
        else:
            insert_query = text("""
                INSERT INTO batch.ACPT_EXEA_FLX (
                    idfr_flx_rtin_bch,
                    idfr_exea_flx,
                    idfr_est_flx,
                    est_abn_flx,
                    est_excd_flx,
                    est_jobh_flx,
                    in_atr,
                    dt_inc_flx,
                    hr_inc_exea_flx,
                    hr_fim_exea_flx,
                    est_ati,
                    ts_ult_atl
                ) VALUES (
                    :idfr_flx_rtin_bch,
                    DEFAULT,
                    :idfr_est_flx,
                    :est_abn_flx,
                    :est_excd_flx,
                    :est_jobh_flx,
                    'false',
                    :dt_inc_flx,
                    :hr_inc_exea_flx,
                    :hr_fim_exea_flx,
                    'true',
                    :ts_ult_atl
                )
            """)
            self.db.execute(insert_query, {
                'idfr_flx_rtin_bch': id_fluxo,
                'dt_inc_flx': current_date,
                'idfr_est_flx': idfr_est_flx,
                'est_abn_flx': est_abn_flx,
                'est_excd_flx': est_excd_flx,
                'est_jobh_flx': est_jobh_flx,
                'hr_inc_exea_flx': start_timestamp,
                'hr_fim_exea_flx': end_timestamp,
                'ts_ult_atl': current_timestamp
            })

        self.db.commit()

        select_query = text("""
            SELECT idfr_exea_flx
            FROM batch.ACPT_EXEA_FLX
            WHERE idfr_flx_rtin_bch = :idfr_flx_rtin_bch
            ORDER BY ts_ult_atl DESC
            LIMIT 1
        """)

        result = self.db.execute(select_query, {'idfr_flx_rtin_bch': id_fluxo})
        return result.fetchone()

    def insert_obs_acpt_exea_flx(self, idfr_flx_rtin_bch, idfr_exea_flx, obs_flx):
        # Check if the record exists
        check_query = text("""
            SELECT COUNT(*)
            FROM batch.OBS_ACPT_EXEA_FLX
            WHERE idfr_flx_rtin_bch = :idfr_flx_rtin_bch
            AND idfr_exea_flx = :idfr_exea_flx
        """)

        record_exists = self.db.execute(check_query, {
            'idfr_flx_rtin_bch': idfr_flx_rtin_bch,
            'idfr_exea_flx': idfr_exea_flx
        }).scalar()

        # Update if exists, otherwise insert
        if record_exists:
            update_query = text("""
                UPDATE batch.OBS_ACPT_EXEA_FLX
                SET obs_flx = :obs_flx
                WHERE idfr_flx_rtin_bch = :idfr_flx_rtin_bch
                AND idfr_exea_flx = :idfr_exea_flx
            """)
            self.db.execute(update_query, {
                'idfr_flx_rtin_bch': idfr_flx_rtin_bch,
                'idfr_exea_flx': idfr_exea_flx,
                'obs_flx': obs_flx
            })
        else:
            insert_query = text("""
                INSERT INTO batch.OBS_ACPT_EXEA_FLX (
                    idfr_flx_rtin_bch,
                    idfr_exea_flx,
                    obs_flx
                ) VALUES (
                    :idfr_flx_rtin_bch,
                    :idfr_exea_flx,
                    :obs_flx
                )
            """)
            self.db.execute(insert_query, {
                'idfr_flx_rtin_bch': idfr_flx_rtin_bch,
                'idfr_exea_flx': idfr_exea_flx,
                'obs_flx': obs_flx
            })

        self.db.commit()

    def buscar_status_fluxos(self):
        query = text("""
            SELECT
                idfr_flx_rtin_bch,
                idfr_est_flx
            FROM
                batch.acpt_exea_flx
        """)
        result = self.db.execute(query)
        return [dict(row._mapping) for row in result]

    def buscar_status_fluxo_por_id(self, id_fluxo: str):
        query = text("""
            SELECT
                idfr_flx_rtin_bch,
                idfr_est_flx
            FROM
                batch.acpt_exea_flx
            WHERE
                idfr_flx_rtin_bch = :id_fluxo
        """)
        result = self.db.execute(query, {'id_fluxo': id_fluxo})
        return result.fetchone()
