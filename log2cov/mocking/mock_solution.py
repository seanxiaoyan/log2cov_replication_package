import utils
import ast


# def find_patch(source_filename):
#     """
#     Find the usage of patch() in the source file.
#     """
#     tree = utils.parse_ast(source_filename)
    
#     fnDef_list = utils.get_all_fn_def(tree) 
#     for f in fnDef_list:
#         file_name_dot = utils.path_to_dot_notation(source_filename)
#         caller_name = utils.form_caller_name(file_name_dot,f.name)
#         ast_modifier = ast_patch_finder()
#         method = ast_modifier.visit(f)
        



# class ast_patch_finder(ast.NodeVisitor):
#     def __init__(self, module_name, condition_lineno):
#         self.module_name = module_name
#         self.condition_lineno = condition_lineno # the line number of the condition statement
#         self.must = []
#         self.may = []
#         self.lineno = set()
      
#     def generic_visit(self, node):
#         if hasattr(node,"lineno"):
#             if node.lineno not in self.lineno:
#                 if node.lineno == self.condition_lineno:
#                     location = f"{self.module_name}@{node.lineno}"
#                     self.must.append(location)
#                 else:
#                     location = f"{self.module_name}@{node.lineno}"
#                     self.may.append(location)

#                 self.lineno.add(node.lineno)
#         return super().generic_visit(node)

    
#     def visit_If(self, node):
#         utils.get_all_fn_def(node)




if __name__ == "__main__":
    test_file = "../salt/tests/unit/cloud/clouds/test_proxmox.py"
    test_file = "example_mock.py"
    tree = utils.parse_ast(test_file)

    print(ast.dump(tree, include_attributes=True, indent=4))
