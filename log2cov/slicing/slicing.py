

import concurrent.futures 
import utils
import slicing.slicer_assignment_eval as slicer
from itertools import repeat
import logging 
from datetime import datetime
import db
import pymongo
import os
import config 

class MayResolver():
    def __init__(self, project_name, db_name):
        self.project_name = project_name
        self.db_name = db_name

        # init db collection
        self.fn_counted = db.Connect.get_connection().get_database(self.db_name).get_collection("counted_fn")
        self.fn_counted.create_index([("location", pymongo.ASCENDING)], unique=True)
        self.may_resolved = db.Connect.get_connection().get_database(self.db_name).get_collection("resolved_may")
        self.may_resolved.create_index([("location", pymongo.ASCENDING)], unique=True)

        self.project_root_dir = config.PROJECT_ROOT_PATH
        self.reversed_call_graph = config.REVERSED_CALL_GRAPH_LOCATION
        self.call_graph= config.CALL_GRAPH_LOCATION


    def slicing_for_match(self):
        """
        In a given path, slicing the module ast and finding the match between conditional stmt logging stmt
        """
        
        modules = utils.get_module_names.get_file_path_all(self.project_root_dir, 'py')

        self.create_counted_coverage()

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


    def update_coverage(self):
        """
        Update coverage collection using resolved_may collection
        """
        db_ = db.Connect.get_connection().get_database(self.db_name)

        resolved_may = db_['resolved_may']
        coverage = db_['coverage']

        for doc in resolved_may.find():
            # Use the location field as the query to find the corresponding doc in the coverage collection
            coverage_doc = coverage.find_one({"location": doc["location"]})
            # If a document was found
            if coverage_doc is not None:
                # Update the 'covered' field of the coverage collection document
                # catch duplicatekeyerror
                try:
                    coverage.update_one({"_id": coverage_doc["_id"]}, {"$set": {"covered": doc["covered"]}})
                except pymongo.errors.DuplicateKeyError:
                    print(f"DuplicateKeyError for {doc['location']}")

        

        # Drop the resolved_may collection
        resolved_may.drop()


