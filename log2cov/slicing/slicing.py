

import concurrent.futures 
import utils
import slicing.slicer_assignment_eval as slicer
from itertools import repeat
import logging 
from datetime import datetime
import db
import pymongo
import os

class MayResolver():
    def __init__(self, project_name, db_name, project_root_dir, reversed_call_graph_location, call_graph_location):
        self.project_name = project_name
        self.db_name = db_name

        # init db collection
        self.fn_counted = db.Connect.get_connection().get_database(self.db_name).get_collection("counted_fn")
        self.fn_counted.create_index([("location", pymongo.ASCENDING)], unique=True)
        self.may_resolved = db.Connect.get_connection().get_database(self.db_name).get_collection("resolved_may")
        self.may_resolved.create_index([("location", pymongo.ASCENDING)], unique=True)

        self.project_root_dir = project_root_dir
        self.reversed_call_graph = reversed_call_graph_location
        self.call_graph= call_graph_location


    def slicing_for_match(self):
        """
        In a given path, slicing the module ast and finding the match between conditional stmt logging stmt
        """
        
        modules = utils.get_module_names.get_file_path_all(self.project_root_dir, 'py')

        self.create_counted_coverage()

        if not os.path.exists("log2cov-out/logs"):
            os.makedirs("log2cov-out/logs")
        log_location = datetime.now().strftime('log2cov-out/logs/slicing_%Y_%m_%d_%H_%M.log')
        logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(levelname)s %(message)s')

        
        # slicing modules
        total_if_coverage = 0
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for result in executor.map(slicer.process_file, modules,repeat(self.project_name), repeat(self.db_name), repeat(self.project_root_dir), repeat(self.reversed_call_graph), repeat(self.call_graph) ):
                total_if_coverage += result

        # for i in modules:
        #     slicer.process_file(i, self.project_name, self.db_name, self.project_root_dir, self.reversed_call_graph, self.call_graph)
        # slicer.process_file(modules[0], self.project_name, self.db_name, self.project_root_dir, self.reversed_call_graph, self.call_graph)

        # drop the collection of counted coverage
        self.remove_counted_coverage()


    def create_counted_coverage(self):
        """
        Create counted coverage collection
        count function that has been processed for fixable may coverage
        location is the funciton ast path
        """

        # create Single Index for counted coverage collection
        self.fn_counted.create_index([("location", pymongo.ASCENDING)], unique=True)

    def remove_counted_coverage(self):
        """
        remove the collection of counted coverage
        """
        self.fn_counted.drop()





 

