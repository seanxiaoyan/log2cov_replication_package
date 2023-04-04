import program_analysis.program_analysis_ast as program_analysis_ast
import program_analysis.program_analysis_logre as program_analysis_logre
import log_analysis.process_log as process_log
import utils
import db
import mocking.mock_solution as mock_solution
import os
from slicing.slicing import MayResolver
import shutil

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

    project_name = 'homeassistant'
    db_name = "homeassistant_unit_initial"
    call_graph_location = 'log2cov-out/call_graph/homeassistant.json'
    project_root_dir = '/projects/core'

  

    '''
    RQ1
    '''
    reversed_call_graph = utils.reverse_call_graph(call_graph_location, project_name)

    may_killer = MayResolver(project_name, db_name, project_root_dir, reversed_call_graph, call_graph_location)
    may_killer.slicing_for_match()

    