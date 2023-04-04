import json
import os
import ast

class ast_proceeser(ast.NodeTransformer):
    def __init__(self, json_filename, caller_name, project_name):
        '''
        module_name: dot notation of the abs path to a module
        '''
        with open(json_filename) as f:
            data = json.load(f)
        self.json = data
        self.caller_name = caller_name
        self.lineno = set() # record lineno added to the coverage db
        self.project_name = project_name

    # def get_docs(self):
    #     return self.db_docs

    def get_ast_path(self, callee_name):
        #return AST path of callee
        callee_full_name = callee_name
        if callee_name:

            
            if self.caller_name in self.json:
                l = self.json[self.caller_name] # get list of callees

                # check if there exists duplicate callee name
                l_ = [i.split(".")[-1] for i in l]
                l_set = set(l_)

                if len(l_) == len(l_set):
                    # if there are no duplciate method name
                    callee_name = callee_name.split(".")[-1]
                    for item in l:
                        if callee_name in item:
                            # e.g. nova.cache_utils.get_client -> log2cov-out/AST/nova/nova/cache_utils/get_client.txt
                            names = item.split('.')
                           
                            callee_full_name = os.path.join("log2cov-out", "AST", self.project_name, *names) + ".txt"
                        # print("------ caller id: {}; callee id: {}   ->   {} ------".format(self.caller_name,callee_name,callee_full_name))
                else:
                    for item in l:
                        if callee_name in item:
                            
                            names = item.split('.')

                            callee_full_name = os.path.join("log2cov-out", "AST", self.project_name, *names) + ".txt"
            # else:
            #     print(self.caller_name)      
        return callee_full_name

    def visit_Call(self, node):
        # Using caller name and callee name to get callee full name
        # e.g. caller name： nova.availability_zones._get_cache
        #       callee name： get_client
        #       callee full name -> nova.cache_utils.get_client

        # check if the function defined in current module
        if isinstance(node.func, ast.Name):
            callee_name = node.func.id
            node.func.id = self.get_ast_path(callee_name)

        # check if the function defined in other internal modules:
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id != "self":
                    callee_name = node.func.value.id +'.' + node.func.attr
                else:
                    callee_name = node.func.attr
            elif isinstance(node.func.value, ast.Attribute):
                callee_name = node.func.value.attr +'.' + node.func.attr
            else:
                callee_name = node.func.attr
            node.func.attr = self.get_ast_path(callee_name)
        self.generic_visit(node)
        return node
    
    # def generic_visit(self, node):
    #     if hasattr(node,"lineno"):
    #         if node.lineno not in self.lineno:
 
    #             doc = {
    #                 "location" : f"{self.module_name}@{node.lineno}",
    #                 "covered" : 'No'
    #             }
    #             self.db_docs.append(doc)
    #             self.lineno.add(node.lineno)


    #     return super().generic_visit(node)