# CTM Caminho crítico
particionado  backup para obter condicoes da schedule por sigla
brctmp1.schedule.bkp#dia_semana(sigla)
Mnome_member
Icond_in
Ocond_out
Ectrl_ex
Qrecurso
O/I### ignorar

## servidores zowe zosmf
z/OSMF
BSB
https://10.8.36.70/zosmf/LogOnPanel.jsp
BS2
https://10.8.36.68/zosmf/LogOnPanel.jsp
BS3
https://10.8.36.66/zosmf/LogOnPanel.jsp
HOM
https://172.17.221.244/zosmf/LogOnPanel.jsp
DES
https://172.17.209.161/zosmf/LogOnPanel.jsp
LAB
https://172.17.208.135/zosmf/LogOnPanel.jsp

## Particionados backup do backup executa 3/dia
BRA.PCP.SCHZOWE  copia particionados schedules gerado pela CTMDBKP1 

## Arquivo de condições via JCL ou chegada de arquivo
brp.pcp.force.d*.ss*
col 19 rotina que forçou
col 28 jobid de quem forçou
37 rotina forçada
46 odate do forçado




### Erros
Ao acessar particionado protegido
'{"category":6,"rc":8,"reason":386400778,"message":"Data set not found.","details":["IKJ56228I DATA SET HMCTMP1.SCHEDULE.BKP NOT IN CATALOG OR CATALOG CAN NOT BE ACCESSED    "]}'

### arquivos de log de acesso
HMP.LOG.SYSLOGA.D220823.T145902.SS000116
BRP ..
erro ao acessar membro HMCTMP1.SCHEDULE.BKP#SEG(PCP) com o usuário zwepcp
IEF450I ZWEPCP IZUFPROC ZOSMF - ABEND=S222 U0000 REASON=00000000 881
        TIME=15.55.27
/HASP395 ZWEPCP   ENDED - ABEND=S222 pesquisei em HMP.LOG.SYSLOGA.D220823.T155905.SS000116
  Seria acesso? Acessei apenas para leitura.

### condições comuns no arquivo
s3 consulta provável rotina em db2 ler a rotina logo à direita de s3-

detectar condições não deletadas
api ctm tempos inicio fim rotina /statistics




### modelo de schedule 
HOMB DJOD180  LIB HMCTMP1.SCHEDULE.PCP                          TABLE: DJO      
COMMAND ===>                                                    SCROLL===> CRSR 
+---------------------------------- BROWSE -----------------------------------+ 
| =========================================================================== | 
| IN       RDOD124B-DJOD180     ODAT      RDOD215A-DJOD180     ODAT           | 
|          DJOD150-DJOD180      ODAT      RDOD102A-DJOD180     ODAT           |  condicoes in segunda parte é a rotina atual esquerda é antecessora tipo A
|          RDOD102B-DJOD180     ODAT                                          | 
| CONTROL  DJOD180-DJOD181      S             DJOD180-184-524-104  E          | 
|                                                                             | 
| RESOURCE INIT                 0001          CPUDB2FI#$           0001       | 
|                                                                             | 
| FROM TIME         +     DAYS    UNTIL TIME      +     DAYS                  | 
| DUE OUT TIME      +     DAYS    PRIORITY     SAC    CONFIRM                 | 
| TIME ZONE:                                                                  | 
| =========================================================================== | 
| OUT      DJOD180-DJOD178      ODAT +    DJOD180-DJOD179      ODAT +         | cond out primeiro rotina atual - segundo sucessor se tipo A senão apenas mata cond in 
|          RDOD124B-DJOD180     ODAT -    RDOD215A-DJOD180     ODAT -         | 
|          DJOD150-DJOD180      ODAT -    RDOD102A-DJOD180     ODAT -         | 
|          RDOD102B-DJOD180     ODAT -                                        | 

### Análise
Condições a serem ignoradas:
###D0103-SOLD7803

DB2IIT.OPR_RLZD_CND nesta tabela select where jobnaame <> ctm3%
condições do tipo A (+) e modelo O-D marcam a rotina que sucede a rotina O ou seja a D.
SOLD0100-SOLD0103    1608 
SOLD0100-SOLD0103    1608 -

filtro condição sold0100-% 
estou na rotina sold0100 e quero saber para quem passa condição, caso, tipo A. Se for D está apenas deletando.
filtro condição &-sold0100 
estou em qq rotina que passa condição para a sold0100

Use case
condições s3-*  são de jcl passadas por contcnd
nome_job:orderid -> consulta condições tipo A e D 
- condições tipo +  <origem>-<destino>
rejeitar condições <origem> = ###...
origem = nome_job  aponta para job <destino>  e será condição de saída
origem not nome_job aponta para job antecessor = origem e será condição de entrada 


### TODO
#### Para caminho crítico:
- não capturar rotinas com DCTM SUSP
- 

- tabela  D3G1 - BRDB2P1/Banco de dados/Tables/select na tabela DB2IIT.OPR_RLZD_CND condições
- Usuário para acesso em desenv CTMPCP01 provido pelo Sueide, falta demais plexes homologa da API CTM
Alguns métodos dão erro 500, Sueide vai ver com responsável.

#### Para cloudx37:
- WSL do Windows, que já tenho instalado, e nesta imagem instalar 
o docker image. 


## Testes
condin = 'S3-PCPEAF60-PCPEAF61(|PCPEAF6A-PCPEAF61|PCPEAF6B-PCPEAF61|PCPEAF6X-PCPEAF61)'
condout = 'S3-PCPEAF60-PCPEAF61-PCPEAF6A-PCPEAF61-PCPEAF6B-PCPEAF61-PCPEAF6X-PCPEAF61-'

VARIAS CONDIÇOES COM S3 SEM CONDIÇÃO
S3-PCPDRECX-PCPCINB2S3-PCPDRECX-PCPCOUB2S3-PCPDRECX-PCPCTLB2S3-PCPDRECX-PCPDATB2S3-PCPDRECX-PCPDOCB2S3-PCPDRECX-PCPFORB2S3-PCPDRECX-PCPJCLB2S3-PCPDRECX-PCPMSGB2S3-PCPDRECX-PCPPARB2S3-PCPDRECX-PCPRESB2S3-PCPDRECX-PCPCINBRS3-PCPDRECX-PCPCOUBRS3-PCPDRECX-PCPCTLBRS3-PCPDRECX-PCPDATBRS3-PCPDRECX-PCPDOCBRS3-PCPDRECX-PCPFORBRS3-PCPDRECX-PCPJCLBRS3-PCPDRECX-PCPMSGBRS3-PCPDRECX-PCPPARBRS3-PCPDRECX-PCPRESBRS3-PCPDRECX-PCPCINHMS3-PCPDRECX-PCPCOUHMS3-PCPDRECX-PCPCTLHMS3-PCPDRECX-PCPDATHMS3-PCPDRECX-PCPDOCHMS3-PCPDRECX-PCPFORHMS3-PCPDRECX-PCPJCLHMS3-PCPDRECX-PCPMSGHMS3-PCPDRECX-PCPPARHMS3-PCPDRECX-PCPRESHMS3-PCPDRECX-PCPCINB3S3-PCPDRECX-PCPCOUB3S3-PCPDRECX-PCPCTLB3S3-PCPDRECX-PCPDATB3S3-PCPDRECX-PCPDOCB3S3-PCPDRECX-PCPFORB3S3-PCPDRECX-PCPJCLB3S3-PCPDRECX-PCPMSGB3S3-PCPDRECX-PCPPARB3S3-PCPDRECX-PCPRESB3

Em condições com S3 pode ocorrer que na forma abaixo
S3-rotina1-rotina2 
Se rotina1 <> nome da schedule
    então a rotina1 é um jcl que enviou a condição
    logo, a rotina2 será a rotina destinatária da condição
    neste caso, a schedule atual apenas serve de intermediária para as condições e se liga à rotina2 apenas para a passagem de condição
    então, as condições de saída da schedule atual serão também as de entrada com o sinal de '-' ao final para finalizar as condições
