
import os
from ast import *
import graph_traversal
from itertools import repeat
from concurrent.futures import TimeoutError
from pebble import ProcessPool, ProcessExpired
import logging
import pymongo
import db
from utils.get_module_names import get_file_path_all
from datetime import datetime
import config

def mongodb_insert_many(db_logRE, docs):


 
    try:
        insert_status = db_logRE.insert_many(docs, ordered=False)
        
        # get the number of inserted documents
        len_inserted = len(insert_status.inserted_ids)
        return len_inserted
    except pymongo.errors.BulkWriteError:
        return "encounter duplication"


def traverse_AST(entry, log_seq=None):

    client = db.Connect.get_connection()
    db_logRE = client.get_database(config.DB_NAME).get_collection("logRE")
   

    if not os.path.exists(entry):
        print(f"{entry} does not exist")
    try:
        tree = graph_traversal.get_ast(entry)
        if not tree:
            logging.error(f"{entry} is not a valid txt file")
        else:
            node_visitor = graph_traversal.newVisitor(filepath=entry, size=0, size_hit_return=0)
            node_visitor.visit(tree)
            # len_result = (len(node_visitor.log)+len(node_visitor.hit_return_log))
            
            docs_to_insert = graph_traversal.get_logRe_docs(node_visitor, log_seq)

            if docs_to_insert:
                insertion_length = mongodb_insert_many(db_logRE, docs_to_insert)
                logging.debug(f"[{insertion_length}] {entry}")
                return entry
            else:
                return entry

    except MemoryError:
        msg = f"mem error for ast {entry}: {MemoryError.args}"
        logging.error(msg)
    
    
def program_analysis_logRE(project_name, entry = None):

    # setup logging

    # if log2cov-out/logs does not exist, create it
    if not os.path.exists("log2cov-out/logs"):
        os.makedirs("log2cov-out/logs")      
    # log_location = datetime.now().strftime('log2cov-out/logs/salt_%Y_%m_%d_%H_%M.log')
    log_location = datetime.now().strftime('log2cov-out/logs/update_coverage_db.log')
    logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(asctime)s %(created)f %(levelname)s %(message)s')

    # get ast files
    if entry is None:
        ast_root_dir = os.path.join("log2cov-out", "AST", project_name)
        entries= get_file_path_all(ast_root_dir, 'txt')
        
        # create index for logRE collection
        db_logRE = db.Connect.get_connection().get_database(config.DB_NAME).get_collection("logRE")
        db_logRE.create_index([("logRE", pymongo.ASCENDING)])
        db_logRE.create_index([("entry", pymongo.ASCENDING)])
        log_seq = None
    else:
        # Below is for incremental update coverage db
        entries = entry
        # get log sequence
        log_seq_path = os.path.join("log2cov-out", "log_sequence", project_name, "log_seq.txt")
        # log_seq_path = config.LOG_SEQ_PATH
        with open(log_seq_path, 'r') as f:
            log_seq = f.read()

    

    # Traverse ASTs and update coverage db, max time 120 seconds for each traversal 
    results = []
    with ProcessPool(max_workers=8) as pool:
         future = pool.map(traverse_AST, entries, repeat(log_seq), timeout=240)
         iterator = future.result()

         # iterate over all results, if a computation timed out
         # print it and continue to the next result
         while True:
             try:
                 result = next(iterator)
                 if result:
                    results.append(result)

             except TimeoutError as error:
                 print("time out 120 seconds, hard stop current process")
             except StopIteration:
                 break
             except ProcessExpired as error:
                 print("%s. Exit code: %d" % (error, error.exitcode))

    print("All:",len(entries))
    print("Done:",len(results))
    logging.info(f"Done: {len(results)}")

