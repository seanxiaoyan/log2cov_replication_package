import program_analysis.program_analysis_ast as program_analysis_ast
import program_analysis.program_analysis_logre as program_analysis_logre
import log_analysis.process_log as process_log
import utils
import db
import mocking.mock_solution as mock_solution
import os
import pymongo
import sys 
import pr_changed_fn
import update_cg
import config
import time




REPO_OWNER = "saltstack"
REPO_NAME = "salt"
GITHUB_TOKEN = "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"
CSV_FILE = "filtered_prs.csv"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
OUTPUT_FILE = "num_changed_files.png"

def set_changed_files(pr_number, changed_files, project_root_dir):
    # changed_files: list of file paths

    # append project root dir to each file path
    changed_files = [os.path.join(project_root_dir, f) for f in changed_files]
    
    db_changed_files = db.Connect.get_connection().get_database(config.DB_NAME).get_collection("changed_files")
    db_changed_files.create_index([("pr_number", pymongo.ASCENDING)], unique=True)
    # replace the existing doc with the new one
    db_changed_files.replace_one({"pr_number": pr_number}, {"pr_number": pr_number, "file_list": changed_files}, upsert=True)



if __name__ == "__main__":
    pr_number = sys.argv[1]
    workload_name = sys.argv[2]
    db_name = 'salt' + '_' + workload_name
    config.set_db_name(db_name)
    config.set_task("update_coverage_db")


    '''workload'''
    project_name = 'salt'
    log_file = os.path.join("/data/logs", pr_number, f"{workload_name}.log")

    if not os.path.exists(log_file):
        print(f"log file {log_file} does not exist")
        exit()


    thread_id_index = 4 
    project_root_dir = '/projects/salt'
    modules_dir = os.path.join(project_root_dir, project_name)

    original_cg_path = '/log2cov/log2cov-out/call_graph/salt.json'

    # ---------------------------------------------------------------------------------------------------------------------------

    print("get modified files in a PR")
    changed_files, file_name_map, lines_changed, pr_valid, functions_changed = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)
    
    functions_changed_processed = {'.'.join(filter(lambda x: x != '__init__', item.split('.'))) for item in functions_changed}

    # if changed_files is empty, exit
    if not changed_files:
        exit()
    # add changed_files to config so that it can be used in other modules
    set_changed_files(pr_number, list(changed_files), project_root_dir)

    if workload_name == 'salt': # for each codebase version, we only need to process the call graph once, that is, up on the first workload
        # 2. update the call graph using the modified files
        cg_subset_path = '/tmp/salt.json'

        # make sure the cg_subset does not exist, otherwise remove it 
        if os.path.exists(cg_subset_path):
            os.remove(cg_subset_path)
        
        changed_modules = [f for f in changed_files if os.path.exists(os.path.join(project_root_dir, f))]
        update_cg.run_pycg('salt', changed_modules, cg_subset_path)

        # Process the sub call graph 
        print("process sub call graph")
        modules_dir = os.path.join(project_root_dir, 'salt')
        utils.get_call_graph(modules_dir, cg_subset_path, 'salt', out_dir=cg_subset_path)

        # update the original call graph
        
        update_cg.update_call_graph(original_cg_path, cg_subset_path, changed_modules, file_name_map)

    # 3. clean up collection in coverage db
    print("clean up coverage collection in  db")
    db.clean_collection(config.DB_NAME, 'coverage')
    db.clean_collection(config.DB_NAME, 'new_entries')

    # 4. program analysis for AST for the modified files
    print("program analysis for AST for the modified files")
    # create index for collection "new_entries" 
    coll_new_entries = db.Connect.get_connection().get_database(config.DB_NAME).get_collection("new_entries")
    coll_new_entries.create_index([("entry", pymongo.ASCENDING)], unique=True)
    
    changed_modules = [os.path.join('/projects/salt', f) for f in changed_files if os.path.exists(os.path.join(project_root_dir, f))]
    program_analysis_ast.program_analysis_AST(project_name, project_root_dir, original_cg_path, changed_modules)

    # 5. log analysis
    print("log analysis for log sequence")
    process_log.dump_log_seq(log_file, project_root_dir, project_name, thread_id_index)
   
    # 6. program analysis for logRE 
    print("program analysis for logRE")

    # use changed functions to get their caller functions
    caller_functions_of_changed_functions = update_cg.get_affected_functions(original_cg_path, functions_changed_processed)
    db_ = db.Connect.get_connection().get_database(config.DB_NAME)
    coll_logRE = db_.get_collection("logRE")

    entries_changed_function_caller = []
    for i in caller_functions_of_changed_functions:
        entry = os.path.join("log2cov-out/AST/salt", *i.split('.')[:-1], i.split('.')[-1] + ".txt")
        result = coll_logRE.delete_many({"entry": entry})
        entries_changed_function_caller.append(entry)

    cursor = coll_new_entries.find({})
    entries_for_getting_logre = [doc["entry"] for doc in list(cursor)] + entries_changed_function_caller
    entries_for_getting_logre = list(set(entries_for_getting_logre))

    program_analysis_logre.program_analysis_logRE(project_name, entries_for_getting_logre)

    # 7. update coverage db
    print(f"*** update coverage db for workload {workload_name}***")
    db.Connect.get_connection().get_database(config.DB_NAME).drop_collection("coverage")
    time.sleep(1) 
    db_coverage = db.Connect.get_connection().get_database(config.DB_NAME).get_collection("coverage")
    # create Coumpund Index for  coverage database
    db_coverage.create_index([("location", pymongo.ASCENDING),("covered",pymongo.ASCENDING )], unique=True)
    db.update_coverage_db()


