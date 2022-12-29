"""
Programa: class pzowe
Autor: Paulo Roberto de Rezende
Gerência: DITEC/GPROM/DIV6/EQ64
Objetivo: classe com chamadas a métodos do Zowe
Data final: 05/04/2022
"""
import json
import os
from json.decoder import JSONDecodeError

import requests
import urllib3
from requests import Response
from requests.exceptions import ConnectTimeout, Timeout
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from urllib3.exceptions import NewConnectionError


class Pzowe:
    def __init__(self):
        self.mask = None
        self.user = ''
        self.pwd = ''
        self.svr = ''  # onde está baseado o Zowe com que se deseja trabalhar
        self.cookie = ''  # autenticação
        self.endpoint = ""
        self.particionados = {'HM': {'JCL': {'PCP': 'HMCTMP1.JCL.PCP',
                                             'IMPLA': 'HMCTMP1.JCL.IMPLA',
                                             'TESTE': 'HMCTMP1.JCL.TESTE',
                                             'INATIVO': 'HMCTMP1.JCL.INATIVO',
                                             'TMP': 'HMA.PCP.JCLX37'},
                                     'PROC': 'HMP.STDPRI.PROCLIB'},
                              'DS': {'JCL': {'PCP': 'DSS.CTMD01B.JCL'},
                                     'PROC': 'DSP.STDPRI.PROCLIB'},
                              'BR': {'JCL': {'PCP': 'BRCTMP1.JCL.PCP',
                                             'IMPLA': 'BRCTMP1.JCL.IMPLA',
                                             'TESTE': 'BRCTMP1.JCL.TESTE',
                                             'INATIVO': 'BRCTMP1.JCL.INATIVO',
                                             'TMP': 'BRA.PCP.JCLX37'},
                                     'PROC': 'BRP.STDPRI.PROCLIB'},
                              'B2': {'JCL': {'PCP': 'B2CTMP1.JCL.PCP',
                                             'IMPLA': 'B2CTMP1.JCL.IMPLA',
                                             'TESTE': 'B2CTMP1.JCL.TESTE',
                                             'INATIVO': 'B2CTMP1.JCL.INATIVO',
                                             'TMP': 'B2A.PCP.JCLX37'},
                                     'PROC': 'B2P.STDPRI.PROCLIB'},
                              'B3': {'JCL': {'PCP': 'B3CTMP1.JCL.PCP',
                                             'IMPLA': 'B3CTMP1.JCL.IMPLA',
                                             'TESTE': 'B3CTMP1.JCL.TESTE',
                                             'INATIVO': 'B3CTMP1.JCL.INATIVO',
                                             'TMP': 'B3A.PCP.JCLX37'},
                                     'PROC': 'B3P.STDPRI.PROCLIB'}
                              }
        self.locais_arquivos = {'HM': {'JCL': 'HMA.PCP.JCLX37',
                                       'REL': 'HMA.PCP.RELCLX37',
                                       'BKP': 'HMA.PCP.BKPX37',
                                       'HST': 'HMA.PCP.HSTX37',
                                       'X37': 'HMH.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'DS': {'JCL': 'DSA.PCP.JCLX37',
                                       'REL': 'DSA.PCP.RELCLX37',
                                       'BKP': 'DSA.PCP.BKPX37',
                                       'HST': 'DSA.PCP.HSTX37',
                                       'X37': 'DSH.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'BR': {'JCL': 'BRA.PCP.JCLX37',
                                       'REL': 'BRA.PCP.RELX37',
                                       'BKP': 'BRA.PCP.BKPX37',
                                       'HST': 'BRA.PCP.HSTX37',
                                       'X37': 'BRP.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'B2': {'JCL': 'B2A.PCP.JCLX37',
                                       'REL': 'B2A.PCP.RELX37',
                                       'BKP': 'B2A.PCP.BKPX37',
                                       'HST': 'B2A.PCP.HSTX37',
                                       'X37': 'B2P.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'B3': {'JCL': 'B3A.PCP.JCLX37',
                                       'REL': 'B3A.PCP.RELX37',
                                       'BKP': 'B3A.PCP.BKPX37',
                                       'HST': 'B3A.PCP.HSTX37',
                                       'X37': 'B3P.PCP.ALL.CLOUDX37.ABENDS.SS000119'}
                                }
        self.msg_logon = ""
        # des 172.17.209.161
        # lb 172.17.208.5
        self.servidores = {
            'HM': '172.17.211.150:7554',
            'LB': 'https://zowelab.bb.com.br:7554',
            'BR': '10.8.36.26:7554',
            'B2': '10.8.36.41:7554',
            'B3': '10.8.36.67:7554',
            'DS': 'https://zowedes.bb.com.br:7554'}
        self.ret = {200: 'OK 	The requested action was successful.',
                    201: ' 	Created 	A new resource was created.',
                    202: '	Accepted 	The request was received, but no modification has been made yet.',
                    204: '	No Content 	The request was successful, but the response has no content.',
                    400: '	Bad Request 	The request was malformed.',
                    401: '	Unauthorized 	The client is not authorized to perform the requested action.',
                    404: '	Not Found 	The requested resource was not found.',
                    415: '	Unsupported Media Type 	The request data format is not supported by the server.',
                    422: 'Unprocessable Entity 	The request data was properly formatted but contained invalid or '
                         'missing data.',
                    500: '	Internal Server Error 	The server threw an error when processing the request.'
                    }
        self.hlq = {'HM': ['HMP', 'HMH', 'HMO', 'HMT'],
                    'DS': ['DSP', 'DSH', 'DSO', 'DST'],
                    'LB': ['LBP', 'LBH', 'LBO', 'LBT'],
                    'BR': ['BRP', 'BRH', 'BRO', 'BRT'],
                    'B2': ['B2P', 'B2H', 'B2O', 'B2T'],
                    'B3': ['B3P', 'B3H', 'B3O', 'B3T']
                    }

    @staticmethod
    def get_zowe_server(environment: str) -> str:
        server_ip = os.getenv(f'ZOWE_IMAGE_{environment.upper()}')
        if server_ip is None:
            print('Nenhum socket foi passado à aplicação')
            exit()
        return f'{server_ip}:7554'

    @staticmethod
    def add_chars_to_string_side(string: str, qty: int, chars: str, side: str) -> str:
        if side == 'left':
            return qty * chars + string
        elif side == 'right':
            return string + qty * chars
        else:
            return string

    def get_endpoint(self):
        return "https://" + self.servidores[self.svr.upper()]

    def is_logged(self, amb) -> bool:
        self.user = os.getenv('USER')
        self.pwd = os.getenv('PWD')
        self.svr = amb.upper()
        return True if self.logon_zowe(ambiente=self.svr) != 'erro' else False

    def logon_zowe(self, ambiente: str) -> object:  # efetua logon e recupera cookie
        resp = None
        try:
            self.msg_logon = f'Tentando conectar ao Zowe {ambiente}...'
            self.endpoint = self.get_zowe_server(ambiente)
            print(self.msg_logon)
            method_ws = "auth/login"
            headers = {'Content-Type': 'application/json', 'X-CSRF-ZOSMF-HEADER': ''}
            data = {}
            urllib3.disable_warnings()
            resp = requests.post(url=f"{self.endpoint}/gateway/api/v1/{method_ws}",
                                 headers=headers, json=data, auth=(self.user, self.pwd),
                                 verify=False)
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            self.cookie = 'erro'
        except JSONDecodeError as json_err:
            print(f'Json decode error: {json_err}')
            self.cookie = 'erro'
        except requests.exceptions.RequestException as e:
            print(e, 'Sem conexão com o Zowe')
            self.cookie = 'erro'
        except (ConnectionError, Timeout) as e:
            print(e, 'Sem conexão com o Zowe')
            self.cookie = 'erro'
        except ConnectTimeout as e:
            print(e, 'Sem conexão com o Zowe')
            self.cookie = 'erro'
        except NewConnectionError as e:
            print(e, 'Sem conexão com o Zowe')
            self.cookie = 'erro'
        except KeyboardInterrupt as e:
            print(e, 'Sem conexão com o Zowe 4')
            self.cookie = 'erro'
        except Exception as err:
            print(f'Other error occurred: {err}')
            self.cookie = 'erro'

        if self.cookie != 'erro':
            self.cookie = self.get_cookie(resp)
        return self.cookie

    @staticmethod
    def get_cookie(response: Response) -> dict:
        return dict(apimlAuthenticationToken=response.cookies['apimlAuthenticationToken'])

    def get_partitioned_dataset_members(self, partition: str, iniciado_por: str, filter_names):
        self.mask = iniciado_por  # [0:qt].upper()
        start = "/datasets/api/v2/" if os.getenv('AMBIENTE') != 'B3' else "/datasets/api/v1/"
        self.endpoint = self.get_endpoint()
        url = f'{self.endpoint}{start}{partition.upper()}/members'
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        result = json.loads(retorno.text)
        if result is not None:
            retorno = filter(filter_names, result['items'])
        return list(retorno)

    def get_members_zos_dataset(self, particionado, iniciado_por, atributo, qt, mig):
        # basic auth
        # Lista membros de um particionado fornecido
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        self.endpoint = self.get_endpoint()
        atrib = atributo
        migrated_behave = mig
        qry = '?start='
        mask = qry + iniciado_por if iniciado_por != '' else ''
        url = f'{self.endpoint}{start}{particionado.upper()}/member{mask}&pattern={mask}*'
        headers = {'X-IBM-Attributes': atrib, 'X-IBM-Max-Items': str(qt), 'X-IBM-Migrated-Recall': migrated_behave,
                   "X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.text)

    def get_dataset_member_content(self, membro_com_caminho):
        # basic auth
        # conteúdo de membro de um particionado fornecido
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        self.endpoint = self.get_endpoint()
        url = self.endpoint + start + membro_com_caminho.upper()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return ['erro', retorno] if 'status' in retorno.text or 'category' in retorno.text \
            else ['ok', retorno.text.splitlines()]

    def write_dataset_content(self, dataset, member, conteudo: str, caps: bool):
        # basic auth
        # escreve num membro ou dataset, cria se não existir, senão sobrescreve conteúdo
        # caps se true o conteúdo será uppercase
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        destino = dataset + '(' + member + ')' if member != '' else dataset
        if caps:
            conteudo = conteudo.upper()
        url = self.endpoint + start + destino.upper()
        retorno = requests.put(url=url, cookies=self.cookie, headers=headers, data=conteudo.encode('utf-8'),
                               auth=(self.user, self.pwd), verify=False)
        return retorno

    def create_dataset_partition(self, dataset_name, body):
        # vide zowe_methods_doc.txt
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        data = body
        url = self.endpoint + start + dataset_name.upper()
        retorno = requests.post(url=url, cookies=self.cookie, headers=headers, json=data, auth=(self.user, self.pwd),
                                verify=False)
        return retorno.text

    def list_zos_datasets(self, dslevel, x_ibm_attribs='', max_items=100, volser='', sttart=''):
        # dslevel é o nome ou máscara do nome do arquivo
        # traz tb os atributos do arquivo se passar base no campo X-IBM-Attributes
        # se o dataset estiver migrado, traz somente o nome e o flag migrado
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds?dslevel="
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        if x_ibm_attribs != '':
            headers["X-IBM-Attributes"] = "base"
        headers["X-IBM-Max-Items"] = str(max_items)
        tail = ''
        if volser != '':
            tail += '&volser=' + volser
        if sttart != '':
            tail += '&startr=' + sttart
        url = self.endpoint + start + dslevel.upper() + tail
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return retorno.content

    def get_dataset_attributes(self, dataset):
        # retorna atributos de datasets do filtro dataset
        # https://172.17.211.150:7554/api/v1/datasets/HMH.ATB.ATBF307.E307.SS000121%20%20
        start = "dataset/api/v2/" if os.getenv('AMBIENTE') != 'B3' else "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper()
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.content)['items']

    def get_dataset_contents(self, dataset):  # usar com calcaloc
        # retorna o conteúdo de um dataset
        start = "/datasets/api/v2/" if os.getenv('AMBIENTE') != 'B3' else "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper() + '/content'
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        if 'status' in json.loads(retorno.content):  # caso tenha dado erro
            return ['erro', json.loads(retorno.content)]
        elif json.loads(retorno.content)['records'] == '':
            return ['erro', json.loads(retorno.content)['records']]
        else:
            return ['ok', json.loads(retorno.content)['records']]

    def get_zosmf_dataset_attributes(self, dataset):
        # retorna atributos de datasets do filtro dataset
        # https://172.17.211.150:7554/ibmzosmf/api/v1/zosmf/restfiles/ds?dslevel=
        start = "/datasets/api/v2/" if os.getenv('AMBIENTE') != 'B3' else "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.get_endpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper()
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.content)['items']

    def gera_dataframe_geral(self, dataset, headers):
        ret = self.get_dataset_contents(dataset)
        if ret[0] != 'erro':
            a = ret[1].splitlines()
            relat = []
            dicio = {}
            for linha in a:
                campos = linha.split()
                for i in range(len(campos)):
                    dicio[headers[i]] = campos[i]
                relat.append(dicio)
                dicio = {}
        else:
            return ['erro', ret[1]]
