
from utils.get_ast import parse_ast 
import json
import ast
import os 

class ast_patch_finder(ast.NodeVisitor):
    def __init__(self, module_path):
        self.callee_list = set()
        self.alias = {}
        self.module_name = ""
        self.module_path = module_path


    def visit_ImportFrom(self, node):
        # construct full import name
        if node.module is None:
            import_name = ""
        else:
            import_name = node.module
            
        for name in node.names:
            import_name = import_name + "." + name.name
     
            if name.asname is not None:
                self.alias[name.asname] = import_name
            else:
                self.alias[name.name] = import_name

        self.generic_visit(node)
  
        
    # general patch() function call
    def visit_Call(self, node):
        try:
            if hasattr(node, "func"):
                if isinstance(node.func, ast.Name):
                    if node.func.id == "patch":
                        self.callee_list.add(node.args[0].value)
        except Exception as e:
            pass
        return super().generic_visit(node)




    # patch() as decorator
    def visit_FunctionDef(self, node):
        try:

            if hasattr(node, "decorator_list"):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name):
                            if decorator.func.id == "patch":
                                self.callee_list.add(decorator.args[0].value)
                                break
                        elif isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == "patch":
                                self.callee_list.add(decorator.args[0].value)
                                break
                            elif decorator.func.attr == "object" and decorator.func.value.attr == "patch":
                                dependency_name = ""
                                for arg in decorator.args:
                                    dependency_name = dependency_name + '.' + ast.unparse(arg)
                                dependency_name = dependency_name.replace("'","") # remove the single quotes
                                dependency_name = dependency_name.strip(".") # remove the first dot
                                first_component = dependency_name.split(".")[0]
                                if first_component in self.alias:
                                    dependency_name = dependency_name.replace(first_component, self.alias[first_component])

                                self.callee_list.add(dependency_name)
                                break
        except Exception as e:
            pass
                   
        return super().generic_visit(node)
    # patch() as context manager 
    def visit_withitem(self, node):
        try:

            if hasattr(node, "context_expr"):
                if isinstance(node.context_expr, ast.Call):
                    # with patch() -> find Constant
                    if isinstance(node.context_expr.func, ast.Name):
                        if node.context_expr.func.id == "patch":
                            self.callee_list.add(node.context_expr.args[0].value)

                    # with patch.object()
                    elif isinstance(node.context_expr.func, ast.Attribute):
                        if isinstance(node.context_expr.func.value, ast.Name):
                            if node.context_expr.func.value.id == "patch":
                                self.callee_list.add(node.context_expr.args[0].id
                                +"." + node.context_expr.args[1].value)
        except Exception as e:
            pass
        


        return super().generic_visit(node)



def find_patching(source_filename):
    """
    find usage of unittest.mock.patch in the source file
    """
    tree = parse_ast(source_filename) # an ast tree for the source file
    patch_finder= ast_patch_finder(source_filename)
    patch_finder.visit(tree)
    return patch_finder.callee_list



def remove_callee(list_callee, project_name, call_graph_path):
    """
    remove the callees from call graph
    """
    # load call graph json -> dict
    with open(call_graph_path) as f:
        data = json.load(f)

    for callee in list_callee:

        if callee not in data:
            continue
        
        # search for callee in the call graph values
        for caller in data.keys():
            if callee in data[caller]:
                data[caller].remove(callee)

    # save updated call graph dict -> json
    with open(call_graph_path, 'w') as f:
        json.dump(data, f,indent=4)


    # Also remove the callee AST files
    for callee in list_callee:
        if isinstance(callee, str):
            name_split = callee.split(".")
            callee_ast_path = "log2cov-out/AST/"  + os.path.join(project_name, *name_split) + ".txt"
            if os.path.exists(callee_ast_path):
                os.remove(callee_ast_path)
                print("removed", callee_ast_path)
            else:
                # remove "/__init__"
                callee_ast_path = callee_ast_path.replace("/__init__.txt", ".txt")
                if os.path.exists(callee_ast_path):
                    os.remove(callee_ast_path)
                    print("removed", callee_ast_path)
                else:
                 print("not found", callee_ast_path)
    
