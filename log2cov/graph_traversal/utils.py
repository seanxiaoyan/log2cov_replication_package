from ast import *
import logging
import re
import os 

def read_file(filename):
  if not os.path.exists(filename):
    return None
  try :
    with open(filename, "rt") as file:
        return file.read()
  except IsADirectoryError:
    logging.error(f"{filename} is a directory")

def seq_to_string(seq):
  return "".join([str(x) for x in seq])

def remove_duplicate_log(log):
  non_dup = []
  for item in log:
    if item not in non_dup:
      non_dup.append(item)

  return non_dup

def validate_log(log):
  # check if log has only one element and that element is []
  try:
    log[1]
  except IndexError:
    return -1
  return 1

def astNotFoundHandler(name):
  pass

def mark_loop(log):
  for seq in log:
    if seq:
      seq[0].begin_loop = True
      seq[-1].end_loop = True

def mark_cycle_begin(log):

  # list of list
  for seq in log:
    if seq:
      seq[0].begin_cycle = True


def mark_cycle_end(log):

  for seq in log:
    if seq:
      seq[-1].end_cycle = True


# def complete_missing_coverage(hit_return_log, coverage_pool):
#   '''
#   Complete missing coverage of log sequence in hit return log 
#   hit_return_log: list of logSeq objects
#   coverage_pool: list of coverage infos for conditional branches
#   '''
#   for obj in hit_return_log:
#     if obj.log:
#       index = obj.coverage_pool_index
#       # assign coverage info to a logRe in log sequence, any logRe in log sequence can be used, we choose the last one
#       for log_seq in obj.log:
#         log_seq[-1].must_not_coverage += itertools.chain(*coverage_pool[index:])
      


def get_logRe_docs(visitor, log_seq=None):

    docs_log = _get_logRe_docs(visitor.log, visitor.cycle, visitor.filepath, log_seq)
    docs_hit_log = _get_logRe_docs(visitor.hit_return_log, visitor.cycle, visitor.filepath, log_seq)
    
    return docs_log + docs_hit_log


def _get_logRe_docs(log, cycle, filepath, log_seq):

  docs = []
  dic = {}

  for seq in log:
    if seq:
        if cycle and filepath in cycle:
            seq[0].begin_cycle = True 
            seq[-1].end_cycle = True

    logRE = ""
    code_path = set()
    may_coverage = set()
    must_not_coverage = set()


    cycle_begin = False
    loop_begin = False

    
    for l in seq:
        logRE_component = ""
        if l.begin_cycle and not cycle_begin:
            logRE_component += "("
            cycle_begin = True
        if l.begin_loop and not loop_begin:
            logRE_component += "("
            loop_begin = True
        if l.module and l.lineno:
          logRE_component += l.module
          logRE_component += "@"
          logRE_component += str(l.lineno)
        if l.end_loop and loop_begin:
          # check if component end with (
          if logRE_component:
            if logRE_component[-1] == "(":
              logRE_component = logRE_component[:-1]
            else:
              logRE_component +=")*"
          # check if logRE end with (
          elif logRE:
            if logRE[-1] == "(":
              logRE = logRE[:-1]
            else:
              logRE_component +=")+"
          loop_begin=False
        if l.end_cycle and cycle_begin:
          if logRE_component:
            if logRE_component[-1] == "(":
              logRE_component = logRE_component[:-1]
            else:
              logRE_component +=")+"
          # check if logRE end with (
          elif logRE:
            if logRE[-1] == "(":
              logRE = logRE[:-1]
            else:
              logRE_component +=")+"
          cycle_begin=False
     
        logRE += logRE_component

    if not logRE:
      continue
    
    logRE = check_standalone(logRE)
    # valid logRE
    if not validate_logRE(logRE):
      continue
    
    if log_seq:
      # match logRE
      pattern = re.compile(logRE+'\D') # add '\D' to avoid match file@3 with file@31
      _match = re.search(pattern, log_seq)
      if not _match:
        continue
    
    # update Must Coverage
    for l in seq:
      if l.may_coverage:
          may_coverage.update(l.may_coverage)

      if l.must_not_coverage:
        must_not_coverage.update(l.must_not_coverage)

      if l.coverage:
        for path in l.coverage:
            if path not in code_path:
              code_path.add(path)
    
    # logging.info(f"{logRE} [{filepath}] {code_path}")
    non_covered = must_not_coverage-code_path
    doc = {
      'logRE': logRE,
      'coverage': code_path,
      'may_coverage': may_coverage,
      'must_not_coverage': non_covered,
      'entry': filepath
    }
    
    # If logRE already exists in the entry_dict, update fields as necessary
    if logRE in dic:
      dic[logRE]['coverage'] = dic[logRE]['coverage'].union(code_path)
      dic[logRE]['may_coverage'] = dic[logRE]['may_coverage'].union(may_coverage)
      dic[logRE]['must_not_coverage'] = dic[logRE]['must_not_coverage'].union(non_covered)
    else:
      # logRE does not exist in entry_dict, so just add it
      dic[logRE] = doc

  
  for k, v in dic.items():
    new_doc = {
      'logRE': v['logRE'],
      'coverage': list(v['coverage']),
      'may_coverage': list(v['may_coverage']),
      'must_not_coverage': list(v['must_not_coverage']),
      'entry': v['entry']
    }
    docs.append(new_doc)

  return docs
  
def print_seq(node_visitor):
  '''
  Print all log sequences of the given node visitor, including corresponding covered path
  '''
  _print_seq(node_visitor.log, node_visitor.cycle, node_visitor.filepath, node_visitor.path_visited)

  # hit_return_log = []
  # # for obj in node_visitor.hit_return_log:
  # #   if obj.log:
  # #     hit_return_log += obj.log
  _print_seq(node_visitor.hit_return_log, node_visitor.cycle, node_visitor.filepath)

def _print_seq(log, cycle, filepath, path_outside_condition_branch=[]):
  '''
  path_outside_condition_branch: coverage outside condition branch, used to complete coverage, not for hit return log.
  '''

  # docs = []

  for seq in log:
    if seq:
        if cycle and filepath in cycle:
            seq[0].begin_cycle = True 
            seq[-1].end_cycle = True

    logRE = ""
    code_path = set(path_outside_condition_branch)
    must_not_coverage = set()
    may_coverage = set()
    # for path in node_visitor.path_visited:
    #     if path not in code_path:
    #         code_path.add(path)
    cycle_begin = False
    loop_begin = False

    
    for l in seq:
        if l.may_coverage:
          may_coverage.update(l.may_coverage)
        if l.must_not_coverage:
          must_not_coverage.update(l.must_not_coverage)
        logRE_component = ""
        if l.begin_cycle and not cycle_begin:
            logRE_component += "("
            cycle_begin = True
        if l.begin_loop and not loop_begin:
            logRE_component += "("
            loop_begin = True
        if l.module and l.lineno:
          logRE_component += l.module
          logRE_component += "@"
          logRE_component += str(l.lineno)
        if l.end_cycle and cycle_begin:
          if logRE_component:
            if logRE_component[-1] == "(":
              logRE_component = logRE_component[:-1]
            else:
              logRE_component +=")+"
          # check if logRE end with (
          elif logRE:
            if logRE[-1] == "(":
              logRE = logRE[:-1]
            else:
              logRE_component +=")+"
          cycle_begin=False
        if l.end_loop and loop_begin:
          # check if component end with (
          if logRE_component:
            if logRE_component[-1] == "(":
              logRE_component = logRE_component[:-1]
            else:
              logRE_component +=")+"
          # check if logRE end with (
          elif logRE:
            if logRE[-1] == "(":
              logRE = logRE[:-1]
            else:
              logRE_component +=")+"
          loop_begin=False
        logRE += logRE_component

    logRE = check_standalone(logRE)

    if not validate_logRE(logRE):
      continue
    if not logRE:
      continue



    for l in seq:
      if l.coverage:
        for path in l.coverage:
            if path not in code_path:
                code_path.add(path)

    l_must = list(code_path-must_not_coverage)
    l_must_not = list(must_not_coverage-code_path)
    l_must_not.sort()
    l_must.sort()
    l_may = list(may_coverage)
    l_may.sort()
    print(f'LogRE: {logRE}')
    print(f'must: {l_must}')
    print(len(code_path))
    print(f'must_not: {l_must_not}')
    print(f'may: {l_may}')

def check_standalone(logRE):
  standalone_pattern =  r"^\(\w[.\w]*@(\d+|\(\d+(\|\d+)*\))\)\*$"

  if re.match(standalone_pattern, logRE):
      return logRE.replace('*', '+')

  return logRE

def validate_logRE(logRE):
  '''
  Validate if the given logRE is a valid regular expression pattern
  '''
 
  try:
    re.compile(logRE)
    if re.search(r"\*\Z", logRE) is not None:
      return False
    return True
  except re.error:
    return False
  
def get_ast(path):
    str_repr = read_file(path)
    if str_repr:
      tree = eval(str_repr)
      return tree
    else:
      return None

def mark_must_not_coverage(branch_1_log, branch_1_coverage, branch_2_log, branch_2_coverage, fn_def_lineno):
  # label coverage difference
  
  # branch_1_must_not_coverage = branch_2_coverage - branch_1_coverage 
  branch_1_must_not_coverage = branch_2_coverage - branch_1_coverage
  for seq in branch_1_log:
    if seq:
      if seq[0].must_not_coverage:
        seq[0].must_not_coverage.update(branch_1_must_not_coverage)
      else:
        seq[0].must_not_coverage = branch_1_must_not_coverage
      
      if seq[0].must_not_coverage:
        # remove function definition line number from must_not_coverage
        if bool(fn_def_lineno & seq[0].must_not_coverage):
          seq[0].must_not_coverage-=fn_def_lineno
                

  # branch_2_must_not_coverage = branch_1_coverage - branch_2_coverage
  branch_2_must_not_coverage = branch_1_coverage - branch_2_coverage
  for seq in branch_2_log:
    if seq:
      if seq[0].must_not_coverage:
        seq[0].must_not_coverage.update(branch_2_must_not_coverage)
      else:
        seq[0].must_not_coverage = branch_2_must_not_coverage
      
      if seq[0].must_not_coverage:
        # remove function definition line number from must_not_coverage
        if bool(fn_def_lineno & seq[0].must_not_coverage):
          seq[0].must_not_coverage-=fn_def_lineno


def found_log(visitor):
  if visitor.log:
    for seq in visitor.log:
      for logRe in seq:
        if logRe.lineno:
          return True

  return False