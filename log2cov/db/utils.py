
import db.connect as connect
# import connect
from pprint import pprint
import pymongo
import config

def view_collections(db):
    print(db.list_collection_names())

def view_doc_count(coll):
    return coll.count_documents({})

def clean_db(project_name):
    '''
    Delete the database if it exists
    '''
    client = connect.Connect.get_connection()
    client.drop_database(project_name)

def clean_collection(db_name, coll_name):
    '''
    Delete the collection if it exists
    '''
    client = connect.Connect.get_connection()
    client.get_database(db_name).drop_collection(coll_name)




def match_logRe_logSeq(coll_logRe, log_seq, name_coll_matched):
    '''
    coll_logRe: collection of logRe
    log_seq: log sequence
    name_coll_matched: name of collection to store matched logRE
    '''

    coll_logRe.aggregate([
        {
            "$match": 
            {
                "$expr": {
                    "$regexMatch": {
                    "input": log_seq,
                    "regex": "$logRE"
                    }
                }
            }
        },
        { "$out" : name_coll_matched}
    ])


def print_all_docs(coll, query):
    '''
    print all documents in a collection that match the query 
    '''
    cursor = coll.find(query)

    for document in cursor:
        pprint(document)



def create_coll(db, coll_name):
    db.create_collection(coll_name)

def insert_many_docs(coll, docs):
    coll.insert_many(docs, ordered=False)

def insert_doc(coll, doc):
    coll.insert_one(doc)

def insert_log_seq(log_seq_location, db):
    with open(log_seq_location) as f:
        salt_log_seq = f.read()

    doc = {
        'seq': salt_log_seq
    }

    insert_doc(db.logSeq, doc)


def create_index(coll, field_name):
    coll.create_index([(field_name, pymongo.ASCENDING)], unique=True)


def get_coverage_stats(coverage_db_name):
    coll = connect.Connect.get_connection().get_database(coverage_db_name).coverage
    num_all = view_doc_count(coll)
    num_must = coll.count_documents({"covered" : {'$eq' : 'Must'}})
    num_must_not = coll.count_documents({"covered" : {'$eq' : 'No'}})
    num_may = coll.count_documents({"covered" : {'$eq' : 'May'}})


    print("num_all: ", num_all)
    print("num_must: ", num_must)
    print("num_must_not: ", num_must_not)
    print("num_may: ", num_may)


def check_must_covered(db, location):
    logRE_regex = ""
    for i in location:
        if i == '(' or i == ')' or i == '+' or i == '|':
            logRE_regex += f'\{i}'
        else:
            logRE_regex += i

    query = { "logRE": { "$regex": f'^(\(*{logRE_regex}\)*(\+)*)+$'} }

    cursor = db.find(query)
    set_list = []
    for dup_logRE in cursor:
        set_list.append(set(dup_logRE['must_not_coverage']))
    must_not_coverage = list(set.intersection(*set_list))
    for location in must_not_coverage:
        # update the covered field to Must
        try:
            if location == "nova.network.floating_ips@172":
                print("***", dup_logRE['logRE'], "****")
        except pymongo.errors.DuplicateKeyError:
            pass
    for document in cursor:
        location = document['logRE']


def check_coverage_location(db, location):
   

    query = { "location": { "$eq": location} }

    cursor = db.find(query)

    
    for document in cursor:
        location = document['location']
        covered = document['covered']
        print(location, covered)
        


def update_coverage_db():
    """
    Update coverage db with the coverage of each logRE
    """
    client = connect.Connect.get_connection()
    db_ = client.get_database(config.DB_NAME)
    # collection for coverage
    coverage = db_.coverage
    # collection for logRE
    matched_logRE = db_.logRE
    # collection for global statements
    global_coverage = db_.global_coverage

    # set to memorize updated modules
    updated_modules = set()

    # find all logRE in logRE collection
    cursor = matched_logRE.find()

    processed_logREs = set()

    for document in cursor:
        # get one logRE
        logRE = document['logRE']
        
        if not logRE in processed_logREs:
            # find all duplicate of that logRE
            logRE_regex = ""
            for i in logRE:
                if i == '(' or i == ')' or i == '+' or i == '|':
                    logRE_regex += f'\{i}'
                else:
                    logRE_regex += i

            query = { "logRE": { "$regex": f'^(\(*{logRE_regex}\)*(\+)*)+$'} }
            cursor_dup_logRE = matched_logRE.find(query)

            # process must coverage
            set_list = []
            for dup_logRE in cursor_dup_logRE:
                set_list.append(set(dup_logRE['coverage']))
            if not set_list:
                print(f"logRE: {logRE} | regex:  f'^(\(*{logRE_regex}\)*(\+)*)+$'")
                continue
            must_coverage = list(set.intersection(*set_list))
            for location in must_coverage:
                # update or insert the covered field to Must
                try:
                    coverage.update_one({'location': location}, {'$set': {'covered': 'Must'}}, upsert=True)
                except pymongo.errors.DuplicateKeyError:
                    pass
                
                # update global statements of the module of that location
                module_name = location.split('@')[0]

                if module_name.endswith("__init__"):
                    module_name = ".".join(module_name.split(".")[:-1])
                    
                # check if the global statements in that module is already updated
                if module_name not in updated_modules:
                    # update global statements
                    query = {"module_name" : {'$eq' : module_name}}
                    doc = global_coverage.find_one(query)
                    if not doc:
                        continue
                    global_must = doc['must_coverage']
                    global_may = doc['may_coverage']
                    try:

                        for i in global_must:
                            # update or insert the covered field to Must
                            coverage.update_one({'location': i}, {'$set': {'covered': 'Must'}}, upsert=True)
                        for i in global_may:
                            # insert May 
                            coverage.insert_one({'location': i, 'covered':'May'})
                    except pymongo.errors.DuplicateKeyError:
                        pass
                    updated_modules.add(module_name)
            


            # process Must-Not coverage
            # rewind cursor_dup_logRE
            cursor_dup_logRE.rewind()
            set_list = []
            for dup_logRE in cursor_dup_logRE:
                set_list.append(set(dup_logRE['must_not_coverage']))
            must_not_coverage = list(set.intersection(*set_list))
            for location in must_not_coverage:
                # update the covered field to No
                try:
                    coverage.insert_one({'location': location, 'covered':'No'})
                except pymongo.errors.DuplicateKeyError:
                    pass


            # process May coverage
            # rewind cursor_dup_logRE
            cursor_dup_logRE.rewind()
            may_cov_all = set()
            may_list = []
            for dup_logRE in cursor_dup_logRE:
                may_list.append(set(dup_logRE['may_coverage']))
            may_cov_all = set.intersection(*may_list)
            must_not_all = set.union(*set_list)
            may_cov_all = may_cov_all - must_not_all
            for location in may_cov_all:
                # only update a location to May-Covered if it is Not-Covered yet
                try:
                    coverage.insert_one({'location': location, 'covered':'May'})
                except pymongo.errors.DuplicateKeyError:
                    pass


            # add the logRE to processed_logREs to avoid duplicate processing
            cursor_dup_logRE.rewind()
            for dup_logRE in cursor_dup_logRE:
                processed_logREs.add(dup_logRE['logRE'])

def insert_log_seq(seq, db):
    doc = {
        'log_sequence': seq
    }

    insert_doc(db.log_sequence, doc)

