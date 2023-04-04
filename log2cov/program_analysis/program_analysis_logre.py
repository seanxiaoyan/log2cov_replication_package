
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


def mongodb_insert_many(db_logRE, docs):


 
    try:
        insert_status = db_logRE.insert_many(docs, ordered=False)
        
        # get the number of inserted documents
        len_inserted = len(insert_status.inserted_ids)
        return len_inserted
    except pymongo.errors.BulkWriteError:
        return "encounter duplication"


def traverse_AST(entry, log_seq, project_name, port_number):

    client = db.Connect.get_connection()
    db_logRE = client.get_database(project_name).get_collection("logRE")
   

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

            # if db_upated:
            #     # logging.info(entry)
            #     return entry
            # else:
            #     # logging.debug(entry)
            #     pass

    except MemoryError:
        msg = f"mem error for ast {entry}: {MemoryError.args}"
        logging.error(msg)
    
    
def program_analysis_logRE(project_name, db_port):

    # setup logging

    # if log2cov-out/logs does not exist, create it
    if not os.path.exists("log2cov-out/logs"):
        os.makedirs("log2cov-out/logs")
    log_location = datetime.now().strftime('log2cov-out/logs/salt_%Y_%m_%d_%H_%M.log')
    logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(levelname)s %(message)s')

    # get ast files
    ast_root_dir = os.path.join("log2cov-out", "AST", project_name)
    entries= get_file_path_all(ast_root_dir, 'txt')

    # get log sequence
    log_seq_path = os.path.join("log2cov-out", "log_sequence", project_name, "log_seq.txt")
    with open(log_seq_path, 'r') as f:
        log_seq = f.read()

    # create index for field: logRE in collection logRE
    db_logRE = db.Connect.get_connection().get_database(project_name).get_collection("logRE")
    db_logRE.create_index([("logRE", pymongo.ASCENDING)])

    # Traverse ASTs and update coverage db, max time 120 seconds for each traversal 
    results = []
    with ProcessPool(max_workers=8) as pool:
         future = pool.map(traverse_AST, entries, repeat(log_seq), repeat(project_name), repeat(db_port), timeout=120)
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

# if __name__ == "__main__":
    
#     project_name = 'salt'
#     db_port = 27017
#     log_location = datetime.now().strftime('logs/salt_%Y_%m_%d_%H_%M.log')
#     logging.basicConfig(filename=log_location, level=logging.DEBUG, format='%(levelname)s %(message)s')
#     ast_root_dir = f'{project_name}-ast'
#     entries= get_module_names(ast_root_dir, '.txt')
#     log_file = "salt_unit"
#     thread_id_index = 1
#     coll_log_seq = db.Connect.get_connection(db_port).get_database(project_name).get_collection("log_sequence")

#     # process_log.log_to_db(log_file, project_name, thread_id_index, db_port)
#     log_sequence = coll_log_seq.find_one({"log_sequence": {"$exists": True}})
    
#     for key, value in log_sequence.items():
#         print(key)
   