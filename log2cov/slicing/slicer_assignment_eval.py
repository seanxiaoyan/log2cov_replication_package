
import gast
import beniget
import os
import db
import builtins
import slicing.py_builtin as py_builtin
import slicing.get_if_coverage as get_if_coverage
import graph_traversal
from collections import OrderedDict
import utils
import json 
from config import LogConfig
import slicing.parser as parser
import itertools 
"""
slicing module gast and finding the match between conditional stmt logging stmt
matching: variables in conditional stmt appears in logging stmt

beniget is able to distinguish the local variables and global variables
"""


class slicer(gast.NodeVisitor):
    def __init__(self, module_node, module_name, project_name, db, call_graph, reversed_call_graph_path, project_root_dir):
        self.du = beniget.DefUseChains()
        self.du.visit(module_node)
        self.ud_chains = beniget.UseDefChains(self.du)
        self.module_name = module_name # filename in dot format
        self.project_name = project_name
        self.db_coverage = db.coverage
        self.db = db
        self.ancestors = beniget.Ancestors()
        self.ancestors.visit(module_node)
        self.builtins = dir(builtins)
        self.type_builtins = py_builtin.builtin_type_methods # applies only when dealing with object attribute like str.startswith()
        self.call_graph = call_graph
        self.if_stmt_coverage = 0
        self.project_root_dir = project_root_dir
        with open(reversed_call_graph_path) as f:
            self.reversed_call_graph = json.load(f)

        self.var_assign_map = OrderedDict()
        self.dependency = [] # class, function definition
        self.current_class_constructor = None
        

        # append parent name for class.method or inner function
        for node in gast.walk(module_node):
            if isinstance(node, gast.FunctionDef) or isinstance(node, gast.ClassDef) or isinstance(node, gast.AsyncFunctionDef):
                for child in gast.iter_child_nodes(node):
                    if isinstance(child, gast.FunctionDef) or isinstance(child, gast.AsyncFunctionDef):
                        tmp = child.name 
                        child.name = node.name+os.path.sep+tmp
        

    def get_assignment_node(self, node):
        '''
        Find the assignment node of the variable

        return True if the variable is assigned, False otherwise
        '''
        if self.get_assignment_log(node) or self.get_assignment_local(node) or self.get_assignment_caller(node):
            return True

        return False

    def has_intermediate_use(self, node, assign_lineno, pt_of_interest_lineno):
        # capture the use of the variable
        use_chains = self.ud_chains.chains[node]

        intermediate_use = None

        for use_chain in use_chains:
            for use in use_chain.users():
                parents = self.ancestors.parents(use.node)
                for d in range(len(parents)-1, -1, -1): # find the last parent that is an expression
                    # parent[d].lineno should be larget than assign_lineno and smaller than if_stmt_lineno
                    if isinstance(parents[d], gast.Subscript) and parents[d].lineno > assign_lineno and parents[d].lineno < pt_of_interest_lineno:
                        intermediate_use = parents[d]
                        break 
                    elif isinstance(parents[d], gast.Attribute) and parents[d].lineno > assign_lineno and parents[d].lineno < pt_of_interest_lineno:
                        intermediate_use = parents[d]
                        break

                if intermediate_use:
                    # check if this use is a subscript that is a target in a assignment
                    for d in range(len(parents)-1, -1, -1):
                        if isinstance(parents[d], gast.Assign) and parents[d].lineno > assign_lineno and parents[d].lineno < pt_of_interest_lineno:
                            if intermediate_use == parents[d].value:
                                intermediate_use = None
                                break

                if intermediate_use is not None:
                    return True

                    

            if isinstance(use.node, gast.Attribute):
                parents = self.ancestor.parents(use.node)
                for i in range(len(parents)-1, -1, -1): # find the last parent that is an expression
                    if isinstance(parents[i], gast.expr) and parents[i].lineno > assign_lineno and parents[i].lineno < pt_of_interest_lineno:
                        return True
                        
        
        return False
           
    def get_assignment_local(self, node):
        '''
        Find the assignments of the variable
        '''
        uses = self.ud_chains.chains[node]
        num_valid_assign = 0
        collected_assign = []
        
        for use in uses:
            try:
                parents = self.ancestors.parents(use.node)
                for parent in parents:
                    # If assign is under try caluse, skip
                    if isinstance(parent, gast.Try):
                        return False
                    
                    if isinstance(parent, gast.arguments):
                        if self.get_assignment_caller(node):
                            num_valid_assign += 1

                    if isinstance(parent, gast.Assign) and node.end_lineno > parent.end_lineno: # check lineno here to ensure the assignment is before the use
                        # check if the variable is assigned to self.attr
                        for i in gast.walk(parent.value):
                            if isinstance(i, gast.Attribute) and not self.check_attr_node(i): # var = self.attr 
                                return False

                            elif isinstance(i, gast.Name) and i.id != "self" and i.id not in self.builtins:
                                self.get_assignment_node(i)
                              
                        if self.check_covered(parent):
                            # check if there are intermediate use of the variable. If so, skip for now
                            if self.has_intermediate_use(node, parent.lineno, self.if_stmt_lineno):
                                return False
                            
                            collected_assign.append(parent)
                            num_valid_assign += 1
                        else:
                            return False
                        
            except KeyError:
                return False
            
        if num_valid_assign == len(uses):
            for assign in collected_assign:
                for child in gast.walk(assign):
                    if isinstance(child, gast.Call):
                        return False
                if node.id not in self.var_assign_map:
                    self.var_assign_map[node.id] = [gast.unparse(assign)]
                else:
                    self.var_assign_map[node.id].append(gast.unparse(assign))

        return True
    
    def not_covered_in_logRE(self, node):
        '''
        check the coverage of the node lineno in logREs
        '''
        db_ = self.db.logRE
        location = self.module_name + '@' + node.lineno.__str__()

        cursor = db_.find({'must_not_coverage': location})
        # check if the cursor is empty
        doc = cursor.next()
        if doc is not None:
            return True
        else:
            return False

    def check_covered(self, node):
        '''
        Check if the node is covered 
        '''
        db_ = self.db_coverage

        # get location of doc
        location = self.module_name + '@' + node.lineno.__str__()
        
        doc = db_.find_one({'location': location})
        if not doc:
            return False 
        if doc['covered'] == "Must":
            return True
        else:
            return False


    def get_assignment_log(self, n):
        '''
        get the value of variable from log stmt
        '''
        if not isinstance(n, gast.Name):
            return False

        log_location = ""
        
        map_lineno_log = {}

        for chain in self.ud_chains.chains[n]:
            # get the top level user of the variable
            for top_level_user in chain.users():
                if top_level_user.node.lineno < n.lineno:
                    for second_level_user in top_level_user.users():
                        # if second_level_user.node is Call node and is log 
                        if isinstance(second_level_user.node, gast.Call) and \
                            isinstance(second_level_user.node.func, gast.Attribute) and \
                            isinstance(second_level_user.node.func.value, gast.Name) and \
                            second_level_user.node.func.value.id in LogConfig.config("pattern"):
                            # check if the log stmt is under try caluse or if stmt using ancestor
                            parents = self.ancestors.parents(second_level_user.node)
                            for parent in parents:
                                if isinstance(parent, gast.Try) or isinstance(parent, gast.If):
                                    return False
                
                            map_lineno_log[second_level_user.node.lineno] = second_level_user.node

                        # var in log can be in dict, goes one more level
                        for third_level_user in second_level_user.users():
                            if isinstance(third_level_user.node, gast.Call) and \
                            isinstance(third_level_user.node.func, gast.Attribute) and \
                            isinstance(third_level_user.node.func.value, gast.Name) and \
                            third_level_user.node.func.value.id in LogConfig.config("pattern"):
                                # check if the log stmt is under try caluse or if stmt using ancestor
                                parents = self.ancestors.parents(third_level_user.node)
                                for parent in parents:
                                    if isinstance(parent, gast.Try) or isinstance(parent, gast.If):
                                        return False
                                    
                                map_lineno_log[third_level_user.node.lineno] = third_level_user.node
                        
                               
        if not map_lineno_log.keys():
            return False
        
        keys = list(map_lineno_log.keys())
        keys.sort(reverse=True)

        log_lineno = keys[0]
     
        log_node = map_lineno_log[log_lineno]

        log_constant = log_node.args[0]

        if not isinstance(log_constant, gast.Constant):
            return False

        # check if multiple variables in log stmt
        dict_var = False
        for i in log_node.args:
            if isinstance(i, gast.Dict):
                dict_var = True
        
        if dict_var:
            var_index = -1
            for i in log_node.args:
                if isinstance(i, gast.Dict):
                    for j in i.values:
                        if not isinstance(j, gast.Name):
                            continue
                        if j.id == n.id:
                            var_index = i.values.index(j)
                            break
            if var_index == -1:
                return False
        else:
            var_index = 0
            for i in log_node.args:
                if isinstance(i, gast.Name) and i.id == n.id:
                    var_index = log_node.args.index(i) - 1 # -1 because the first arg is log_constant
                    break
                var_index += 1

            if var_index == -1:
                return False

        # get the value of the variable
        possible_log_lineno = [] # log stmt can be in the same line or multiple lines
        for i in range(log_node.lineno, log_node.end_lineno+1):
            possible_log_lineno.append(i)

        for lineno in possible_log_lineno:
            log_location = "[" + self.module_name + "@" + str(lineno) + "]" # construct location component in log line

            var_values = parser.get_var_from_log(log_constant.value, log_location, var_index)

            if var_values is not None:
                for var_value in var_values:
                    if n.id not in self.var_assign_map:
                        if var_value.replace('.','',1).isdigit() or var_value == "True" or var_value == "False" or var_value == "None":
                            self.var_assign_map[n.id] = [f"{n.id}  =  {var_value}"]
                        else:
                            self.var_assign_map[n.id] = [f"{n.id}  =  '{var_value}'"]
                    else:
                        if var_value.replace('.','',1).isdigit() or var_value == "True" or var_value == "False" or var_value == "None":
                            self.var_assign_map[n.id].append(f"{n.id}  =  {var_value}")
                        else:
                            self.var_assign_map[n.id].append(f"{n.id}  =  '{var_value}'")

                return True

        return False

    def get_assignment_caller(self, node):
        '''
        var is passed in as parameter
        assignment of the variable using caller function
        '''

        """
        return True if the variable is defined in the caller function
        """

        # check parameters
        # get current function
        anc = self.ancestors.parents(node)
        cur_fn = None
        current_function_param = None

        param_index = 0
        param_id = None
        var_value = None

        for i in anc:
            if isinstance(i, gast.FunctionDef) or isinstance(i, gast.AsyncFunctionDef):
                cur_fn = i.name
                current_function_param = i.args
                break

        if cur_fn:
            # current_function_param: ast arguments node

            arg_list = current_function_param.args

            found = False

            if arg_list:
                for arg in arg_list:
                    if isinstance(arg, gast.Name) and arg.id == node.id:
                        found = True
                        param_id = arg.id
                        break
                    param_index += 1
                

            if found:
                if arg_list[0].id == 'self':
                    param_index -= 1

                if node.id == 'self':
                    return False
                
                # check if the param is defined in the caller function
                '''
                here should get the value of the param in the caller function
                '''
                var_value = self.check_caller_function(cur_fn, param_index, param_id)


   
                if not var_value:
                    return False 
                if var_value == "default_value":  
                    return False
                else:
                    if node.id not in self.var_assign_map:
                        self.var_assign_map[node.id] = [node.id + " = " + str(var_value)]
                    else:
                        self.var_assign_map[node.id].append(node.id + " = " + str(var_value))
                    return True
                

        return False
    

    def eval_if_stmt(self, expr_node):
        '''
        Eval the expression in the if statement

        expr: The expression in the if statement

        return 1 if the expression is true, 0 if the expression is false, -1 if the expression is not evaluable
        return 2 if the expression is evaluated as both true and false in different cases during system execution
        '''

        branch_selection_true = False 
        branch_selection_false = False
      
        assignment_list = []
        for value in self.var_assign_map.values():
            assignment_list.append(value)

        cartesian_product = itertools.product(*assignment_list)

        assignment_combo = next(cartesian_product)

        while assignment_combo is not None:
            for assignment in assignment_combo:
                try:
                    exec(assignment)
                except Exception as e:
                    return -1
                
            expr = gast.unparse(expr_node)
            try:
                res = eval(expr)
            except Exception as e:
                return -1
            
            if res:
                branch_selection_true = True
            else:
                branch_selection_false = True
            
            if branch_selection_true and branch_selection_false:
                return 2
            try:
                assignment_combo = next(cartesian_product)
            except StopIteration:
                break

        return 1 if branch_selection_true else 0


    

    def check_caller_function(self, cur_fn, var_position, var_id): 

        var_value = None 

        if self.project_name not in cur_fn:
            cur_fn = self.module_name + "." + cur_fn

        cur_fn_dot = cur_fn.replace(os.path.sep, '.')
        
        if not cur_fn_dot in self.reversed_call_graph:
            return 

        callers = self.reversed_call_graph[cur_fn_dot]

        

        if callers:
            for caller in callers:
                # check if the fn call is executed 

                # check if the function call executed 
                caller_ast_path = os.path.join("log2cov-out/AST", self.project_name, *caller.split('.')) + ".txt"
                caller_ast = graph_traversal.get_ast(caller_ast_path)
                if caller_ast is None:
                    continue
                import slicing.function_locator as fl
                cur_fn_ast_path = os.path.join("log2cov-out/AST", self.project_name, cur_fn.replace('.', os.path.sep)) + ".txt"
                if not os.path.exists(cur_fn_ast_path) or not os.path.exists(caller_ast_path):
                    continue
                locator = fl.Locator(cur_fn_ast_path, self.db_coverage)
                locator.visit(caller_ast)
                fn_call_valid = locator.caller_valid

                # go to caller module, go to the function call line, 

                if fn_call_valid:
                    caller_module_name = locator.module_name
                    caller_lineno = locator.fn_call_lineno
                    caller_module_path = os.path.join(self.project_root_dir, *caller_module_name.split('.')) + ".py"

                    if not os.path.exists(caller_module_path):
                        # try init file
                        caller_module_path = os.path.join(self.project_root_dir, *caller_module_name.split('.'), "__init__.py")
                        if not os.path.exists(caller_module_path):
                            print(f"caller module path not exist: {caller_module_path}")
                            continue

                    with open(caller_module_path) as f:
                        code = f.read()

                    try:
                        caller_module_gast = gast.parse(code)
                    except SyntaxError:
                        print(f"SyntaxError in parsing {caller_module_path} to ast")
                        return 

                    caller_slicer = fl.Caller_Slicer(caller_module_gast, caller_lineno, var_position, var_id,
                        caller_module_name, self.project_name, self.db, self.reversed_call_graph, self.project_root_dir
                        )
                    caller_slicer.visit(caller_module_gast)
                    if caller_slicer.caller_slicing_valid:
                        # var is defined in the caller function
                        var_value = caller_slicer.param_value
                        break
                    if caller_slicer.use_default:
                        var_value = "default_value"
                        break
                
        
        return var_value
                
                

    def visit_If(self, node):
        """
        check if meet the creteria:
        1. Leads to May coverage

        2. If the test node is Boolop, and the op == Or(), ok if one of the var appears in the logging stmt
           Otherwise, all variables in the if stmt should appeared in logging stmt
        """ 

        # check if this if stmt results in May Coverage
        db_ = self.db_coverage

        

        # get location of doc
        location = self.module_name + '@' + node.lineno.__str__()

        doc = db_.find_one({'location': location})
        if not doc:
            return 
        
        if doc and doc['covered'] != "Must":
            return
           
        # '''
        # get resolvable may coverage
        # '''
        # branch_selection = True
        
        # fun_ast_location = self.get_fn_ast_path(node)
        # if not fun_ast_location:
        #     print(f"AST file not found: {fun_ast_location}")
        #     return

        # if not os.path.exists(fun_ast_location):
        #     # remove the dir __init__ from the fun_ast_location
        #     f = fun_ast_location.rsplit(".",1)[0].split(os.path.sep)
        #     f_no_init = [i for i in f if i != '__init__']
        #     path_without_init = os.path.join(*f_no_init) + ".txt"   

        #     if not os.path.exists(path_without_init):
        #         return
        #     else:
        #         fun_ast_location = path_without_init
    
        
        # ast = graph_traversal.get_ast(fun_ast_location)

        # lineno = node.lineno
        # coverage = get_if_coverage.Coverage_If(target_lineno=lineno, module_name=self.module_name, db=self.db, branch_selection=branch_selection) # input lineno
        # coverage.visit(ast) #input function ast

        
        """
        Get valid if coverage
        """
        name_nodes = set() # contains only locally defined variable's Name nodes

        # init for the current if stmt
        self.op_is_or = False
        self.if_stmt_lineno = node.lineno

        # find name nodes in the test node of if stmt
        # if test node is Name node, no need to find compare node
        if isinstance(node.test, gast.Name):
            # check if this name node is locally defined
            if node.test.id not in self.builtins:
                name_nodes.add(node.test)
    
        # if test node is BoolOp node check if the op is Or
        elif isinstance(node.test, gast.BoolOp): # test is multiple conditions
            if isinstance(node.test.op, gast.Or):
                self.op_is_or = True
                # list of set of name nodes, each list contains name nodes in one compare node
                list_of_name_nodes = []
                for compare in node.test.values:
                    name_nodes_in_compare = set()
                    for n in gast.walk(compare):
                        if isinstance(n, gast.Attribute) and not self.check_attr_node(n):
                            continue
                        if isinstance(n, gast.Name) and n.id not in self.builtins and n.id != "self":
                            name_nodes_in_compare.add(n)
                        

                    list_of_name_nodes.append(name_nodes_in_compare)      
            else:
                for n in gast.walk(node.test):
                    if isinstance(n, gast.Name) and n.id not in self.builtins and n.id != "self":
                        name_nodes.add(n)
                    if isinstance(n, gast.Attribute) and not self.check_attr_node(n):
                        return

        elif isinstance(node.test, gast.Compare):

            for n in gast.walk(node.test):
                if isinstance(n, gast.Name) and n.id not in self.builtins and n.id and n.id != "self":
                    name_nodes.add(n)
                if isinstance(n, gast.Attribute) and not self.check_attr_node(n):
                    return
                    
        # if the test node is attribute, check the attribute
        elif isinstance(node.test, gast.Attribute) and not self.check_attr_node(node.test):
            return

        else:
            # print("test node is not Name or BoolOp or Compare", self.module_name, node.lineno)
            return

        """
        check if var is defined
        """

        # (re)initialize the var assignment map for the current if stmt
        self.var_assign_map = OrderedDict()

        if self.op_is_or: # use list_of_name_nodes
            op_valid = False

            if len(node.test.values) != len(list_of_name_nodes):
                # print("len(node.test.values) != len(list_of_name_nodes)")
                return 

            for i in range(len(node.test.values)):
                compare = node.test.values[i]
                n_nodes_of_compare = list_of_name_nodes[i]
                for n in n_nodes_of_compare:
                    self.get_assignment_node(n) 
                    
                
                if_stmt_eval_result = self.eval_if_stmt(compare)
                if if_stmt_eval_result == -1 :

                    return
                else:
                    op_valid = True
                    break

            if not op_valid:
                return
            

            
        else: # use name_nodes
            for n in name_nodes: # ******* 
                self.get_assignment_node(n) 
                
            for n in name_nodes:
                if n.id not in self.var_assign_map:
                    return
            
            if_stmt_eval_result = self.eval_if_stmt(node.test)
            if if_stmt_eval_result == -1 :
                # print(f"not evaluable if stmt: {location}")
                return
        
        if if_stmt_eval_result == 2:
            branch_selections = [True, False]
        else:
            branch_selections = [True] if if_stmt_eval_result == 1 else [False]
        
        fun_ast_location = self.get_fn_ast_path(node)
        if not fun_ast_location:
            print(f"AST file not found: {fun_ast_location}")
            return

        if not os.path.exists(fun_ast_location):
            # remove the dir __init__ from the fun_ast_location
            f = fun_ast_location.rsplit(".",1)[0].split(os.path.sep)
            f_no_init = [i for i in f if i != '__init__']
            path_without_init = os.path.join(*f_no_init) + ".txt"   

            if not os.path.exists(path_without_init):
                return
            else:
                fun_ast_location = path_without_init
    
        
        ast = graph_traversal.get_ast(fun_ast_location)
        lineno = node.lineno

        for branch_selection in branch_selections:
            coverage = get_if_coverage.Coverage_If(target_lineno=lineno, module_name=self.module_name, db=self.db, branch_selection=branch_selection) # input lineno
            coverage.visit(ast) #input function ast
            

                                                  
        self.generic_visit(node)
    
    def check_attr_node(self, node):
        """
        check if the attribute node
        """
        return False 
    

 
    
    def get_fn_ast_path(self, node):
        '''
        get the path from the module to the function of the node
        '''

        anc = self.ancestors.parents(node)
        cur_fn_name = None
        for n in anc:
            if isinstance(n, gast.FunctionDef) or isinstance(n, gast.AsyncFunctionDef):
                cur_fn_name = n.name
                break

        if not cur_fn_name:
            return 

        fn_ast_path = os.path.join("log2cov-out/AST", self.project_name, *self.module_name.split('.'), cur_fn_name) + '.txt'
  
        return fn_ast_path





def process_file(source_filename, project_name, db_name, project_root_dir, reversed_call_graph_path, call_graph_path):
    db_ = db.Connect.get_connection().get_database(db_name)
    with open(source_filename) as f:
        code = f.read()
    try:
        module_ast = gast.parse(code)

    except SyntaxError:
        print(f"SyntaxError in parsing {source_filename} to ast")
        return 0

    module_name = utils.mod_path_dot(source_filename, project_root_dir) # module name in dot format
    if module_name.endswith("__init__"):
            module_name = ".".join(module_name.split(".")[:-1])

    s = slicer(module_ast, module_name, project_name, db_, call_graph_path, reversed_call_graph_path, project_root_dir)
    s.visit(module_ast)

    return s.if_stmt_coverage



def test_local_slicing(file_path):

    c = process_file(file_path, "nova", 27000, "/home/x439xu/evaluation/projects/salt", "log2cov-out/reversed_call_graph/salt.json", "log2cov-out/call_graph/salt.json")
    print(c)


  

