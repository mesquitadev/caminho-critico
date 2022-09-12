import os

from critico import read_text_files, get_treated_schedule_content, build_critical_path, built_tree, print_tree, \
     get_raw_frc_conditions
from zowe.pzowe import Pzowe




def is_logged(obj_zowe) -> bool:
    obj_zowe.user = os.getenv('USER')
    obj_zowe.pwd = os.getenv('PWD')
    obj_zowe.svr = os.getenv('AMBIENTE')
    if obj_zowe.logon_zowe(ambiente=obj_zowe.svr) != 'erro':
        return True
    else:
        return False






pzowe = Pzowe()
if is_logged(pzowe):
    hlq_ctm = {'HM':'HMA.PCP.SCHZOWE', 'BR':'BRA.PCP.SCHZOWE', 'B2':'B2A.PCP.SCHZOWE', 'B3':'B3A.PCP.SCHZOWE'}
    file_name = 'BRP.PCP.FORCE.D220830.SS000108'
    print('Logado em ' + pzowe.svr)
    particionado = hlq_ctm[os.getenv('AMBIENTE')]+'(PCP)'
    original_schedule_data = pzowe.getContentsDatasetMember(particionado)

    if original_schedule_data[0] != 'erro':
        adequate_schedule_data = get_treated_schedule_content(original_schedule_data[1])
    else:
        print('Erro ao recuperar arquivo de condições!')
    external_conditions = get_raw_frc_conditions(pzowe, 'BRP.PCP.FORCE.D220830.SS000108')
    built_tree(external_conditions, 'frc', 'CDCD0143')
    cadeia = [['PCPDRCB1','/','PCPCINB2'],['PCPDRCB1','/','PCPCOUB2','/','PCPCTLB2','/','PCPE001','PCPEOT2']]
    print_tree(cadeia)
    exit(0)

    # critical_path = build_critical_path('pcpdrcb1', adequate_schedule_data)
    # built_tree(cadeia)
    print()
    # PCPEAF61 condicionais e s3
    # pcpdrcb1 s3 sem condicionais várias
    # pcpeaf5d bbn- sem condicionais
    # pcpdsta3 uma condição  simples sem condicionais




