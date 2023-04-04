import ast
import os 
import utils
import db 
import pymongo 



def parse_ast(filename):
    with open(filename, "rt") as file:
        try:
            res = ast.parse(file.read(), filename=filename)
            return res
        except SyntaxError as e:
            pass 


def write_to_file(func_path_dot, ast_content, project_name):
    # remove __init__ from the filename to agree with the call graph naming convention
    split = func_path_dot.split(".")
    
    output_name = os.path.join("log2cov-out/AST", project_name, *split) + ".txt"
    dirname = os.path.dirname(output_name)
    try:
        os.makedirs(dirname)
    except FileExistsError:
        pass
    
   
    output_file = open(output_name, 'w')
    output_file.write(ast_content)
    output_file.close()


def construct_ast(func, mod_path_dot, project_name):
    if ast.dump(func,include_attributes=True):
        func_name = func.name # the function name
        # replace the func.name to module path dot notation
        func.name = mod_path_dot
        ast_content = (ast.dump(func,include_attributes=True, indent=4)+'\n') 
        func_path_dot = mod_path_dot + "." + func_name
        write_to_file(func_path_dot, ast_content, project_name) 



def form_caller_name(filename, function_name):
    '''
    notation: dot notation of the module
    function_name: name of the function
    caller_name: dot notation of the module + function name
        e.g: nova.availability_zones + get_availability_zones -> nova.availability_zones.get_availability_zones
    '''
    # form nova.availability_zones
    # append caller_name 
    caller_name = os.path.join(filename,function_name).replace(os.path.sep,'.')
    return caller_name

def insert_lineno_method(coll, docs):
    '''
    insert location to the coverage database
    docs: list of documents
        document: { location: False }
    '''  
    try:
        coll.insert_many(docs, ordered=False)
    except pymongo.errors.BulkWriteError as e:
        pass



def process_file(source_filepath, json_filename, project_root_dir, port_number, project_name):
    # print("**********  processing {} **********".format(source_filename))

    tree = parse_ast(source_filepath) # an ast tree for the source file
    if not tree:
        return
        
    # get module name in dot format b/c.py -> b.c
    module_name = utils.mod_path_dot(source_filepath,project_root_dir)
    # remove '__init__' to agree with the call graph naming convention
    if module_name.endswith("__init__"):
            module_name = ".".join(module_name.split(".")[:-1])
    
    global_coverage_db = db.Connect.get_connection().get_database(project_name).get_collection("global_coverage")
    # global statements to db
    utils.global_statements_to_db(tree, module_name, global_coverage_db)

    # get all function definitions node to construct AST
    fnDef_list = utils.get_all_fn_def(tree) # a list of function definition AST objects

    for f in fnDef_list:
          
        caller_name = form_caller_name(module_name,f.name)
        
       
        
        ast_modifier = utils.ast_proceeser(json_filename,caller_name,project_name)
        method = ast_modifier.visit(f)

        # use relative path also for the AST
        construct_ast(method, module_name, project_name)

    return "**********  Done {} **********".format(source_filepath)
    
    

def process_file_loc(source_filename, project_name, project_root_dir, port_number):
    """
    Process a module, and insert every statement to the database
    """
    # print("**********  processing {} **********".format(source_filename))

    tree = parse_ast(source_filename) # an ast tree for the source file

    # get module name, omit project root dirname: project_name/b/c.py -> b.c
    module_name = utils.mod_path_dot(source_filename, project_root_dir)
    # remove '__init__' to agree with the call graph naming convention
    if module_name.endswith("__init__"):
            module_name = ".".join(module_name.split(".")[:-1])
            
    tree_visitor = utils.module_visitor(module_name=module_name)
    tree_visitor.visit(tree)
    docs = tree_visitor.get_docs()

    coll = db.Connect.get_connection().get_database(f'{project_name}').get_collection("loc")
    insert_lineno_method(coll, docs)
    



    # print("**********  Done {} **********".format(source_filename))