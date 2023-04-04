import ast
import db
import pymongo


class condition_visitor(ast.NodeVisitor):
    def __init__(self, module_name, condition_lineno):
        self.module_name = module_name
        self.condition_lineno = condition_lineno # the line number of the condition statement
        self.must = []
        self.may = []
        self.lineno = set()
      
    def generic_visit(self, node):
        if hasattr(node,"lineno"):
            if node.lineno not in self.lineno:
                if node.lineno == self.condition_lineno:
                    location = f"{self.module_name}@{node.lineno}"
                    self.must.append(location)
                else:
                    location = f"{self.module_name}@{node.lineno}"
                    self.may.append(location)

                self.lineno.add(node.lineno)
        return super().generic_visit(node)

class uncondition_visitor(ast.NodeVisitor):
    def __init__(self, module_name):
        self.module_name = module_name
        self.must = []
        self.lineno = set()
      
    def generic_visit(self, node):
        if hasattr(node,"lineno"):
            if node.lineno not in self.lineno:
                location = f"{self.module_name}@{node.lineno}"
                self.must.append(location)

                self.lineno.add(node.lineno)
        return super().generic_visit(node)


def global_statements_to_db(tree, module_name, global_coverage_db):
    """
    Get lineno of statements in global scope for the module
    And save them to the global coverage db.

    schema of global coverage db:
    {
        "module_name" : "t.t",
        "must_coverage" : ["module_name@lineno", ...],
        "may_coverage" : ["module_name@lineno", ...],
    }

    """
    

    module_must_coverage = []
    module_may_coverage = []

    collection = global_coverage_db

    # iterate top level nodes of the the module tree
    for node in tree.body:
        # skip FunctionDef because statements inside are at not global level
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            continue

        # add class definition statement to module May coverage
        elif isinstance(node, ast.ClassDef):
            location = f"{module_name}@{node.lineno}"
            module_may_coverage.append(location)

        else:
            # conditional statements and unconditional statements
            if isinstance(node, ast.If) or isinstance(node, ast.Try): 
                visitor = condition_visitor(module_name, node.lineno)
                visitor.visit(node)
                module_may_coverage += visitor.may
                module_must_coverage += visitor.must 
            else:
                visitor = uncondition_visitor(module_name)
                visitor.visit(node)
                module_must_coverage += visitor.must
            
    # constrcut the document
    doc = {
        "module_name" : module_name,
        "must_coverage" : module_must_coverage,
        "may_coverage" : module_may_coverage,
    }

    try:

        collection.insert_one(doc)
    except pymongo.errors.DuplicateKeyError:
        pass
   


