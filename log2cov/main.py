import program_analysis.program_analysis_ast as program_analysis_ast
import program_analysis.program_analysis_logre as program_analysis_logre
import log_analysis.process_log as process_log
import utils
import db
import mocking.mock_solution as mock_solution
import os
import pymongo
import sys 

if __name__ == "__main__":
    db_port = os.environ.get("MONGO_PORT")

    '''workload'''
    project_name = 'salt'
    call_graph_location = '/data/salt.json'
    # log_file = "/data/maven-log/salt/maven_log"
    log_file = sys.argv[1]
    thread_id_index = 4 
    remove_patched_dependency = False
    project_root_dir = '/projects/salt'
    test_dir = "/projects/salt/tests/unit"
    modules_dir = os.path.join(project_root_dir, project_name)


    print("*** clean old output ***")
    db.clean_db(project_name, db_port)
    utils.clean_output(project_name)

    print("*** processing call graph ***")
    processed_call_graph = utils.get_call_graph(modules_dir, call_graph_location, project_name)

    print("*** program analysis for AST ***")
    program_analysis_ast.program_analysis_AST(project_name, project_root_dir, processed_call_graph, db_port)

    if remove_patched_dependency:
        print("*** test analysis for mocking and patching  ***")
        program_analysis_ast.patching_indentification(test_dir, project_name, processed_call_graph)

    print("*** log analysis for log sequence ***")
    process_log.dump_log_seq(log_file, project_root_dir, project_name, thread_id_index)

    print("*** program analysis for logRE ***")
    program_analysis_logre.program_analysis_logRE(project_name, db_port)

    print("*** update coverage db ***")
    db.update_coverage_db(project_name, db_port)

  