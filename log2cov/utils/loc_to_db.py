import ast



class module_visitor(ast.NodeVisitor):
    def __init__(self, module_name):
      self.module_name = module_name
      self.docs = []
      self.lineno = set()

    def get_docs(self):
        return self.docs

    def generic_visit(self, node):
        if hasattr(node,"lineno"):
            if node.lineno not in self.lineno:
                doc = {
                    "location" : f"{self.module_name}@{node.lineno}"
                }
               
                self.docs.append(doc)
                self.lineno.add(node.lineno)

        return super().generic_visit(node)