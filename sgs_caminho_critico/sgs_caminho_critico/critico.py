import re
from enum import Enum
from anytree import Node, RenderTree


class Termos(Enum):
    condicoes = '(\W*){2}-(\W*)-(\w*)|(\w*)-(\w*)'


def read_text_files(file_name, code):
    # 'ISO-8859-1'
    with open(file_name, encoding=code) as f:
        lines = f.readlines()
        f.close()
    return lines


def get_treated_schedule_content(lista: list):
    useful_list = {}
    member = ''
    status = ''
    for linha in lista:
        linha = remove_special_chars(linha, '\x00')
        linha = remove_special_chars(linha, '\x01')
        linha = remove_special_chars(linha, '\x9c')
        if linha == '':
            continue
        if linha[0:4] == 'DCTM':
            status = linha[4:]
            if 'MSUSP' in status:
                status = 'SUSP#'
            if 'MFORCADA' in status:
                status = 'FORCADA'
            if 'MBANCARIO' in status:
                status = 'BANCARIO'
        if linha[0] == 'M':
            if 'M---' in linha[0]:
                continue
            member = linha[1:9]
            useful_list[member] = []
            if status != '':
                useful_list[member].append({'status': status})
        if linha[0] == 'L':
            lib = linha[1:16].split()
            useful_list[member].append({'lib': lib})
        if linha[0] == 'Q':
            rec = linha[1:75].split('0001')
            rec = remove_trash_from_list(rec, '', 'r')
            rec = remove_trash_from_list(rec, ' ', 'l')
            useful_list[member].append({'rec': rec})
        if linha[0] == 'I':
            # cond_in = re.search(Termos.condicoes.value, linha[1:], re.IGNORECASE)
            if 'ODAT' in linha[1:]:
                cond_in = linha[1:].split('ODAT')
            else:
                cond_in = linha[1:].split('STAT')
            cond_in = remove_trash_from_list(cond_in, '', 'r')
            useful_list[member].append({'in': cond_in})  # .group(0)
        if linha[0] == 'O':
            # cond_out = re.search(Termos.condicoes.value, linha[1:], re.IGNORECASE)
            if 'ODAT' in linha[1:]:
                cond_out = linha[1:].split('ODAT')
            else:
                cond_out = linha[1:].split('STAT')
            cond_out = remove_trash_from_list(cond_out, '', 'r')
            useful_list[member].append({'out': cond_out})  # .group(0)
    return useful_list


def remove_special_chars(linha, chars):
    return linha.replace(chars, '')


def remove_trash_from_list(lista, trash, side):
    if len(lista) > 1:
        for i in range(len(lista)):
            if side == 'r':
                lista[i] = lista[i].rstrip()
            else:
                lista[i] = lista[i].lstrip()
    return list(filter((trash).__ne__, lista))

def get_ancestor_list(entrance_parts):
    # ['S3-PCPEAF60-PCPEAF61', '&', '|', 'PCPEAF6A-PCPEAF61', '|', 'PCPEAF6B-PCPEAF61', '|', 'PCPEAF6X-PCPEAF61']
    routine = ''
    main_search = []
    secondary_search = []
    to_secondary = False
    for elm in entrance_parts:
        cond_parts = elm.split('-')
        # if cond_parts[0] == '&':
        #     main_search.append(routine)
        #     routine = ''
        #     continue
        # else:
        #     if to_secondary and routine != '':
        #         secondary_search.append(routine)
        #         routine = ''
        #         to_secondary = False
        #         continue

        for elm_sub in cond_parts:
            if elm_sub == 'S3' or elm_sub == 'BBN':
                routine = cond_parts[1]
                continue
            # routine = elm_sub
            if elm_sub == '|':
                to_secondary = True
                break
            if elm_sub == '&':
                main_search.append(routine)
                routine = ''
                break
            if to_secondary:
                routine = elm_sub
            # routine = elm_sub
            # break
            if to_secondary and routine != '':
                secondary_search.append(routine)
                routine = ''
                to_secondary = False
                break
            # routine = elm_sub
            # break
    return main_search, secondary_search

def build_critical_path(routine, listt):
    list_cond = []
    entrance, output = get_in_out_conds(listt[routine.upper()])
    # aqui é útil apenas se as conds tiverem condicionais
    entrance_parts = get_group_parts(entrance, list_cond)
    # mod1: ['S3-PCPEAF60-PCPEAF61', '&', '|', 'PCPEAF6A-PCPEAF61', '|', 'PCPEAF6B-PCPEAF61', '|', 'PCPEAF6X-PCPEAF61']
    if entrance_parts is not None:
        main, secondary = get_ancestor_list(entrance_parts) # mod1 capturou certo
    #
    # entrance_header = entrance[0:entrance.index('(')]
    output_parts = get_group_parts(output)
    if entrance_parts is not None:
        print('ok')
        # começa uma busca pelos antecessores da rotina
    if output_parts is not None:
        print('ok')
        # começa uma busca pelos sucessores da rotina

    # steps
    # condições de entrada  <<===
    # separa por ( e captura o índice 0 este será a condição fora das condições
    # montar uma lista, sendo neste momento indice [0], '&',
    # particiona lista[1] pelo primeiro caracter dela pode ser um |, armazena antes este caracter
    # adiciona à lista anterior este caracter [[0], '&', caracter, ..
    # o resultado particionado será adicionado à lista, intercalado com o caracter
    # [[0], '&', caracter, cond1, caracter, cond2, caracter ...
    # cond_out = is_an_input_condition(output)
    # cond_sign = is_an_add_condition(output)
    # cond_in = is_an_input_condition(entrance)
    # cond_sign2 = is_an_add_condition(entrance)
    return 1


def get_group_parts(input_cond, list_cond):
    input_cond_string = ''
    if isinstance(input_cond, list):
        for elm in input_cond:
            input_cond_string += elm
    else:
        input_cond_string = input_cond
    if '(' in input_cond_string:
        # 'cond(|cond2|cond3...)'
        if '(' in input_cond_string: # modelo PCPEAF61
            input_cond_list = input_cond_string.split('(')
            list_cond.append(input_cond_list[0])
            list_cond.append('&')
            char_bool = input_cond_list[1][0]
            # [cond, &, '|cond2|cond3...')
            if char_bool == '|':
                cond_group_bool = input_cond_list[1].split(char_bool)
                # [cond, &,cond2,cond3...)]
                for elm in cond_group_bool:
                    if elm == '':
                        list_cond.append(char_bool)
                    else:
                        list_cond.append(elm)
                        list_cond.append(char_bool)
                list_cond.pop()
                # [cond, &,|,cond2,|,cond3...)]
                if list_cond[-1][-1] == ')':
                    list_cond[-1] = list_cond[-1][0:-1]
                    # [cond, &,|,cond2,|,cond3...]
            else:
                print('charbool não previsto get_group_parts')
        else:
            input_cond_list = input_cond_string.split('-')
            cond_size = len(input_cond_list)
            if cond_size == 2: # única condição simples
                list_cond.append(input_cond_list[0])
                list_cond.append('&')
                if len(list_cond) == 2 and list_cond[-1] == '&':
                    list_cond = list_cond[0:-1]
            elif cond_size == 3: # única condição com s3 ou bbn
                list_cond.append(input_cond_list[1])
                list_cond.append('&')
                if len(list_cond) == 2 and list_cond[-1] == '&':
                    list_cond = list_cond[0:-1]
            else: # várias condições simples
                for i in range(0, cond_size, 2):
                    list_cond.append(input_cond_list[i])
                    list_cond.append('&')
    else:
        list_cond = None

    return list_cond


def get_in_out_conds(condition_list: list):
    # atenção, há condições que estão entre parênteses e possuem ou |
    entrance = output = ''
    entrance_list = output_list = []
    for condition in condition_list:
        # aqui deve haver um verificador capaz de decidir que get conditions utilizar... talvez
        conditions = get_simple_conditions(condition, 'in')
        if conditions is not None:
            if isinstance(conditions, list):
                for item in conditions:
                    entrance_list.append(item)
            elif isinstance(conditions, str):
                entrance += conditions

        conditions = get_simple_conditions(condition, 'out')
        if conditions is not None:
            if isinstance(conditions, list):
                for item in conditions:
                    output_list.append(item)
            elif isinstance(conditions, str):
                output += conditions

    ret_in = entrance if entrance != '' else entrance_list
    ret_out = output if output != '' else output_list
    return ret_in, ret_out


def get_simple_conditions(list_element, typo):
    if typo in list_element:
        return  list_element[typo]
    else:
        return None

    # if type == 'in':
    #     prefix = 'i-'
    # else:
    #     prefix = 'o-'
    grp_cond = ''
    # if len(cond) > 1:
        # if '(' in cond or '|' in cond or ')' in cond:
        # modelo ['S3-PCPEAF60-PCPEAF61', '(|PCPEAF6A-PCPEAF61', '|PCPEAF6B-PCPEAF61']
        # grp_cond = ''
        # if len(cond) > 1:
    # cond_text = cond
    # cond_text = ''.join(cond)
    # return cond_text
        # for elm_cond in cond:
        #     if elm_cond[0] == '(' and elm_cond[1] != '|':
        #         grp_cond += '('
        #     if elm_cond[0] == '|' and (elm_cond[1] != '(' or elm_cond[1] != ')'):
        #         grp_cond += '|' + elm_cond[1:]
        #     if elm_cond[0:2] == '(|':
        #         grp_cond += '(|' + elm_cond[2:]
        #     else:
        #         grp_cond += elm_cond if elm_cond not in grp_cond else ''

        # faz isso por elemento de cond
        # localiza posição de ( início do agrupamento
        # localiza a posição de | operadores lógicos
        # localiza a posição de ) fim do agrupamento
        # monta tudo numa linha
    # elif len(cond) > 1 and (cond[1] == '-' or cond[1] == '+'):  # isto só serve para cond simples, composta não serve
    #     cond = prefix + cond[0] + cond[1]
    # else:
    #     cond = prefix + cond[0]
    # return cond + grp_cond if grp_cond != '' else ''


def is_an_add_condition(condition):
    if condition[-1] == '-':
        return 0
    elif condition[-1] == '+':
        return 1
    else:
        return 0


def is_an_input_condition(condition):
    if condition[0:2] == 'i-':
        return 1
    else:
        return 0

def built_tree(root, childs):
    # [['PCPCINB2','PCPCOUB2','PCPCTLB2'], ['PCPD020', 'PCPE001'], ['PCPDOTI'], ['PCPEOT2','PCPS005', 'PCPINOT']]
    _root = Node(root)
    for child in childs[0]:
        c = Node(child, parent=_root)
    for child in childs[0]:
        c = Node(child, parent=_root)
    for child in childs[0]:
        c = Node(child, parent=_root)

    level_1_child_1 = Node(34, parent=_root)
    level_1_child_2 = Node(89, parent=_root)

    level_2_child_1 = Node(45, parent=level_1_child_1)
    level_2_child_2 = Node(50, parent=level_1_child_2)

    for pre, fill, node in RenderTree(root):
        print("%s%s" % (pre, node.name))