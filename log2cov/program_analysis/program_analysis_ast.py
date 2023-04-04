import os
from ast import *
import utils
from itertools import repeat
import concurrent.futures 
import db 
import pymongo

def program_analysis_AST(project_name, project_root_dir, call_graph_location, port_number):
    """
    Construct AST for each function in the source code
    """

    
    p = os.path.join(project_root_dir, project_name)
    modules = utils.get_file_path_all(p, 'py')

    
    # coverage database
    db_coverage = db.Connect.get_connection().get_database(project_name).get_collection("coverage")
    # global_coverage database
    db_global_coverage = db.Connect.get_connection().get_database(project_name).get_collection("global_coverage")

    # create Coumpund Index for  coverage database
    db_coverage.create_index([("location", pymongo.ASCENDING),("covered",pymongo.ASCENDING )], unique=True)
    # create Single Index for coverage database
    db_coverage.create_index([("location", pymongo.ASCENDING)], unique=True)
    
    # create Index for field: module_name in global_coverage database
    db_global_coverage.create_index([("module_name", pymongo.ASCENDING)], unique=True)
    
    # check call graph
    if not os.path.exists(call_graph_location):
        print("call graph not exist")
        exit()

    # create out directory
    try:
        os.makedirs("log2cov-out/AST")
    except FileExistsError:
        pass

    # build AST
    with concurrent.futures.ProcessPoolExecutor() as executor:
        
        for r in executor.map(utils.process_file, modules, repeat(call_graph_location), repeat(project_root_dir), repeat(port_number), repeat(project_name)):
            try:
                print(r)
            except Exception as e:
                print(e)


def patching_indentification(test_dir, project_name, call_graph_location):
    """
    identify the patching usage in the test code, remove callee from the call graph
    if callee is replaced by mock using patch()
    """
    


    modules = utils.get_file_path_all(test_dir, 'py', include_test=True)

    callee_set = set()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(utils.find_patching, modules)
        for res in results:
            callee_set = callee_set.union(res)

    callee_list = list(callee_set)
    utils.remove_callee(callee_list, project_name, call_graph_location)
