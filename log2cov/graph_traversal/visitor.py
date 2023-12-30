import os
import ast
from graph_traversal.logre import logRe
from graph_traversal.utils import *
import logging
import glob
import shutil
from config import LogConfig

class newVisitor(ast.NodeVisitor):
    def __init__( self, filepath, size, size_hit_return, module_path=None,call_stack=None, visitor_type =1, 
    path_visited = None, end_lineno = None, fn_def_lineno = None, path_all = None): # visitor_type 2: condintional branch visitor, 1: other visitor

      self.conditional_branch_visitor_cycle_begin = False
      self.log = []
      self.hit_return = False
      self.hit_return_log = []

      self.end_lineno = end_lineno
      self.fn_def_lineno = fn_def_lineno if fn_def_lineno else set()

      self.size = size
      self.size_hit_return = size_hit_return

      if path_visited:
        self.path_visited = path_visited
      else:
        self.path_visited = set()
      
      if path_all:
        self.path_all = path_all
      else:
        self.path_all = set()

      if module_path:
        self.module_path = module_path

      if call_stack:
        self.call_stack = call_stack
      else:
        self.call_stack = [filepath]

      self.filepath = filepath
      self.cycle = None

      if visitor_type:
        self.visitor_type =visitor_type

    def visit_Raise(self, node):
      self.visit_Return(node)
      
    def visit_Return(self, node):
      # handle early return
      if node.lineno != self.end_lineno:
        self.hit_return = True
      self.set_code_path(node)
      self.generic_visit(node)

    def set_code_path(self, node):
      # record code path
      if hasattr(node,"lineno"):
        line = f'{self.module_path}@{node.lineno}'
        if line not in self.path_visited:
          # path_visited is the list contains all the code path outside the conditional branch
          self.path_visited.add(line)
        
        if line not in self.path_all:
          self.path_all.add(line)
          

    def generic_visit(self, node):
      self.set_code_path(node)
      return super().generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
      self.visit_FunctionDef(node)

    def visit_FunctionDef(self, node):
      
      # get rid off the root dirname which is the project name
      self.module_path = node.name

      # record code path
      self.set_code_path(node)

      # set end line number
      self.end_lineno = node.end_lineno
      # set function definition line number
      self.fn_def_lineno.add(f'{self.module_path}@{node.lineno}')

      self.generic_visit(node)

      # handle early return, mark must-not-visit lines
      if self.hit_return:
        for seq in self.hit_return_log:
          visited = set()
          for logRE in seq:
            visited = visited.union(logRE.coverage)
        
          must_not_covereage = self.path_all - visited
          seq[0].must_not_coverage.update(must_not_covereage)

      
    def visit_While(self, node):
      # record code path
      self.set_code_path(node)

      # while branch, pass lineno of While node to While visitor
      while_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path, call_stack= self.call_stack, 
        visitor_type=1, path_visited=self.get_cur_coverage(), end_lineno=self.end_lineno, 
        fn_def_lineno=self.fn_def_lineno)

      for n in node.body:
        while_visitor.visit(n)

      # record all code path
      self.path_all = self.path_all.union(while_visitor.path_all)

      # Mark cycle for visitor.log
      mark_loop(while_visitor.log)

      # merge self.log and while_visitor.log
      new_log = self.merge_log(while_visitor.log)
      if new_log:
        self.log = new_log
        self.size = len(self.log)
      # pass cycle info
      if self.cycle:
        if while_visitor.cycle:
          self.cycle = self.cycle + while_visitor.cycle
      else:
        if while_visitor.cycle:
          self.cycle = while_visitor.cycle
    
      
    def visit_For(self, node):
      # record code path
      self.set_code_path(node)

      # for branch
      for_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path, call_stack= self.call_stack, visitor_type=1, 
        path_visited=self.path_visited, end_lineno=self.end_lineno, fn_def_lineno=self.fn_def_lineno)

      for n in node.body:
        for_visitor.visit(n)

      # record all code path
      self.path_all = self.path_all.union(for_visitor.path_all)
      # Mark loop for visitor.log
      mark_loop(for_visitor.log)

      # merge self.log and for_visitor.log
      
      new_log = self.merge_log(for_visitor.log)
      if new_log:
        self.log = new_log
        self.size = len(self.log)

      # pass cycle info
      if self.cycle:
        if for_visitor.cycle:
          self.cycle = self.cycle + for_visitor.cycle
      else:
        if for_visitor.cycle:
          self.cycle = for_visitor.cycle

    def visit_Try(self, node):
        self.set_code_path(node)

        try_line = f'{self.module_path}@{node.lineno}'
        path_visited_before_branch = self.get_cur_coverage()
        cur_path_visited = self.get_cur_coverage()
        cur_path_visited.add(try_line)

        # try branch
        try_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path, call_stack= self.call_stack, visitor_type=2,
           path_visited=cur_path_visited, end_lineno=self.end_lineno, fn_def_lineno=self.fn_def_lineno)
        
        for n in node.body:
          try_visitor.visit(n)

        if try_visitor.conditional_branch_visitor_cycle_begin:
          mark_cycle_begin(try_visitor.log)
        if found_log(try_visitor):
          if try_visitor.hit_return:
            self.hit_return = True

            new_log = self.merge_log_hit_return(try_visitor.log)
            self.hit_return_log += new_log
            self.size_hit_return = len(self.hit_return_log)
          else:
            new_log = self.merge_log(try_visitor.log)
            self.log += new_log
            self.size = len(self.log)
          
        else:
          if not self.log:
            self.log = [[logRe()]]
            self.size = 1
          self.path_visited = path_visited_before_branch
          may_coverage = try_visitor.path_visited - path_visited_before_branch
          try:
            for i in self.log:
              i[0].may_coverage.update(may_coverage)
          except IndexError:
            logging.error(f'index error at: {self.filepath} try block, line {node.lineno}')

        # pass hit return log
        new_log = self.merge_log_hit_return(try_visitor.hit_return_log)
        self.hit_return_log += new_log
        self.size_hit_return = len(self.hit_return_log)

        # pass cycle info
        if self.cycle:
          if try_visitor.cycle:
            self.cycle = self.cycle + try_visitor.cycle
        else:
          if try_visitor.cycle:
            self.cycle = try_visitor.cycle

        for n in node.handlers:
          self.visit(n)
        for n in node.finalbody:
          self.visit(n)

        self.path_all.update(try_visitor.path_all)

    def visit_ExceptHandler(self, node):
 

      except_line = f'{self.module_path}@{node.lineno}'
      path_visited_before_branch = self.get_cur_coverage()
      cur_path_visited = self.get_cur_coverage()
      cur_path_visited.add(except_line)
      # except branch
      exception_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path,
         call_stack= self.call_stack, visitor_type=2, path_visited=cur_path_visited, end_lineno=self.end_lineno, 
         fn_def_lineno=self.fn_def_lineno)
      
      for n in node.body:
        exception_visitor.visit(n)

      # mark cycle begin
      if exception_visitor.conditional_branch_visitor_cycle_begin:
        mark_cycle_begin(exception_visitor.log)
      

      if found_log(exception_visitor):
        # if there is log sequence found in exception clause, say [[1]]
        #  the log sequence will be forked, e.g., self.log = [[1]] exception.log = [[2]] -> self.log = [[1,2],[1]]
        # then we need to mark must-not coverage for the log sequences [1], since [1] means that exception clause is not visitied
        # we do this by creating a log sequence place holder 
        log_seq = [[logRe()]]



        # check if method return in conditional branch
        # merge_branch = True
        if exception_visitor.hit_return:
          self.hit_return = True

 

          # merge self.log and exception_visitor.log
          new_log = self.merge_log_hit_return(exception_visitor.log) 
          self.hit_return_log += new_log
          self.size_hit_return = len(self.hit_return_log)
          # self.hit_return_log.append(log_hit_ret)

        else: # no return in exception clause
          new_log = self.merge_log(exception_visitor.log)

          self.log += new_log
          self.size = len(self.log)

        # # record must not coverage
        mark_must_not_coverage(branch_1_log=exception_visitor.log, 
        branch_1_coverage=exception_visitor.path_visited - path_visited_before_branch, 
        branch_2_log=log_seq, branch_2_coverage=set(), fn_def_lineno=self.fn_def_lineno)

        
      else:
        # new_log = self.merge_log(exception_visitor.log)
        if not self.log:
          self.log = [[logRe()]] 
          self.size = 1
        self.path_visited = path_visited_before_branch

        # get coverage inside conditional branch
        may_coverage= exception_visitor.path_visited - path_visited_before_branch
        try:

          for i in self.log:
            i[0].may_coverage.update(may_coverage)

        except IndexError:
          logging.error(f'index error at: {self.filepath}')
      
      # pass hit return log
      new_log = self.merge_log_hit_return(exception_visitor.hit_return_log)
      self.hit_return_log += new_log
      self.size_hit_return = len(self.hit_return_log)

      # pass cycle info
      if self.cycle:
        if exception_visitor.cycle:
          self.cycle = self.cycle + exception_visitor.cycle

      else:
        if exception_visitor.cycle:
          self.cycle = exception_visitor.cycle

      self.path_all.add(except_line)
      self.path_all.update(exception_visitor.path_all)

    def visit_If(self, node):
      # record code path
      self.set_code_path(node)  

      test_line = f'{self.module_path}@{node.lineno}'
      path_visited_before_branch = self.get_cur_coverage()
      cur_path_visited_1 = self.get_cur_coverage()
      cur_path_visited_2 = self.get_cur_coverage()
      cur_path_visited_1.add(test_line)
      cur_path_visited_2.add(test_line)
      branch_1_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path, call_stack= self.call_stack, visitor_type=2,\
        path_visited=cur_path_visited_1, end_lineno=self.end_lineno, fn_def_lineno=self.fn_def_lineno)
      branch_2_visitor = newVisitor(self.filepath, self.size, self.size_hit_return, module_path=self.module_path, call_stack= self.call_stack, visitor_type=2, \
        path_visited=cur_path_visited_2, end_lineno=self.end_lineno, fn_def_lineno=self.fn_def_lineno)
    
      for n in node.body:
        branch_1_visitor.visit(n)

      for n in node.orelse:
        branch_2_visitor.visit(n)

      # record all code paths
      self.path_all.update(branch_1_visitor.path_all)
      self.path_all.update(branch_2_visitor.path_all)

      # mark cycle begin
      if branch_1_visitor.conditional_branch_visitor_cycle_begin:
        mark_cycle_begin(branch_1_visitor.log)
      if branch_2_visitor.conditional_branch_visitor_cycle_begin:
        mark_cycle_begin(branch_2_visitor.log)

      


      # merge visitors' log into the parent's log  if they have log
      if found_log(branch_1_visitor) or found_log(branch_2_visitor):
        #  else clause exists
        #  log found in if clause, no log found in else clause, put placeholder to record coverage info
        if node.body and node.orelse and not found_log(branch_2_visitor): 
          branch_2_visitor.log = [[logRe(coverage=branch_2_visitor.path_visited)]]
        #  log found in else clause, no log found in if clause, put placeholder to record coverage info
        elif node.body and node.orelse and not found_log(branch_1_visitor):
          branch_1_visitor.log = [[logRe(coverage=branch_1_visitor.path_visited)]]

        # #  else clause not exists
        # #  there is log found in if clause, put placeholder so it can record must-not coverage later
        if not node.orelse:
          branch_2_visitor.log = [[logRe()]]

        # check if method return in conditional branch
        merge_branch1 = True
        merge_branch2 = True
        if branch_1_visitor.hit_return:
          # self.hit_return = True
          merge_branch1 = False

          # # record must-not coverage
          # mark_must_not_coverage(branch_1_log=branch_1_visitor.log, branch_1_coverage=list(set(branch_1_visitor.path_visited) - set(path_visited_before_branch)), \
          # branch_2_log=branch_2_visitor.log, branch_2_coverage=list(set(branch_2_visitor.path_visited) - set(path_visited_before_branch)))

          # merge branch_1 log and self.log
          new_log = self.merge_log_hit_return(branch_1_visitor.log)

          # construct logHitReturn object for merged log
          # log_hit_ret = logHitReturn(coverage_pool_index=self.coverage_pool_index, log=new_log)
          # self.hit_return_log.append(log_hit_ret)
          self.hit_return_log += new_log
          self.size_hit_return = len(self.hit_return_log)
        
        if branch_2_visitor.hit_return:
          # self.hit_return = True
          merge_branch2 = False

          # # record must-not coverage TO-DO
          # mark_must_not_coverage(branch_1_log=branch_1_visitor.log, branch_1_coverage=list(set(branch_1_visitor.path_visited) - set(path_visited_before_branch)), \
          # branch_2_log=branch_2_visitor.log, branch_2_coverage=list(set(branch_2_visitor.path_visited) - set(path_visited_before_branch)))


          new_log = self.merge_log_hit_return(branch_2_visitor.log)
          self.hit_return_log += new_log
          self.size_hit_return = len(self.hit_return_log)

        


  
        
        if merge_branch1 and merge_branch2: # no return in branch
          # record must not coverage
          # branch_1_visitor.path_visited = branch2_visitor.path_must_not, vise versa
          # just mark a logre in log to record must-not coverage
          mark_must_not_coverage(branch_1_log=branch_1_visitor.log, 
          branch_1_coverage=branch_1_visitor.path_visited - path_visited_before_branch, \
          branch_2_log=branch_2_visitor.log, branch_2_coverage=branch_2_visitor.path_visited - path_visited_before_branch,
          fn_def_lineno=self.fn_def_lineno)

          new_log = self.merge_log(branch_1_visitor.log, branch_2_visitor.log)
          if new_log:
            self.log = new_log
            self.size = len(self.log)

          # if there is no return found in the child visitor, then the parent hit_return_log need to inherit the child hit_return_log
           

        # if there is no return found in the branch1 visitor but there is return found in the branch2 visitor
        # then the parent hit_return_log need to add the branch2 hit_return_log  
        # and parent log need to be merged with branch1 log
        elif merge_branch1: # No return in branch 1, return in branch 2
          mark_must_not_coverage(branch_1_log=branch_1_visitor.log, 
          branch_1_coverage=branch_1_visitor.path_visited - path_visited_before_branch, \
          branch_2_log=branch_2_visitor.log, branch_2_coverage=branch_2_visitor.path_visited - path_visited_before_branch,
          fn_def_lineno=self.fn_def_lineno)

          new_log = self.merge_log(branch_1_visitor.log)
          self.log += new_log
          self.size = len(self.log)


        # if there is no return found in the branch2 visitor but there is return found in the branch1 visitor
        # then the parent hit_return_log need to add the branch1 hit_return_log
        # and parent log need to be merged with branch2 log
        elif merge_branch2: # No return in branch 2, return in branch 1 
          mark_must_not_coverage(branch_1_log=branch_1_visitor.log, 
          branch_1_coverage=branch_1_visitor.path_visited - path_visited_before_branch, \
          branch_2_log=branch_2_visitor.log, branch_2_coverage=branch_2_visitor.path_visited - path_visited_before_branch,
          fn_def_lineno=self.fn_def_lineno)
          
          new_log = self.merge_log(branch_2_visitor.log)
          self.log += new_log
          self.size = len(self.log)

        else:
          mark_must_not_coverage(branch_1_log=branch_1_visitor.log, 
          branch_1_coverage=branch_1_visitor.path_visited - path_visited_before_branch, \
          branch_2_log=branch_2_visitor.log, branch_2_coverage=branch_2_visitor.path_visited - path_visited_before_branch,
          fn_def_lineno=self.fn_def_lineno)



      else:
        # log exists only in if not in else or only in else not in if 
        if not self.log:
          self.log = [[logRe()]] # put a empty list so we can record cycle information later
          self.size = 1

        self.path_visited = path_visited_before_branch
        # get coverage inside conditional branch
        branch_1_coverage= branch_1_visitor.path_visited - path_visited_before_branch
        branch_2_coverage = branch_2_visitor.path_visited - path_visited_before_branch
        # may coverage = branch_1_coverage + branch_2_coverage
        may_coverage = branch_1_coverage | branch_2_coverage

        try:
          for i in self.log:
            # if there is no log (real log not empty logRe that records cycle info) in if clause, then we do not count the underlying may covered code path
            if i and i[0].lineno:
              i[0].may_coverage.update(may_coverage)
        except IndexError:
          # print(f"Error: log is empty, root: {self.filepath}")
          pass

      # pass hit return log
      new_log = self.merge_log_hit_return(branch_1_visitor.hit_return_log)
      self.hit_return_log += new_log
      new_log = self.merge_log_hit_return(branch_2_visitor.hit_return_log)
      self.hit_return_log += new_log
      self.size_hit_return = len(self.hit_return_log)





      
      # pass cycle info
      if self.cycle:
        if branch_1_visitor.cycle:
          self.cycle = self.cycle + branch_1_visitor.cycle
        if branch_2_visitor.cycle:
          self.cycle = self.cycle + branch_2_visitor.cycle
      else:
        if branch_1_visitor.cycle and branch_2_visitor.cycle:
          self.cycle = branch_1_visitor.cycle + branch_2_visitor.cycle
        else:
          if branch_1_visitor.cycle:
            self.cycle = branch_1_visitor.cycle
          if branch_2_visitor.cycle:
            self.cycle = branch_2_visitor.cycle

    def visit_Call(self, node):
      # record code path
      self.set_code_path(node)

      #check if Call is LOG
      if isinstance(node.func, ast.Attribute):
        if isinstance(node.func.value, ast.Name):
          if node.func.value.id in LogConfig.config("pattern"):

            lno = node.lineno
            # if log statement is multiline, then we need to consider all line
            if node.lineno != node.end_lineno:
              lno = "("
              for i in range(node.lineno, node.end_lineno+1):
                lno += str(i) + "|"
              lno = lno[:-1] + ")"

            new_logRe = logRe(module = self.module_path, lineno=lno, coverage=self.path_visited)

            if self.log:
              for i in self.log:
                  i.append(new_logRe)
            else:
                new = []
                new.append(new_logRe)
                self.log.append(new)
            
        if os.path.exists(node.func.attr) and node.func.attr.endswith(".txt"):
          if not node.func.attr in self.call_stack:
            self.handle_callee(node.func.attr)
          else:
            self.handle_cycle(node.func.attr)

        else:
          astNotFoundHandler(node.func.attr)
        self.generic_visit(node)

      elif isinstance(node.func, ast.Name):
        if os.path.exists(node.func.id) and node.func.id.endswith(".txt"):
          if not node.func.id in self.call_stack:
            self.handle_callee(node.func.id)
          else:
            self.handle_cycle(node.func.id)
        self.generic_visit(node)
      else:
        self.generic_visit(node)
    


    def handle_callee(self, callee):
      if len(self.call_stack) > 20:
        return 
        
      self.call_stack.append(callee)
      
      tmp = self.module_path
      # print(f"*** Start processing {callee} ***")
      visitor = self.process_file(callee, self.call_stack)
      self.path_visited.update(visitor.path_visited)
      self.path_all.update(visitor.path_all)
      self.handle_hit_return(visitor)

      # always merge list first before mark cycle, this can avoid using log placeholder
      if visitor.cycle and callee in visitor.cycle:
        mark_cycle_begin(visitor.hit_return_log)
        mark_cycle_end(visitor.hit_return_log)
        #handle recursion
        if visitor.log:
          mark_cycle_begin(visitor.log)
          mark_cycle_end(visitor.log)
          

          # merge list self.log and visitor.log
          new_log = self.merge_log(visitor.log)
          if new_log:
            self.log = new_log
            self.size = len(self.log)
        
      elif visitor.cycle and self.filepath in visitor.cycle:
        # handle cyclic call chain  
        # merge list self.log and visitor.log
        if visitor.log:
          new_log = self.merge_log(visitor.log)
          if new_log:
            self.log = new_log
            self.size = len(self.log)

        if self.log and not visitor.log: # cycle begin and end in self.log
          mark_cycle_begin(self.log)
          mark_cycle_end(self.log)
          
        if not self.log and visitor.log: # cycle begin and end in visitor.log
          mark_cycle_begin(visitor.log)
          mark_cycle_end(visitor.log)

        if self.log and visitor.log: # cycle begin in self.log , cycle end in visitor.log
          mark_cycle_begin(self.log)
          mark_cycle_end(visitor.log)
          if self.visitor_type == 2:
            self.conditional_branch_visitor_cycle_begin = True

      else:
        self.cycle = visitor.cycle
        # merge list self.log and visitor.log
        if visitor.log:
          new_log = self.merge_log(visitor.log)
          if new_log:
            self.log = new_log
            self.size = len(self.log)

      self.module_path = tmp
      self.call_stack.pop()
      
      # print(f"*** Done processing {callee} ***")
    
    def process_file(self, ast_path, stack):

      # check if ast_path exists, if not, that means missing path component in ast path
      # ex: AST/salt/salt/config/get_cloud_config_value.txt
      #  -> AST/salt/salt/config/__init__/get_cloud_config_value.txt
      if not os.path.exists(ast_path):
        left_part = ast_path.rsplit('/',1)[0]
        right_part = ast_path.rsplit('/',1)[1]
        middle_part = '**'
        pattern = os.path.join(left_part,middle_part,right_part)
        for fname in glob.glob(pattern, recursive=True):
            if os.path.isfile(fname):
                target_path = fname
        shutil.copyfile(target_path, ast_path)
      t = get_ast(ast_path)
      visitor = newVisitor(filepath=ast_path, size=self.size, size_hit_return=self.size_hit_return, call_stack=stack, path_visited=self.path_visited)
      visitor.visit(t)

      # add visitor.fn_def_lineno  to self.fn_def_lineno
      self.fn_def_lineno.update(visitor.fn_def_lineno)
      return visitor

    def merge_log(self, visitor_log, visitor2_log=None):
      '''
      cartisian product of log sequences

      e.g. self.log: [['log@1'],['log@2']] 
           visitor_log: [['log@3'],['log@4']] 
           out:      [['log@1', 'log@3'], ['log@1', 'log@4'], ['log@2', 'log@3'], ['log@2', 'log@4']]

      '''
    

      # limit size due to memory constraint
      
      if visitor_log and self.size + len(self.log) * len(visitor_log) > 100000:
        return []
      if visitor2_log and self.size + len(self.log) * len(visitor2_log) > 100000:
        return []

      new_log =[]
      # uniq_seq = set()

      if self.log:
        for i in self.log:
          for j in visitor_log:
            combine = i+j
            # str_repr = seq_to_string(combine)
            # if combine and str_repr not in uniq_seq:
            new_log.append(combine)
              # uniq_seq.add(str_repr)
          if visitor2_log:
            for d in visitor2_log:
              combine = i+d 
              # str_repr = seq_to_string(combine)
              # if combine and str_repr not in uniq_seq:
              new_log.append(combine)
                # uniq_seq.add(str_repr)

      else:
        for i in visitor_log:
            new_log.append(i)
        if visitor2_log:
          for i in visitor2_log:
            # str_repr = seq_to_string(i)
            # if str_repr not in uniq_seq:
              new_log.append(i)
              # uniq_seq.add(str_repr)

      return new_log
    def handle_cycle(self, callee):
      # print("*** handle cycle")

      # encounter cyclic call chain. e.g. A -> B -> A
      # Every LogRE obtained between A and A should be grouped and marked "+"
      if self.cycle:
        self.cycle.append(callee)
      else:
        self.cycle  = [callee]

    def get_cur_coverage(self):
      coverage = set()
      for i in self.path_visited:
        coverage.add(i)
      return coverage

    def handle_hit_return(self, visitor):
      # complete missing coverage information for visitor hit_return_log

      # merge visitor.hit_return_log and self.log

      new_log = self.merge_log_hit_return(visitor.hit_return_log)
      # add visitor.hit_return_log to self.hit_return_log
      self.hit_return_log += new_log
      self.size_hit_return = len(self.hit_return_log)

    def merge_log_hit_return(self, hit_return_log):
      if not hit_return_log:
        return []

      if self.size_hit_return + len(self.log) * len(hit_return_log) > 100000:
        return []

      if self.log:
        new_log =[]

        # copy log so later changes won't modify hit_return_log
        self_log_copy = self.copy_logs(self.log)
        hit_return_log_copy = self.copy_logs(hit_return_log)

        for i in self_log_copy:
          for logRe in i:
            logRe.coverage = []
          for j in hit_return_log_copy:
            combine = i+j
            new_log.append(combine)


        return new_log

      else:
        return hit_return_log.copy()
    

    def copy_logs(self, logs):
        """
        logRE: list of lists of logRE objects

        Returns a copy of the logRE
        """
        new_logs = []
        for seq in logs:
            new_seq = []
            for logRE in seq:
                new_logRE = logRE.copy()
                new_seq.append(new_logRE)
            new_logs.append(new_seq)

        return new_logs
    