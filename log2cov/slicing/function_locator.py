import ast 
import gast 
import beniget
import builtins
from collections import OrderedDict
import os 
import logging 
import graph_traversal
import slicing.py_builtin as py_builtin
from config import LogConfig
import slicing.parser as parser
class Locator(ast.NodeVisitor):
    def __init__(self, callee_name, db):
        self.callee_name = callee_name
        self.caller_valid = False
        self.module_name = None
        self.db_coverage = db
        self.fn_call_lineno = None

    def visit_FunctionDef(self, node):
        self.module_name = node.name
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        if self.caller_valid:
            return


        if isinstance(node.func, ast.Attribute):
            if node.func.attr == self.callee_name:
                location = self.module_name + "@" + str(node.lineno)
                doc = self.db_coverage.find_one({'location': location})
                if doc and doc['covered']== 'Must':
                    self.caller_valid = True
                    self.fn_call_lineno = node.lineno
        
        elif isinstance(node.func, ast.Name):
            if node.func.id == self.callee_name:
                location = self.module_name + "@" + str(node.lineno)
                doc = self.db_coverage.find_one({'location': location})
                if doc and doc['covered']== 'Must':
                    self.caller_valid = True
                    self.fn_call_lineno = node.lineno
        
        else:
            self.generic_visit(node)


class Caller_Slicer(gast.NodeVisitor):
    '''
    Get the value of the variable from the caller function
    '''
 

    def __init__(self, module_node, call_lineno, param_position, param_id, 
                module_name='a', project_name="p", db=None, 
                reversed_call_graph=None, project_root_dir=None):

        self.du = beniget.DefUseChains()
        self.du.visit(module_node)
        self.ud_chains = beniget.UseDefChains(self.du)
        self.module_name = module_name# filename in dot format
        self.project_name = project_name
        if db is not None:
            self.db_coverage = db.coverage
        self.db = db
        self.ancestors = beniget.Ancestors()
        self.ancestors.visit(module_node)
        self.builtins = dir(builtins)
        self.type_builtins = py_builtin.builtin_type_methods # applies only when dealing with object attribute like str.startswith()

        self.current_function = OrderedDict() # { function_ast_path: function_param }
        self.project_root_dir = project_root_dir
   
        self.reversed_call_graph = reversed_call_graph
        self.caller_slicing_valid = False
        self.call_lineno = call_lineno
        self.param_position = param_position
        self.param_id = param_id
        self.var_assign_map = OrderedDict()
        self.param_value = None
        self.use_default = False


        # append parent name for class.method or inner function
        for node in gast.walk(module_node):
            if isinstance(node, gast.FunctionDef) or isinstance(node, gast.ClassDef) or isinstance(node, gast.AsyncFunctionDef):
                for child in gast.iter_child_nodes(node):
                    if isinstance(child, gast.FunctionDef ) or isinstance(child, gast.AsyncFunctionDef):
                        tmp = child.name 
                        child.name = node.name+os.path.sep+tmp
        
               
    def visit_FunctionDef(self, node):
        # print the name of function
        fn_path = os.path.join(*self.module_name.split('.'), node.name)
        # fn_params = [arg.id for arg in node.args.args]
        self.current_function[fn_path] = node.args # fn_name to argument object
        
        self.generic_visit(node)
        if len(self.current_function) == 0:
            raise Exception(f"current_function is empty, functionDef lineno: {node.lineno} ")
        self.current_function.popitem()
    
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

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
                            if self.has_intermediate_use(node, parent.lineno, self.call_lineno):
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

                # go to caller function ast, find the function call line number
           
                caller_ast_path = os.path.join("log2cov-out/AST", self.project_name, *caller.split('.')) + ".txt"
                caller_ast = graph_traversal.get_ast(caller_ast_path)
                if caller_ast is None:
                    continue
                
                cur_fn_ast_path = os.path.join("log2cov-out/AST", self.project_name, cur_fn) + ".txt"
                if not os.path.exists(cur_fn_ast_path) or not os.path.exists(caller_ast_path):
                    continue
                locator = Locator(cur_fn_ast_path, self.db_coverage)
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

                    
                    c_slicer = Caller_Slicer(caller_module_gast, caller_lineno, var_position, var_id,
                        caller_module_name, self.project_name, self.db, self.reversed_call_graph, self.project_root_dir
                        )

                    c_slicer.visit(caller_module_gast)
                    if c_slicer.caller_slicing_valid:
                        # var is defined in the caller function
                        var_value = c_slicer.param_value
                        break
                    if c_slicer.use_default:
                        var_value = "default_value"
                        break
        
        return var_value
                
                

    def visit_Call(self, node):
        '''
        get the arg value, from args or from keywords
        '''

        if node.lineno == self.call_lineno:
            self.param_value = None
            self.var_assign_map = OrderedDict() # reinitialze var_assign_map

            # decide value from args or keywords

            if node.keywords:
                for keyword in node.keywords:
                    if keyword.arg == self.param_id:
                        value_str = gast.unparse(keyword.value)
                        try:
                            exec("self.param_value = " + value_str)
                        except NameError:
                            return False
                        except AttributeError:
                            return False
                        break
       
            else:
                # not found val in keywords, try to find in args
                if self.param_position >= len(node.args):
                    # did not provide arg, use default value
                    self.use_default = True
                    return
                
                param_val_node = node.args[self.param_position]

                for i in gast.walk(param_val_node):
                    if isinstance(i, gast.Attribute) and not self.check_attr_node(i): # var = self.attr 
                        return False

                    elif isinstance(i, gast.Name) and i.id != "self" and i.id not in self.builtins:
                        self.get_assignment_node(i)
                        # if not found_assign_i:
                        #     return False
               
                assigned = self.get_var_value(param_val_node)
                if assigned == -1:
                    self.param_value = None

            return 
        else:
            self.generic_visit(node)
    
    def get_var_value(self, param_val_node):
        for assign_expr in self.var_assign_map.values():
            try:
                exec(assign_expr)
            except Exception as e:
                return -1 

        try:
            param_val_expr_str = gast.unparse(param_val_node)
            exec("self.param_value = " + param_val_expr_str)
        except Exception as e:
            return -1
            
    def get_assignment_node(self, node):
        '''
        Find the assignment node of the variable

        return True if the variable is assigned, False otherwise
        '''
        if self.get_assignment_log(node) or self.get_assignment_local(node) or self.get_assignment_caller(node):
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


                # if not var_value:
                #     # check if the param has default value, if so return True
                #     if param_index < len(current_function_param.defaults) and current_function_param.defaults[param_index]:
                #         default = current_function_param.defaults[param_index]
                #         if isinstance(default, gast.Constant):
                #             var_value = default.value

                if not var_value:
                    return False 
                if var_value == "default_value":
                    # if param_index < len(current_function_param.defaults) and current_function_param.defaults[param_index]:
                    #     default = current_function_param.defaults[param_index]
                    #     if isinstance(default, gast.Constant):
                    #         var_value = default.value
                    #         if node.id not in self.var_assign_map:
                    #             self.var_assign_map[node.id] = [node.id + " = " + str(var_value)]
                    #         else:
                    #             self.var_assign_map[node.id].append(node.id + " = " + str(var_value))
                            
                    #         return True
                    
                    return False
                else:
                    if node.id not in self.var_assign_map:
                        self.var_assign_map[node.id] = [node.id + " = " + str(var_value)]
                    else:
                        self.var_assign_map[node.id].append(node.id + " = " + str(var_value))
                    return True
                

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
    
    def check_attr_node(self, node):
        return False
       
if __name__ == "__main__":
    # (self, module_node, module_name, project_name, db, 
    # reversed_call_graph, project_root_dir, call_lineno, param_position)


    path = "test.py"
    with open(path, 'r') as f:
        code = f.read()
    module_gast = gast.parse(code)
    c = Caller_Slicer(module_gast, 3, 0)
    c.visit(module_gast)

    print(c.caller_slicing_valid)