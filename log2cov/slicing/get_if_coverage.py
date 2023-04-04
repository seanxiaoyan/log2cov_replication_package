import ast
import graph_traversal
import os
import pymongo
"""
given the if stmt location, count the number of statement covered by the if stmt
"""
class Line_Marker(ast.NodeVisitor):
    '''
    Mark may-covered lines in condition blocks
    '''
    def __init__(self, module_name, branch_selection, db_coverage, db_resolved_may):
        self.marked_lines = set()
        self.branch_selection = branch_selection
        self.module_name = module_name
        self.db_coverage = db_coverage
        self.db_resolved_may = db_resolved_may
        self.function_calls = set()

    def generic_visit(self, node):
        if hasattr(node, "lineno") and node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return super().generic_visit(node)

    def visit_For(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return

    def visit_If(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return
    
    def visit_ExceptHandler(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return 
    
    def visit_Try(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return
    
    def visit_Raise(self, node):
        return 

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and os.path.exists(node.func.attr):
            self.function_calls.add(node.func.attr)
        elif isinstance(node.func, ast.Name) and os.path.exists(node.func.id):
            self.function_calls.add(node.func.id)
        self.generic_visit(node)

class Coverage_If(ast.NodeVisitor):
    def __init__(self, target_lineno, module_name, db, branch_selection, mark_no = False): # db is the database, need to get collection
        self.docs_to_insert = []
        self.counter = {}
        self.target_lineno = target_lineno
        self.function_calls = set()
        self.inside_target_block = False
        self.module_name = module_name
        self.branch_selection = branch_selection
        self.db_coverage = db.coverage
        self.db_resolved_may = db.resolved_may
        self.db = db
        self.mark_no = mark_no
  
    def visit_If(self, node):
        if node.lineno == self.target_lineno:
            if self.branch_selection == True:
                Marker = Line_Marker(self.module_name, True, self.db_coverage, self.db_resolved_may)
                for i in node.body:
                    Marker.visit(i)

                # process function calls 
                for callee_name in Marker.function_calls:
                    v = Coverage_Fn(function_name = callee_name, db=self.db, branch_selection = True)
                    v.visit(graph_traversal.get_ast(callee_name))

                Marker = Line_Marker(self.module_name, False, self.db_coverage, self.db_resolved_may)
                for i in node.orelse:
                    Marker.visit(i)
                
                for callee_name in Marker.function_calls:
                    v = Coverage_Fn(function_name = callee_name, db=self.db, branch_selection = False)
                    v.visit(graph_traversal.get_ast(callee_name))

            else:
                Marker = Line_Marker(self.module_name, False, self.db_coverage, self.db_resolved_may)
                for i in node.body:
                    Marker.visit(i)

                for callee_name in Marker.function_calls:
                    v = Coverage_Fn(function_name = callee_name, db=self.db, branch_selection = False)
                    v.visit(graph_traversal.get_ast(callee_name))

                if self.mark_no == False:
                    Marker = Line_Marker(self.module_name, True, self.db_coverage, self.db_resolved_may)
                else:
                    Marker = Line_Marker(self.module_name, False, self.db_coverage, self.db_resolved_may)

                for i in node.orelse:
                    Marker.visit(i)

                for callee_name in Marker.function_calls:
                    if self.mark_no == False:
                        v = Coverage_Fn(function_name = callee_name, db=self.db, branch_selection = True)
                    else:
                        v = Coverage_Fn(function_name = callee_name, db=self.db, branch_selection = False)
                    v.visit(graph_traversal.get_ast(callee_name))


        else:
            self.generic_visit(node)
       
    


def check_line(module_name, lineno, branch_selection, db_coverage, db_reloved_may):
    ''' 
    resolve line coverage based on branch selection
    '''
    if not module_name:
        return False
    if branch_selection:
        covered = 'Must'
    else:
        covered = 'No'

    location = module_name + '@' + lineno.__str__()
    doc = db_coverage.find_one({'location': location})
    if doc and doc['covered'] == 'May':
        try:
            if covered == 'Must':
                db_reloved_may.update_one({'location': location}, {'$set': {'covered': 'Must'}}, upsert=True)

            else:
                db_reloved_may.insert_one({'location': location, 'covered': covered})

        except pymongo.errors.DuplicateKeyError:
            pass


    return




# get the count of statement covered by an AST Node 
class Coverage_Fn(ast.NodeVisitor):
    def __init__(self, function_name, db, branch_selection, call_stack=None):
        self.marked_lines = set() # count the number of statement covered by the current function
        if call_stack:
            self.call_stack = call_stack
        else:
            self.call_stack = set([function_name])
        self.db_coverage = db.coverage
        self.db_counted_fn = db.counted_fn
        self.db_resolved_may = db.resolved_may
        self.db = db
        self.branch_selection = branch_selection
        self.module_name = None
        self.docs_to_insert = []

    def visit_FunctionDef(self, node):
      self.fn_def_lineno = node.lineno
      self.module_name = node.name # functiondef node name is actually its module name in our processed AST
      self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def generic_visit(self, node):
        if hasattr(node,"lineno") and node.lineno not in self.marked_lines and node.lineno != self.fn_def_lineno:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)

        return super().generic_visit(node)


    # visit the function call, check if the function call id or attr is a valid os path
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and os.path.exists(node.func.attr):
            if not node.func.attr in self.call_stack:
                self.call_stack.add(node.func.attr)
                ast_path = node.func.attr
                self.process_file(ast_path, self.call_stack)
                self.call_stack.remove(node.func.attr)

        elif isinstance(node.func, ast.Name) and os.path.exists(node.func.id):
            if not node.func.id in self.call_stack:
                self.call_stack.add(node.func.id)
                ast_path = node.func.id
                self.process_file(ast_path, self.call_stack)
                self.call_stack.remove(node.func.id)

        self.generic_visit(node)
    

    "Ignore the following nodes since they are conditional blocks"
    def visit_For(self, node):
        return
    def visit_ExceptHandler(self, node):
        return 
    def visit_If(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return
    def visit_Try(self, node):
        if node.lineno not in self.marked_lines:
            check_line(self.module_name, node.lineno, self.branch_selection, self.db_coverage, self.db_resolved_may)
            self.marked_lines.add(node.lineno)
        return
    
    def process_file(self, ast_path, stack):
        if not os.path.exists(ast_path):
            print("ast path not found: ", ast_path)
            return 
        
        # if function has been counted already
        if function_counted(ast_path, self.db_counted_fn):
            return 

        else:
            tree = graph_traversal.get_ast(ast_path)
            visitor = Coverage_Fn(ast_path, db = self.db, branch_selection = self.branch_selection, call_stack=stack)
            visitor.visit(tree)

            return 
        


def function_counted(location, db_counted_fn):
    """
    check if the location is already counted
    if not, add it to the collection

    Return False if the location already exists
    Return True if the location is added
    """
    try:
        db_counted_fn.insert_one({'location': location})
        return True
    except pymongo.errors.DuplicateKeyError:
        return False




  