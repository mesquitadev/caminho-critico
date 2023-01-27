import json
import os
from enum import Enum
import requests
import urllib3
import asyncio


class Status(Enum):
    ENDED_NOT_OK = 'Ended%20not%20OK'
    ENDED_OK = 'Ended%20OK'
    WAIT_USER = 'Wait%20User'
    WAIT_RESOURCE = 'Wait%20Resource'
    WAIT_HOST = 'Wait%20Host'
    WAIT_WORKLOAD = 'Wait%20Workload'
    WAIT_CONDITION = 'Wait%20Condition'
    STATUS_UNKNOWN = 'Wait%20Condition'
    EXECUTING = 'Executing'
    WAITING_INFO = 'Waiting%20Info'


def get_data_report(name, fmt_rel, filter_name, filter_value):
    return {"name": f"{name}", "format": f"{fmt_rel}",
            "filters": [{"name": f"{filter_name}",
                         "value": f"{filter_value}"}]}


class Ctm:

    def __init__(self, ambiente):
        self.ambiente = ambiente
        self.ctm = f'CTM_{self.ambiente}' if self.ambiente not in ('BR', 'B2', 'B3') else 'CTM_PROD'
        self.end_point = os.getenv(self.ctm)
        self.token = None
        self.plex = os.getenv(f'PLX{self.ambiente}') if self.ambiente != 'DS' \
            else 'PLXDES'

    def logon(self):
        # faz o logon
        method_ws = "session/login"
        headers = {'Content-Type': 'application/json'}
        data = {
            "password": os.getenv('CTM_PWD'),
            "username": os.getenv('CTM_USER')
        }
        urllib3.disable_warnings()
        resp = requests.post(url=f'{self.end_point}{method_ws}',
                             headers=headers, data=json.dumps(data), verify=False)
        self.token = resp.json()['token']

    def logoff(self):
        # faz o logoff
        method_exit = "session/logout"
        username = os.getenv('CTM_USER')
        body = json.loads('{ "token": "' + self.token + '", "username": "' + username + '"}')
        r_fim = requests.post(url=self.end_point + method_exit, data=body, verify=False)
        return r_fim

    def get_plex_order_id(self, order_id):
        return f'{self.plex}:{order_id}'

    def busca_recursos(self, nome_do_recurso):
        searchquery = f'ctm={self.plex}&name={nome_do_recurso}'
        r = requests.get(self.end_point + 'run/resources?' + searchquery,
                         headers={'Authorization': 'Bearer ' + self.token},
                         verify=False)
        return json.loads(r.text)

    def busca_eventos(self, nome_do_evento, data, limite):
        searchquery = f'ctm={self.plex}&name={nome_do_evento}&date={data}&limit={limite}'
        r = requests.get(f'{self.end_point}run/resources?{searchquery}',
                         headers={'Authorization': 'Bearer ' + self.token},
                         verify=False)
        return r.text

    def estado_dos_jobs(self, tabela, status, em_hold, limite):
        searchquery = f'ctm={self.plex}&folder={tabela}&status={status}&held={em_hold}&limit={limite}'
        r = requests.get(f'{self.end_point}/run/jobs/status?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text.splitlines()

    def url_estado_jobs(self, retorno):  # verificar
        header = {"Authorization": "Bearer " + self.token}
        saida = retorno
        url = ""
        for a in saida:
            if 'logURI' in a:
                # url = saida[23].split('"')[3][0:len(saida[23].split('"')[3])]
                url = a[16:-1]
                break
        r = requests.get(url=url, headers=header, verify=False)
        return r.text

    # def rerun_job(job_id, token, retorno, endpoint):  # verificar
    #     header = {"Authorization": "Bearer " + token}
    #     api_endpoint = get_endpoint(ambiente, ctm)
    #     url_parte = f'/run/job/{job_id}/rerun'
    #     r = requests.post(api_endpoint + url_parte, headers={"Authorization": "Bearer " + token}, verify=False)
    #     print(r)
    #     saida = retorno.splitlines()
    #     for a in saida:
    #         if 'logURI' in a:
    #             url = saida[23].split('"')[3][0:len(saida[23].split('"')[3])]
    #             break
    #     url = ""
    #     print(url)
    #     r = requests.get(url=url, headers=header, verify=False)
    #     return r.text

    def estado_dos_jobs_com_subapplication(self, subpp, status, em_hold, limite):
        searchquery = f'ctm={self.plex}&subApplication={subpp}&status={status}&held={em_hold}&limit={limite}'
        r = requests.get(f'{self.end_point}/run/jobs/status?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return json.loads(r.text)['statuses']

    def estado_dos_jobs_com_resource_semaphore(self, tabela, status, em_hold, limite, recurso):
        searchquery = f'ctm={self.plex}&folder={tabela}&status={status}&held={em_hold}&limit={limite}' \
                      f'&resourceSemaphore={recurso}'
        r = requests.get(f'{self.end_point}/run/jobs/status?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    def estado_dos_jobs_com_resource_mutex(self, tabela, status, em_hold, limite, recurso):
        searchquery = f'ctm={self.plex}&folder={tabela}&status={status}&held={em_hold}' \
                      f'&limit={limite}&resourceMutex={recurso}'
        r = requests.get(f'{self.end_point}/run/jobs/status?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    def estado_dos_jobs_com_intervalo(self, tabela, status, em_hold, hr_inicio, hr_fim, limite):
        searchquery = f'ctm={self.plex}&folder={tabela}&status={status}&held={em_hold}' \
                      f'&limit={limite}&fromTime={hr_inicio}&toTime={hr_fim}'
        r = requests.get(f'{self.end_point}/run/jobs/status?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    # verficar estado do job
    def estado_do_job(self, jobid):
        r = requests.get(f'{self.end_point}/run/job/{jobid}/status',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    # verificar se há dados interessantes aqui
    def dados_do_job(self, jobid):
        r = requests.get(f'{self.end_point}/run/job/{jobid}/get',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    # verificar se é condição de entrada
    def condicoes_aguardadas(self, jobid):  # ok
        r = requests.get(f'{self.end_point}/run/job/{jobid}/waitingInfo',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.json()

    # verificar se é condição de saída
    def output_do_job(self, jobid):  # incluso header
        header = {"Authorization": "Bearer " + self.token}
        r = requests.get(f'{self.end_point}/run/job/{jobid}/output?token={self.token}',
                         headers=header, verify=False)
        return r.text

    def job_log(self, jobid):  # incluso header
        header = {"Authorization": "Bearer " + self.token}
        r = requests.get(f'{self.end_point}/run/job/{jobid}/log?token={self.token}',
                         headers=header, verify=False)
        return r.text

    # verificar se trago job pelo nome da condição
    def pega_nome_da_condicao(self, nome, data, limite):
        # data no formato MMDD ou STAT
        searchquery = f'ctm={self.plex}&name={nome}&date={data}&limit={limite}'
        r = requests.get(f'{self.end_point}/run/events?{searchquery}',
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    def pega_definicoes_de_tabelas(self, formato, tabela):  # funciona apenas com XML
        searchquery = f'format={formato}&folder={tabela}&ctm={self.plex}'
        r = requests.get(self.end_point + '/deploy/jobs?' + searchquery,
                         headers={"Authorization": "Bearer " + self.token},
                         verify=False)
        return r.text

    def inclui_condicao(self, data, condicao):
        method_include = f'run/event/{self.plex}'
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.token}
        body = json.loads('{ "date": "' + data + '", "name": "' + condicao + '"}')
        r = requests.post(f'url={self.end_point}{method_include}',
                          headers=headers, data=json.dumps(body), verify=False)
        return r.text

    def deleta_condicao(self, nome, data):
        method_delete = f'/run/event/{self.plex}/{nome}/{data}'
        r = requests.delete(f'{self.end_point}{method_delete}',
                            headers={"Authorization": "Bearer " + self.token}, verify=False)
        return r.text

    def roda_relatorio(self, data_report):
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.token}
        method_include = "reporting/report"
        url = f'{self.end_point}{method_include}'
        r = requests.post(url=url, headers=headers, json=data_report, verify=False)
        return r.json()

    @staticmethod
    def get_endpoint(ambiente, ctm):
        return ctm[ambiente].upper()

    async def status_relatorio(self, report_id):
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer ' + self.token}
        method_include = f"reporting/status/{report_id}"
        url = f'{self.end_point}{method_include}'
        await asyncio.sleep(7)
        r = requests.get(url=url, headers=headers, verify=False)
        if r.ok:
            return json.loads(r.content)
        else:
            return r.json()
