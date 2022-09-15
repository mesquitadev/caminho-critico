import csv


class Chain:

    def __init__(self):
        self.routines = []
        self.cond_in = None
        self.cond_out = None

    def get_routines_in_condouts_by_in_conditions(self, in_condition) -> list:
        l = []
        # for i in range(len(in_conditions)):
        for x in range(len(self.cond_out)):
            # result = check_condition_in_list(res, condicoes_rotinas_filhas, i)
            if in_condition in self.cond_out[x]:  # and not result:
                self.routines.append(self.cond_out[x][0])
        for elm in self.routines:
            if elm not in l:
                l.append(elm)
        self.routines = l
        # l = []

        # return l

    def get_in_conditions_by_routine(self, routine) -> list:
        in_conditions = []
        for i in range(len(self.cond_in)):  # captura as entradas  que possuem a rotina
            if routine in self.cond_in[i][0]:
                in_conditions.append(self.cond_in[i][1])
        return in_conditions

    def get_chain(self, routine):
        conditions = self.get_in_conditions_by_routine(routine)
        self.routines.append(routine)
        for condition in conditions:
            self.get_routines_in_condouts_by_in_conditions(condition)

    def read_cond_type(self, file_name, type:str, mode='r'):
        content = []
        with open(file_name, mode) as csvfile:
            csvreader = csv.reader(csvfile)
            for conteudo in csvreader:
                content.append(conteudo)
        if type == 'in':
            self.cond_in = content
        else:
            self.cond_out = content
