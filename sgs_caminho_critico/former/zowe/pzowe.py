"""
Programa: class pzowe
Autor: Paulo Roberto de Rezende
Gerência: DITEC/GPROM/DIV6/EQ64
Objetivo: classe com chamadas a métodos do Zowe
Data final: 05/04/2022
"""

import getpass
import json
import os
from json.decoder import JSONDecodeError
import requests
import urllib3
from requests import Response
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from urllib3.exceptions import NewConnectionError


from enum import Enum

'''
Tentar pegar as seguintes informções de job abendado

imagem  ok
tempo de processamento  ok
programa  ok
gasto de cpu
jobid  ok
run number
Criticidade

arquivos de entrada e saída
informação de alocação dos arquivos


'''


class Rotinas_admitidas(Enum):
    IFAUTOEDIT = '%%IF %%'
    ATUPREV = 'ATUPREV'
    ATUPRV = 'ATUPRV'
    CONTFRC = 'CONTFRC'
    CTMAPI = 'CTMAPI'
    CICS_OPEN_CLOSE = 'PCICE015'
    GUARDA = 'GUARDA'


class Execs_rejeitados(Enum):
    DB2_LOAD = 'PDB2E812'
    DB2_CHECK = 'PDB2E860'
    DB2_REORG = 'PDB2E870'


class Termos_rejeitados(Enum):
    IFJCL = ' IF '


class Linhas_jcl(Enum):
    JOB = '(//\w+\s+)(JOB\s+)'
    NOTE_JOBLINE = "(\/\/)(\s*)(')(\w*\s*){1,20}(')(\))(,)"
    REGION = '(REGION=\d*\w)'
    COND = '(\/\/)(\s*)(COND=\()(\(\d*,EQ\),){1,10}(\(\d*,EQ\))(\)\s*)'
    XEQ = '(\/\*XEQ\s*)(\w*%%\$SIGN%%\.)(JES2\s*)'
    JOBPARM = '(\/\*JOBPARM\s*SYSAFF=\w*%%\$SIGN\s*)'
    JCL_COMMENT = '(\/\/\*)(-){1,90}(\*)(\s*)'
    LIBSYM = '(\/\/\*\s*%%LIBSYM\s*)(\w*\.AUTOEDIT\.)(\w*\s*)(%%MEMSYM\s*\w*%%)(\w*\s*)'
    INCLIB = '(\/\/\*\s*%%INCLIB\s*)(\w*\.AUTOEDIT\.)(\w*\s*)(%%INCMEM\s*\w*\s*)'
    SET_AUTOEDIT = '(\/\/\*\s*%%SET\s*)(%%\w*|\W*\w*\.*){1,10}'
    IF_AUTOEDIT = '(\/\/\*\s*%%IF\s*)(%%\w*|\W*\w*\.*){1,10}'
    ENDIF_AUTOEDIT = '(\/\/\*\s*%%ENDIF\s*)(%%\w*|\W*\w*\.*){1,10}'
    IF_ENDIF_AUTOEDIT = '(\/\/\*\s*%%IF\s*)(%%\w*|\W*\w*\.*){1,10}(\s*%%ENDIF\s*)'
    EXEC_REGULAR = '(\/\/P\w*\s*EXEC\s*P\w*,)'
    LINHA_CARDLIB = '(\/\/\s*CARDLIB=\w*\.\w*\.\w*,\s*)'
    JCL_SIMBOLICO_IGUAL_VALOR_AUTOEDIT = '(\/\/\s*\w*=)(\%\%\w*|\W*\w*)(,\s*)'
    JCL_SIMBOLICO_IGUAL_NUMERO_OU_CARACTER = '(\/\/\s*\w*=)(\w*|\d*)[(,\s*)]*'
    LINHA_QR_OU_SIMBOLICO_IGUAL_VALOR = '(\/\/\s*)(\w*=\d*,){1,10}(\w*=\d*){0,1}(,|\s*)'
    OVERRIDE_STEP = '(\/\/)(\w*\.\w*\s*DD\s*)(\w*=\w*|,|\w*=\(\w*,\d*\)){1,10}(\s*)'
    NOME_DA_PROC = '(?:\/\/P\w*\s*EXEC\s*)(P\w*)'


class Linhas_proc(Enum):
    LINHA_QR = '(\/\/\s*)(\w*=\d*,){1,10}(\w*=\d*){0,1}(,|\s*)'
    CAPTURA_QR = '(&Q[RCT]\S+,&Q[RCT]\S+)(?:\)\,RLSE\)\S*)'


class Pzowe:
    def __init__(self):
        self.size = None
        self.mask = None
        self.user = ''  # chave técnica
        self.pwd = ''
        self.plex = ''
        self.inicio_exec = 0
        self.fim_exec = 0
        self.svr = ''  # onde está baseado o Zowe com que se deseja trabalhar
        self.cookie = ''  # autenticação
        self.endpoint = ""
        self.chkPwd = False
        self.chkUsr = False
        self.ip = ''  # do servidor Zowe
        self.jobname = ''
        self.procname = ''
        self.jobid = ''
        self.tipo = ''  # tipos Job ou Task
        self.owner = ''
        self.prefix = ''
        self.jcl = None
        self.proc = None
        self.proc_db2 = None
        self.jcl_rejected_msg = None
        # self.rotina_processada = False
        self.jcl_accepted_msg = None
        self.get_file_content_error = None
        self.single_step_job = True
        self.proc_to_search = None
        self.filaJES = ''  # 'ACTIVE','OUTPUT','INPUT','ALL'
        self.backup_xeq_jobparm = {'XEQ': '', 'JOBPARM': ''}
        self.prefix_amb = {'HM': ['/*XEQ HMAJES2', '/*JOBPARM SYSAFF=HOMA'],
                           'DS': ['/*XEQ DSAJES2', '/*JOBPARM SYSAFF=DESA']}
        self.ctm3 = {'HM': 'HMXCTM.REXXCTM3.SYSOUT.',
                     'DS': 'DSXCTM.REXXCTM3.SYSOUT'}
        self.SVRS = ['HM', 'LB', 'BR', 'B2', 'B3', 'DS']  # ambientes zowe
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
                              'BS': {'JCL': {'PCP': 'B3CTMP1.JCL.PCP',
                                             'IMPLA': 'B3CTMP1.JCL.IMPLA',
                                             'TESTE': 'B3CTMP1.JCL.TESTE',
                                             'INATIVO': 'B3CTMP1.JCL.INATIVO',
                                             'TMP': 'B3A.PCP.JCLX37'},
                                     'PROC': 'B3P.STDPRI.PROCLIB'}
                              }
        self.locais_arquivos = {'HM': {'JCL': 'HMA.PCP.JCLX37',
                                       'REL': 'HMA.PCP.RELCLX37',
                                       'X37': 'HMH.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'DS': {'JCL': 'DSA.PCP.JCLX37',
                                       'REL': 'DSA.PCP.RELCLX37',
                                       'X37': 'DSH.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'BR': {'JCL': 'BRA.PCP.JCLX37',
                                       'REL': 'BRA.PCP.RELX37',
                                       'X37': 'BRP.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'B2': {'JCL': 'B2A.PCP.JCLX37',
                                       'REL': 'B2A.PCP.RELX37',
                                       'X37': 'B2P.PCP.ALL.CLOUDX37.ABENDS.SS000119'},
                                'B3': {'JCL': 'B3A.PCP.JCLX37',
                                       'REL': 'B3A.PCP.RELX37',
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

    def setUser(self, mens):
        self.user = input(mens)

    def getRespostaMensagem(self, mens):  # utilitária, substitui input
        return input(mens)

    def setPwd(self, mens):
        self.pwd = getpass.getpass(mens)





    def checkCredentials(self):  # verificação básica de chave técnica e senha
        chkPwd = chkUsr = True

        # verifica usuario
        if (self.user == '' or len(self.user) > 7):
            chkUsr = False

            # verifica senha
        if (self.pwd == '' or len(self.pwd) > 8):
            chkPwd = False

        return (chkUsr and chkPwd)

    def checkServer(self):
        # verifica o nome do servidor
        if self.svr == '' or (self.svr.upper() not in (self.SVRS)):
            return False
        return True



    def get_override_root(self, texto: str) -> str:
        start_in = texto.find(' DD ') + 4
        return texto[:start_in]

    @staticmethod
    def add_chars_to_string_side(string: str, qty: int, chars: str, side: str) -> str:
        if side == 'left':
            return qty * chars + string
        elif side == 'right':
            return string + qty * chars
        else:
            return string

    def getChosenServer(self, svr):  # servidor de trabalho do Zowe
        self.svr = svr.upper()

    def decodeServer(self):  # encontra ip do servidor
        self.ip = self.servidores[self.svr]  # '172.17.211.150'

    def setEndpoint(self):
        return "https://" + self.servidores[self.svr.upper()]

    def is_nome_dataset_correto(self, hlq, ambiente, nome_dataset):
        qualificadores = nome_dataset.split('.')
        if qualificadores[0] not in hlq[ambiente]:
            print('nome de arquivo incorreto')
            return False
        else:
            return True

    def logon_zowe(self,
                   ambiente: str) -> object:  # efetua logon no Zowe e recupera cookie para autenticação not basic auth
        resp = ''
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

    def get_cookie(self, response: Response) -> dict:
        return dict(apimlAuthenticationToken=response.cookies['apimlAuthenticationToken'])



    def geraProfile(self):  # criação de perfil no zowe
        print('Gerando profile para ', self.svr, '...')
        cmd1 = 'zowe profiles update zosmf-profile '
        cmd2 = ' --host ' + self.ip + ' --port 443 --user ' + self.user + ' --password '
        cmd3 = ' --rejectUnauthorized false'
        cmd = cmd1 + self.svr + cmd2 + self.pwd + cmd3
        os.system(cmd)
        input('pressione enter para prosseguir ... ')

    def setDados(self, job: str, jobid: str, tipo: str, filaJES='', owner='*',
                 prefix='*'):  # insere dados em atributos
        self.jobname = job
        self.jobid = jobid
        self.tipo = tipo
        self.owner = owner
        self.prefix = prefix
        self.filaJES = filaJES
        self.tipo = 'JOB' if ((tipo == 'J') or (tipo == 'JOB')) else 'STC'
        self.jobid = self.tipo + self.jobid  # if (self.tipo == 'J') else  'STC'+ self.jobid

    def stepPgmFilenumRunningByJobnameJobid(self):  # step, pgm e step number de job em execução
        # cookie based method
        # https://172.17.208.5:7554/jobs/api/v2/GODTCP1/JOB63132/steps
        print('Método: stepPgmFilenumRunningByJobnameJobid[self.jobname, self.jobid, self.tipo]')
        print()
        porta = ':7554'
        start = "/jobs/api/v2/"
        urllib3.disable_warnings()
        url = "https://" + self.ip + porta + start + self.jobname + '/' + self.jobid + '/steps'
        print(url)
        retorno = requests.get(url=url, cookies=self.cookie, verify=False)
        detalhes_job = json.loads(retorno.text)
        for k in detalhes_job:
            print('step ' + k['name'])
            print('pgm ' + k['program'])
            print('step num ' + str(k['step']))

    def getMembersZosDataset(self, particionado, iniciado_por, atributo, qt, mig):
        # basic auth
        # Lista membros de um particionado fornecido
        '''
        iniciado_por pode ser '' para todos
        qt pode ser 0 para até 1000 data sets
        
        https://172.17.208.5:7554/ibmzosmf/api/v1/zosmf/restfiles/ds/lba.pcp.rodtex/member?start=tes
        dataset-name particionado
        start comece por este membro 
        pattern padrão ispf lmmlist service
        headers:
        X-IBM-Max-Items máx num de membros str
        X-IBM-Attributes member apenas member name é retornado  base todos os atributos básicos retornados total 
        X-IBM-Migrated-Recall 
        wait defa se migrado, aguarda desmigração para processar cmd, 
        nowait emite recall mas não espera, 
        error não tenta recall o dataset
        retorno
        { para base
    "items": [
        {
        "member": "TESTE002",
        "vers": 1,
        "mod": 7,
        "c4date": "2021/09/02",
        "m4date": "2021/12/16",
        "cnorc": 26,
        "inorc": 25,
        "mnorc": 26,
        "mtime": "18:58",
        "msec": "34",
        "user": "I176976",
        "sclm": "N"
        },
        ...
    ],
    "returnedRows": 2,
    "totalRows": 2,
    "JSONversion": 1
    }
    para member
    {
    "items": [
        {
        "member": "TESTE001"
        },
       ...
    ],
    "returnedRows": 3,
    "JSONversion": 1
    }
        
    Qdo não encontra, retorna
    '{"category":4,"rc":8,"reason":0,"message":"LMINIT error",
    "details":["ISRZ002 Data set not cataloged - \'LBA.PCP.ROTEX\' was not found in catalog."]}'        
        '''
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        self.endpoint = self.setEndpoint()
        atrib = atributo
        migrated_behave = mig
        qry = '?start='
        mask = qry + iniciado_por if iniciado_por != '' else ''
        url = f'{self.endpoint}{start}{particionado.upper()}/member{mask}&pattern={mask}*'
        headers = {'X-IBM-Attributes': atrib, 'X-IBM-Max-Items': str(qt), 'X-IBM-Migrated-Recall': migrated_behave,
                   "X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.text)

    def reactGetMembersZosDataset(self, retorno, atrib):
        # trata erro
        # '{"category":4,"rc":8,"reason":0,"message":"LMINIT error",
        # "details":["ISRZ002 Data set not cataloged - \'LBA.PCP.ROTEX\' was not found in catalog."]}'
        if 'category' in retorno:
            print('Erro categoria: ', retorno['category'])
            print('RC: ', retorno['rc'])
            print('Mensagem: ', retorno['message'])
            print('Detalhes: ', retorno['details'])
        elif atrib == 'member' or atrib == '':
            for item in retorno['items']:
                print('Membro: ', item['member'])
        elif atrib == 'base':
            for item in retorno['items']:
                print(item)

    def getContentsDatasetMember(self, membro_com_caminho):
        # basic auth
        # conteúdo de membro de um particionado fornecido
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        self.endpoint = self.setEndpoint()
        url = self.endpoint + start + membro_com_caminho.upper()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        # for linha in retorno.text.splitlines():
        #     print(linha)
        if 'status' in retorno.text or 'category' in retorno.text:
            return ['erro', retorno]
        else:
            return ['ok', retorno.text.splitlines()]  # retorna uma lista cada elemento uma linha do arquivo



    def listaConteudoSysoutFile(self, file):  # lista sysout de um arquivo até da fila H
        # basic auth
        # https://172.17.208.5:7554/jobs/api/v1/J908PRR/JOB42342/files/102/content  onde 102 é o id do arquivo de sysout desejado
        file = str(file) if type(file) != 'str' else file
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + "/jobs/api/v2/" + self.jobname + '/' + self.jobid + '/files/' + file + '/content'
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        detalhes_sysout_file = json.loads(retorno.text)
        if 'content' in detalhes_sysout_file:
            return detalhes_sysout_file
        else:
            return 'NOT_FOUND'

    def getReadyUrlContent(self, url):  # retorna conteúdo das urls prontas records-url
        # basic auth
        print('getReadyUrlContent>>>')
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, headers=headers, auth=(self.user, self.pwd), verify=False)
        return retorno.text.split('\n')

    def printListaConteudoSysoutFile(self, detalhes_sysout_file):  # função de impressão
        print('Conteúdo de arquivo da sysout: ')
        if detalhes_sysout_file != 'NOT_FOUND':
            for linha in detalhes_sysout_file['content'].splitlines():
                print(linha)
        else:
            print('Sysout do step abendado não localizada!')

    def getImagemExecTime(self, detalhes_sysout_file, stepAbendado=''):  # eliminate?
        # depende do método listaConteudoSysoutFile
        # roda activeJobsByOwnerPrefix e recupera imagem, rc
        # retcode é a mais mudar lógicaa fora daqui
        retorno = {}
        valores = self.activeJobsByOwnerPrefix()
        retorno['imagem'] = valores['exec-system']
        retorno['retcode'] = valores['retcode']

        for linha in detalhes_sysout_file['content'].splitlines():
            # teste aqui colocar tb o tempo do step abendado ...
            if 'minutes execution time'.upper() in linha:
                tempo = linha.split()
                print('Tempo de execução total do job: ', tempo[1], ' minutos')
                retorno['tempo total'] = tempo[1]
                # if 'S Y S T E M' in linha:
                #     imagem = linha.split()
                #     print('Executado em: ',imagem[18]+imagem[19]+imagem[20]+imagem[21])
                #     retorno['imagem']= imagem[18]+imagem[19]+imagem[20]+imagem[21]
                # if stepAbendado != '':
                if '-' + stepAbendado in linha:
                    tempoStepAbendado = linha.split()
                    print('Tempo de execução do step abendado: ', tempoStepAbendado[8], ' minutos')
                    retorno['tempo step abendado'] = tempoStepAbendado[8]
        return retorno

    # https://172.17.208.5:7554/ibmzosmf/api/v1/zosmf/restjobs/jobs?owner=*&prefix=*&max-jobs=1000&exec-data=Y
    # https://172.17.208.5:7554/ibmzosmf/api/v1/zosmf/restjobs/jobs?owner=*&prefix=*&status=ALL&max-jobs=1000&exec-data=N
    def activeJobsByOwnerPrefix(self):
        # basic auth
        print('activeJobsByOwnerPrefix>>>')
        maxJobs = '&max-jobs=1000&exec-data=Y'
        start = "/ibmzosmf/api/v1/zosmf/restjobs/jobs?owner="
        # owner =    input('Entre o owner........: ') 
        # prefix   = input('Entre o prefix........: ')
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + self.owner + "&prefix=" + self.prefix + "&status=" + self.filaJES + maxJobs
        retorno = requests.get(url=url, headers=headers, auth=(self.user, self.pwd), verify=False)
        dados = json.loads(retorno.text)

        for k in dados:
            # for l in k: # impressão do que vier
            #     print(l,end='');print(': ',end='');print(k[l])
            # print()

            # termo = k['jobname']  if 'jobname' in k else '<< sem dados >>'
            print('Jobname: ', k['jobname'] if 'jobname' in k else '<< sem dados >>')
            print('jobid: ', k['jobid'] if 'jobid' in k else '<< sem dados >>')
            print('Tipo do job: ', k['type'] if 'type' in k else '<< sem dados >>')
            print('Classe: ', k['class'] if 'class' in k else '<< sem dados >>')
            print('Return code: ', k['retcode'] if 'retcode' in k else '<< sem dados >>')
            print('Owner: ', k['owner'] if 'owner' in k else '<< sem dados >>')
            print('Fase: ', k['phase'] if 'phase' in k else '<< sem dados >>', end='')
            print(' - ', k['phase-name'] if 'phase-name' in k else '<< sem dados >>', end='')
            print(' - ' + k['status'] if 'status' in k else '<< sem dados >>')
            print('plex: ', k['exec-member'] if 'exec-member' in k else '<< sem dados >>')
            print('exec-system: ', k['exec-system'] if 'exec-system' in k else '<< sem dados >>')
            print('subsistema: ', k['subsystem'] if 'subsystem' in k else '<< sem dados >>')
            print('job-correlator: ', k['job-correlator'] if 'job-correlator' in k else '<< sem dados >>')
            print('Url: ', k['url'] if 'url' in k else '<< sem dados >>')
            print('Submetido em: ', k['exec-submitted'] if 'exec-submitted' in k else '<< sem dados >>')
            print('Iniciado  em: ', k['exec-started'] if 'exec-started' in k else '<< sem dados >>')
            print('files-url: ', k['files-url'] if 'files-url' in k else '<< sem dados >>')
            print()
        print(url)
        return dados

    def getListJobsByOwnerPrefixFilaJES(self):  # lista jobs por prefix, owner e fila
        # basic auth
        # "https://172.17.208.5:7554/jobs/api/v1?prefix=*&owner=OMV*&status=OUTPUT" -H
        # print('getListJobsByOwnerPrefixFilaJES[self.owner self.prefix]')
        opcoes = ['status=' + self.filaJES,
                  'owner=' + self.owner,
                  'owner=' + self.owner + '&status=' + self.filaJES,
                  'prefix=' + self.prefix,
                  'prefix=' + self.prefix + '&status=' + self.filaJES,
                  'prefix=' + self.prefix + '&owner=' + self.owner,
                  'prefix=' + self.prefix + '&owner=' + self.owner + '&status=' + self.filaJES
                  ]
        opt = ''
        prefix = 'prefix=' + self.prefix if self.prefix != '' else ''
        owner = 'owner=' + self.owner if self.owner != '' else ''
        status = 'status=' + self.filaJES if self.filaJES != '' else ''
        start = "/jobs/api/v1?"
        self.endpoint = self.setEndpoint()
        url = self.endpoint + start
        # vide aqui https://172.17.208.5:7554/apicatalog/ui/v1/#/tile/jobs/jobs
        if prefix != '':
            if owner == '':
                if status == '':
                    opt = opcoes[3]
                else:
                    opt = opcoes[4]
            else:
                if status == '':
                    opt = opcoes[5]
                else:
                    opt = opcoes[6]
        else:
            if owner == '':
                if status != '':
                    opt = opcoes[0]
                else:
                    print('Um dentre prefix, fila ou owner deve ser informado !')
                    exit()
            else:
                if status == '':
                    opt = opcoes[1]
                else:
                    opt = opcoes[2]
        url += opt
        # print('url ', url)
        # print()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        dados = json.loads(retorno.text)
        # print(dados)
        jobs_fila = []
        for k in dados['items']:
            jobs_fila.append(k)
            # for l in k: # impressão do que vier
            #     print(l,': ',k[l])
            # print()
        return jobs_fila




    def getJCL(self):  # recupera o JCL do job
        # traz o JCL de um JOB com opções de pesquisa
        # https://172.17.208.5:7554/ibmzosmf/api/v1/zosmf/restjobs/jobs/CGRIG6L1/JOB39428/files/JCL/records?mode=text
        # basic auth
        self.endpoint = self.setEndpoint()
        start = "/ibmzosmf/api/v1/zosmf/restjobs/jobs/"
        endPart = '/files/JCL/records?mode=text'
        url = self.endpoint + start + self.jobname + '/' + self.jobid + endPart
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        lista = retorno.text.split('\n')
        return lista

    def writeToDataset(self, dataset, member, conteudo: str, caps: bool):
        # basic auth
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        destino = dataset + '(' + member + ')' if member != '' else dataset
        if caps:
            conteudo = conteudo.upper()
        url = self.endpoint + start + destino.upper()
        retorno = requests.put(url=url, cookies=self.cookie, headers=headers, data=conteudo.encode('utf-8'),
                               auth=(self.user, self.pwd), verify=False)
        return retorno



    def issueConsoleCmd(self, consoleName, cmd):
        # https://172.17.208.5:7554/ibmzosmf/api/v1/zosmf/restconsoles/consoles/laba
        '''
        cmd spec
        cmd*	string

Specifies the command to issue.
sol-key	string

Specifies a keyword that you want to detect in solicited messages, that is, the command response. Case is not significant.
solKeyReg	string
default: N

If sol-key specified, solKeyReg indicates whether the sol-key represents a regular expression.
Y: sol-key is a regular expression.
N: sol-key is a normal string. This is the default.
Enum:
Array [ 2 ]
unsol-key	string

Specifies a keyword that you want to detect in unsolicited messages. Case is not significant.
Message suppression can prevent the return of an unsolicited message. To determine whether a particular message ID is suppressed through the message processing facility on your system, enter the following command to list the MPF settings: D MPF.
unsolKeyReg	string
default: N

If unsol-key specified, unsolKeyReg indicates whether the unsol-key represents a regular expression.
Y: unsol-key is a regular expression.
N: unsol-key is a normal string. This is the default.
Enum:
Array [ 2 ]
detect-time	integer
minimum: 1

Indicates how long the console attempts to detect the value of unsol-key in the unsolicited messages. The unit is seconds. For example, if the value of detect-time is 10, the console checks the unsolicited messages for 10 seconds. The default is 30 seconds.
async	string
default: N

Indicates the method of issuing the command.
Y: Asynchronously.
N: Synchronously. This is the default.
Enum:
Array [ 2 ]
system	string

Name of the system in the same sysplex that the command is routed to. The default is the local system.
unsol-detect-sync	string
default: N

Indicates how to detect the keyword that is specified with the unsol-key field from unsolicited messages.
Y: Synchronously detect the keyword from unsolicited messages. The request is not returned until the unsol-detect-timeout value has elapsed or the detection result is complete.
N: Asynchronously detect the keyword from unsolicited messages. The request is returned immediately with the detection-url. The client application must invoke the value of detection-url to poll the result of the detection asynchronously. This is the default is the field is not specified.
Enum:
Array [ 2 ]
unsol-detect-timeout	integer
minimum: 1

Indicates how long the console attempts to detect the value of unsol-key in the unsolicited messages. The unit is seconds. For example, if the value of detect-time is 10, the console checks the unsolicited messages for 10 seconds. The default is 30 seconds.
auth	string
default: INFO

Specifies the authority this console has to issue the operator commands. The value of this field only takes effect when the user issues a command from the console for the first time. Otherwise, this field is omitted. The values are:
MASTER: Allows this console to act as a master console, which can issue all MVS operator commands.
ALL: Allows this console to issue system control commands, input/output commands, console control commands, and informational commands.
INFO: Allows this console to issue informational commands. This is the default.
CONS: Allows this console to issue console control and informational commands.
IO: Allows this console to issue input/output and informational commands.
SYS: Allows this console to issue system control commands and informational commands.
Enum:
Array [ 6 ]
routcode	string
default: NONE

One or more routing codes. The routing codes can be list of n, where n is integers 1 - 128, separated by comma ','.
mscope	string
default: LOCAL

The systems from which this console can receive messages that are not directed to a specific console. The value of this field only takes effect when the user issues a command from the console for the first time. Otherwise, this field is omitted. The values are:
(sysname): List of one or more system names, where system-name can be any combination of A - Z, 0 - 9, # (X'7B'), $ (X'5B'), or @ (X'7C'), and cannot start with number 0-9. Up to 32 systems can be specified if the couple dataset is configured for that many, separated by comma ','. The systems specified after the 32nd will be ignored.
LOCAL: System on which the console is active. This is the default.
ALL: All systems.
storage	integer
minimum: 1

Amount of storage in kilobytes in the TSO/E user's address space, which can be used for message queuing to this console. The value of this field only takes effect when the user issues a command from the console for the first time. Otherwise, this field is omitted. If specified, storage must be a number from 1 – 2000. If you omit the operand, the console uses storage=1 when a session is established. Also, a value of 0 is listed in the OPERPARM segment of the user's profile to indicate that no storage value was specified. Storage is one of the OPERPARM key words.
auto	string
default: NO

Specifies whether or not the console receives messages that are eligible for automation. The value of this field only takes effect when the user issues a command from the console for the first time. Otherwise, this field is omitted.
YES: The console receives messages that are eligible for automation.
NO: The console does not receive messages that are eligible for automation. This is the default.
Enum:
Array [ 2 ]
}
        '''
        start = "/ibmzosmf/api/v1/zosmf/restconsoles/consoles/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        data = cmd
        url = self.endpoint + start + consoleName.upper()
        retorno = requests.put(url=url, cookies=self.cookie, headers=headers, json=data, auth=(self.user, self.pwd),
                               verify=False)
        return retorno

    def decodeGetIssueCmd(self, retorno):
        ret = json.loads(retorno.content)
        for k, v in ret.items():
            print(k, v)
        print()

    def createSeqPartitionDataset(self, datasetName, body):
        '''
        {
volser	string

Volume.
unit	string

Device type.
dsorg	string

Data set organization.
alcunit	string

Unit of space allocation.
primary	integer

Primary space allocation.
secondary	integer

Secondary space allocation.
dirblk	integer

Number of directory blocks.
avgblk	integer

Average block.
recfm	string

Record format.
blksize	integer

Block size.
lrecl	integer

Record length.
storclass	string

Storage class.
mgntclass	string

Management class.
dataclass	string

Data class.
dsntype	string

Dataset type.
}
        '''
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        data = body
        url = self.endpoint + start + datasetName.upper()
        retorno = requests.post(url=url, cookies=self.cookie, headers=headers, json=data, auth=(self.user, self.pwd),
                                verify=False)
        return retorno.text

    def listZosDatasets(self, dslevel, X_IBM_Attributes='', maxItems=100, volser='', sttart=''):
        # dslevel é o nome ou máscara do nome do arquivo
        # traz tb os atributos do arquivo se passar base no campo X-IBM-Attributes
        # se o dataset estiver migrado, traz somente o nome e o flag migrado
        start = "/ibmzosmf/api/v1/zosmf/restfiles/ds?dslevel="
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        if X_IBM_Attributes != '':
            headers["X-IBM-Attributes"] = "base"
        headers["X-IBM-Max-Items"] = str(maxItems)
        tail = ''
        if volser != '':
            tail += '&volser=' + volser
        if sttart != '':
            tail += '&startr=' + sttart
        url = self.endpoint + start + dslevel.upper() + tail
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return retorno.content

    def getDatasetAttributes(self, dataset):
        # retorna atributos de datasets do filtro dataset
        # https://172.17.211.150:7554/api/v1/datasets/HMH.ATB.ATBF307.E307.SS000121%20%20
        start = "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper()
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.content)['items']

    def getDatasetContents(self, dataset):  # usar com calcaloc
        # retorna o conteúdo de um dataset
        # https://172.17.211.150:7554/api/v1/datasets/HMH.PCP.SUBALOC.D220131.SS000109/content
        start = "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper() + '/content'
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        # TODO alterado inserindo elif de arquivo vazio
        if 'status' in json.loads(retorno.content):  # caso tenha dado erro
            return ['erro', json.loads(retorno.content)]
        elif json.loads(retorno.content)['records'] == '':
            return ['erro', json.loads(retorno.content)['records']]
        else:
            return ['ok', json.loads(retorno.content)['records']]

    def getDatasetAttributesZosmf(self, dataset, atributos):
        # retorna atributos de datasets do filtro dataset
        # https://172.17.211.150:7554/ibmzosmf/api/v1/zosmf/restfiles/ds?dslevel=
        start = "/api/v1/datasets/"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        url = self.endpoint + start + dataset.upper()
        retorno = requests.get(url=url, cookies=self.cookie, headers=headers, auth=(self.user, self.pwd), verify=False)
        return json.loads(retorno.content)['items']

    def issueTSOCmdGetResponse(self, cmd):
        # emite comando tso e get response
        # https://172.17.211.150:7554/ibmzosmf/api/v1/zosmf/tsoApp/v1/tso
        start = "/ibmzosmf/api/v1/zosmf/tsoApp/v1/tso"
        urllib3.disable_warnings()
        self.endpoint = self.setEndpoint()
        headers = {"X-CSRF-ZOSMF-HEADER": ""}
        data = {"tsoCmd": cmd.upper()}
        url = self.endpoint + start
        retorno = requests.put(url=url, cookies=self.cookie, headers=headers, json=data, auth=(self.user, self.pwd),
                               verify=False)
        return json.loads(retorno.content)['cmdResponse']  # retorna um list

