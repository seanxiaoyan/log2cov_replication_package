from parse import *
import re
import config

def get_var_from_log(log_constant, log_location, var_index):
    var_values = set()
    parsed_log_constant = parse_log_constant(log_constant)

    if not parsed_log_constant:
        return

    list_log_msg = find_log_msg(log_location)

    if not list_log_msg:
        return
    
    for log_msg in list_log_msg:
        res = parse(parsed_log_constant, log_msg)
        if not res:
            return 
        
        try:
            val = res[var_index]
            var_values.add(val)
        except IndexError:
            return
        
    return list(var_values)

def find_log_msg(log_location):
    res_log_msg = set()

    log_file_path = config.LOG_FILE_PATH
    with open(log_file_path, 'r') as f:
        for lineno, line in enumerate(f):
            if log_location in line:
                log_msg = line.split(log_location)[1].strip()
                res_log_msg.add(log_msg)

    return list(res_log_msg)

def parse_log_constant(log_constant):
    log_constant = re.sub(r'%(\(\w+\))*s', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*d', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*.02f', '{}', log_constant)
    log_constant = re.sub(r'%0.2f', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*x', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*c', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*o', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*u', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*e', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*E', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*f', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*g', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*G', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*i', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*X', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*r', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*a', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*A', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*n', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*p', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*S', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*U', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*y', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*Y', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*z', '{}', log_constant)
    log_constant = re.sub(r'%(\(\w+\))*Z', '{}', log_constant)

    return log_constant
