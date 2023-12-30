import program_analysis.program_analysis_ast as program_analysis_ast
import program_analysis.program_analysis_logre as program_analysis_logre
import db
import os
from slicing.slicing import MayResolver
import config 
import sys
import utils
from datetime import datetime
import logging


if __name__ == "__main__":
    # project_name = 'salt'
    # db_name = 'salt_unit_initial'
    # call_graph_location = '/log2cov/log2cov-out/call_graph/salt.json'
    # project_root_dir = '/projects/salt/'

    # project_name = 'salt'
    # db_name = 'salt_integration'
    # call_graph_location = '/log2cov/log2cov-out/call_graph/salt.json'
    # project_root_dir = '/projects/salt'

    # project_name = 'nova'
    # db_name = "nova_unit_initial"
    # call_graph_location = "/log2cov/log2cov-out/call_graph/nova.json"
    # project_root_dir = '/projects/nova'

    # project_name = 'nova'
    # db_name = "nova_functional"
    # call_graph_location = "log2cov-out/call_graph/nova.json"
    # project_root_dir = '/projects/nova'

    # project_name = 'homeassistant'
    # db_name = "homeassistant_unit_initial"
    # call_graph_location = 'log2cov-out/call_graph/homeassistant.json'
    # project_root_dir = '/projects/core'

    # project_name = 'salt'
    # db_name = 'salt'
    # call_graph_location = '/log2cov/log2cov-out/call_graph/salt.json'
    # project_root_dir = '/projects/salt/'

  

    # '''
    # RQ1
    # '''
    # reversed_call_graph = utils.reverse_call_graph(call_graph_location, project_name)

    # may_killer = MayResolver(project_name, db_name, project_root_dir, reversed_call_graph, call_graph_location)
    # may_killer.slicing_for_match()


    '''
    workload
    '''

    pr_number = sys.argv[1]
    workload = sys.argv[2]

    project_name = 'salt'
    db_name = 'salt' + '_' + workload
    project_root_dir = '/projects/salt/'
    call_graph_location = '/log2cov/log2cov-out/call_graph/salt.json'
    reversed_call_graph_location = utils.reverse_call_graph(call_graph_location, project_name)
    log_path = f'/data/logs/{pr_number}/{workload}.log'

    # if any path above is not valid, exit
    if not os.path.exists(project_root_dir):
        print(f"{project_root_dir} does not exist")
        exit(1)
    if not os.path.exists(call_graph_location):
        print(f"{call_graph_location} does not exist")
        exit(1)
    if not os.path.exists(reversed_call_graph_location):
        print(f"{reversed_call_graph_location} does not exist")
        exit(1)
    if not os.path.exists(log_path):
        print(f"{log_path} does not exist")
        exit(1)
    

    config.set_db_name(db_name)
    config.set_project_root_path(project_root_dir)
    config.set_call_graph_location(call_graph_location)
    config.set_reversed_call_graph_location(reversed_call_graph_location)
    config.set_log_file_path(log_path)
    config.set_task('update_coverage_db')
    config.set_pr_number(pr_number)

    log_location = datetime.now().strftime('log2cov-out/logs/update_coverage_db.log')
    logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(asctime)s %(created)f %(levelname)s %(message)s')

    logging.info(f"starting slicing for {workload}")
    may_resolver = MayResolver(project_name, db_name)
    may_resolver.slicing_for_match()
    may_resolver.update_coverage()
