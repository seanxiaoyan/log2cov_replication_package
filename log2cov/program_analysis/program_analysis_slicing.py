

import concurrent.futures 
import utils
import slicing.slicer as slicer
from itertools import repeat
import logging 
from datetime import datetime

def slicing_for_match(source_code_path, project_name, db_port_number):
    """
    In a given path, slicing the module ast and finding the match between conditional stmt logging stmt
    """

    modules = utils.get_file_path_all(source_code_path, 'py')

    log_location = datetime.now().strftime('logs/slicing_%Y_%m_%d_%H_%M.log')
    logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(levelname)s %(message)s')

    
    # slicing modules
    total_if_coverage = 0
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for result in executor.map(slicer.process_file, modules,repeat(project_name), repeat(db_port_number)):
            total_if_coverage += result

    print(f"Total valid if coverage: {total_if_coverage} on project {project_name}")


if __name__ == "__main__":
    source_code_path = "salt/salt/"
    project_name = 'salt'
    port_number = 27000
    slicing_for_match(source_code_path, project_name, port_number)