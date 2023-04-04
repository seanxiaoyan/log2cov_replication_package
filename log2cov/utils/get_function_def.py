import ast
import sys
import os

class nested_function_remover(ast.NodeTransformer):
    def __init__(self ):
      super().__init__()
      self.inner = False
      
    def visit_FunctionDef(self, node):
        if(self.inner):
            return None
        else:
            self.inner = True
            self.generic_visit(node)
            return node
    def visit_AsyncFunctionDef(self, node):
        if(self.inner):
            return None
        else:
            self.inner = True
            self.generic_visit(node)
            return node
class fnDef_getter(ast.NodeVisitor):
    def __init__( self ):
      super().__init__()
      self.fnDef_list = []
      
      
    
    def visit_FunctionDef(self, node):
        self.fnDef_list.append(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)


def get_all_fn_def(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef) or isinstance(node, ast.AsyncFunctionDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef) or isinstance(child, ast.AsyncFunctionDef):
                    tmp = child.name 
                    child.name = node.name+'.'+tmp

    getter = fnDef_getter()
    getter.visit(tree)
    functionDef_list = getter.fnDef_list

    list_to_return = []

    for fnDef in functionDef_list:
        remover = nested_function_remover()
        new_fnDef = remover.visit(fnDef)
        list_to_return.append(new_fnDef)


    return list_to_return
