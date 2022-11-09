import re
import csv


def is_character_a2z(character):
    # test char and return None if false
    pattern = re.compile("[A-Za-z]+")
    return pattern.fullmatch(character)


def read_csv_file(file_name, delimiter=','):
    return_list = []
    with open(file_name, 'r') as file:
        csvreader = csv.reader(file, delimiter=delimiter)
        for row in csvreader:
            return_list.append(row)
    return return_list


def remove_duplicates_from_list(list_with_duplicates):
    list_no_duplicates = []
    for item in list_with_duplicates:
        if item not in list_no_duplicates:
            list_no_duplicates.append(item)
    return list_no_duplicates
