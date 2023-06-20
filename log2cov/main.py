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





REPO_OWNER = "saltstack"
REPO_NAME = "salt"
GITHUB_TOKEN = "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"
CSV_FILE = "filtered_prs.csv"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
OUTPUT_FILE = "num_changed_files.png"

if __name__ == "__main__":
    '''Get LogRes for a project'''

    workload = sys.argv[1]

    db_name = 'salt' + '_' + workload
    config.set_db_name(db_name)
    thread_id_index = 4
    log_file = f'/data/logs/base_version/{workload}.log'
    project_name = 'salt'
    call_graph_location = '/data/salt.json'
    project_root_dir = '/projects/salt'
    modules_dir = os.path.join(project_root_dir, project_name)


    if not os.path.exists(log_file):
        print(f"{log_file} does not exist")
        exit(1)
    if not os.path.exists(call_graph_location):
        print(f"{call_graph_location} does not exist")
        exit(1)
    if not os.path.exists(modules_dir):
        print(f"{modules_dir} does not exist")
        exit(1)
    

    print("*** clean old output ***")
    utils.clean_output(project_name)

    print("*** processing call graph ***")
    processed_call_graph = utils.get_call_graph(modules_dir, call_graph_location, project_name)

    print("*** program analysis for AST ***")
    program_analysis_ast.program_analysis_AST(project_name, project_root_dir, processed_call_graph)


    print("*** log analysis for log sequence ***")
    process_log.dump_log_seq(log_file, project_root_dir, project_name, thread_id_index)

    print("*** program analysis for logRE ***")
    program_analysis_logre.program_analysis_logRE(project_name)

    print("*** update coverage db***")
    db.update_coverage_db()



  