#!/usr/bin/python

import sys
import re
from datetime import datetime
from helpers import get_osdetails


def initialize(myfile):
    with open(myfile, 'r') as mf:
        content = mf.readlines()
    return content

reg_for_splines = re.compile('^(cpu|iface|dev|intr|bus|tty|fchost)', re.IGNORECASE)
reg_fibre = re.compile('HOST', re.IGNORECASE)
reg_ignore = re.compile(
    '^(bus.*idvendor|intr.*intr/s|temp.*device)', re.IGNORECASE)
reg_delete = re.compile(' AM | PM ', re.IGNORECASE)
reg_linux_restart = re.compile('LINUX RESTART')
reg_average = re.compile('average|durchsch|\<sum\>', re.IGNORECASE)

### program code


def parse_sar_file(content, myfile, username):
    mydict = {}
    mark = 0
    dict_idx = ""
    fibre_key=""
    for line in content:
        line = line.strip()
        # Convert time to 24hour if AM and PM are given
        # and delete AM and PM from line
        if reg_delete.search(line):
            short_time = line.split()[0]
            time_str = " ".join(line.split()[0:2])
            format = '%I:%M:%S %p'
            new_time = datetime.strptime(time_str, format)
            new_time = new_time.strftime('%H:%M:%S-%z')
            line = re.sub('AM |PM ', '', line)
            line = re.sub(short_time, new_time, line)
        # an empty line has been found before
        if mark == 1:
            fields = line.split()
            if not reg_fibre.search(line):
                if reg_linux_restart.search(line):
                    fields.append(f' {line.split()[0]}')

                mykey = " ".join(fields[1:])
            else:
                fchost = fields.pop()
                fields.insert(1,fchost)
                mykey = " ".join(fields[1:])
                fibre_key = mykey

            # first occurence of heading
            if not mydict.get(mykey):
                # set heading as key
                mydict[mykey] = []
            dict_idx = mykey
            mark = 0
        else:
            if dict_idx and line:
                # append line if heading exists
                if dict_idx != fibre_key:
                    mydict[dict_idx].append(line)
                else:
                    # move last column to second column
                    fchost = line.split()[-1]
                    line_f = line.split()[:-1]
                    line_f.insert(1, fchost)
                    line = " ".join(line_f)
                    mydict[dict_idx].append(line)

        if not line:
            # headings follow empty lines, such we set a mark on empty line
            mark = 1

    return mydict


def return_sar_section(key, data):
    col_names = key.split()
    stats_data = {}
    line_nr = 0
    for line in data:
        if not line:
            continue
        # we calculate average by ourself, we don't need a sum and average in german sar data
        if reg_average.search(line):
            continue
        # search for regex (IFACE, DEV, CPU, ...) in heading
        if reg_for_splines.search(col_names[0]):
            # change time to time__<name_from_regex>
            # e.g. 00:20:01__all or 00:20:01__eth0
            row_name = line.split()[0] + '__' + str(line.split()[1])
            stats_data[row_name] = line.split()[2:]

        else:
            # change time to time__<linenumber>
            # e.g. 00:20:01__5
            row_name = line.split()[0] + '__' + str(line_nr)
            # e.g. stats_data['00:20:01__eth0'] = [0.38      0.00 ...]
            stats_data[row_name] = line.split()[1:]

        line_nr += 1
    return stats_data


def handle_diff_type(key, data):
    '''
    Some sar data are for different NICS, INTERUPTS, CPU's
    They need to be extracted and treated different
    key is a sar section title, e.g.: CPU %usr %nice %sys %iowait %steal %irq %soft %guest %idle
    data is a dict looking like: {23:50:01__142': ['362', '47', '13', '0', '0', '10'],...}
    dict keys should be the line specs for pandas
    '''
    same_type = {}
    for line in data:
        # get signifier, e.g. eth0
        x = line.split('__')[1]
        # get time
        y = line.split('__')[0]
        # insert time into field again
        data[line].insert(0, y)
        if not same_type.get(x):
            # use signifier, e.g. eth0, sda1, all as key
            same_type[x] = [data[line]]
        else:
            # append line if signifier already exists (for different points in time)
            same_type[x].append(data[line])
    
    return(same_type)


def handle_generic_type(key, data):
    '''
    set a generic type to equalize the returning data structure compared
    to non generic types
    '''
    same_type = {}
    same_type['generic'] = []
    for line in data:
        y = line.split('__')[0]
        data[line].insert(0, y)
        same_type['generic'].append(data[line])

    return(same_type)


'''
Create the big Field which contains the final data
structured as:
[['CPU %usr %nice %sys %iowait %steal %irq %soft %guest %gnice %idle', \
{'all': [['00:01:00', '0.23', '5.49', '0.44', '0.02', '0.28', '0.00', \
 '0.01', '0.00', '0.00', '93.53'],[...]]},{...}], ['proc/s, {...}], [...]]
len(field1) = 2
len(dict) = 1
keys = all| <something subtype>| generic
dict contains [[row1],[...], [row n]]
'''

def create_data_collection(content, myfile, username):

    mydict = parse_sar_file(content, myfile, username)
    os_details = get_osdetails(myfile)

    data_collection = []
    for key in mydict.keys():
        data = return_sar_section(key, mydict[key])
        # ignore some keys, don't put data into resultset
        if reg_ignore.search(key):
            continue
        if reg_for_splines.search(key):
            data_collection.append([key, handle_diff_type(key, data)])
        else:
            data_collection.append([key, handle_generic_type(key, data)])

    # put os_details as last field
    data_collection.append(os_details)
    return(data_collection)


if __name__ == '__main__':

    try:
        sf = sys.argv[1]
    except(IndexError):
        print(f'Please specify a sar file')
        sys.exit(1)
    content = initialize(sf)
    # dict spec: {generic|all|et0|sda1|...[time, value1,...,value n]}
    #print([x[1].keys() for x in data_collection if len(x[1]) == 9])
    #print([x[0] for x in data_collection if len(x[1]) == 9])
    #print([x[0] for x in data_collection if x[1].get('generic')])
    #print([x[0] for x in data_collection if not x[1].get('generic')])
    #print([x[1]['all'][0] for x in data_collection if len(x[1]) == 9])
    sar_data = create_data_collection(content, sf)
