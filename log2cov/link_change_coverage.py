import db

def b():

    client = db.Connect.get_connection()

    d = client.get_database('salt_salt')
    changed_fns = d['coverage']

    # find all documents where the 'logRE' field contains 'cassandra'
    docs = changed_fns.find({'location': {'$regex': 'salt.modules.cmdmod.*'}})

    # l = list(docs)
    # for i in l:
    #     print(i)
    # print(len(l))


def a():
    client = db.Connect.get_connection()
    dd = client.get_database('salt_pr_impact')
    collection = dd['impact']

    # Find documents with more than 3 fields
    matching_docs = []
    for doc in collection.find():
        if len(doc) > 4:  # Counting the _id field as well
            matching_docs.append(doc)

    # Print the matching documents
    print(len(matching_docs))


def c():
    # Connect to your MongoDB server
    client = db.Connect.get_connection()
    db_salt_workloads_module_coverage = client['salt_workloads_module_coverage']
    db_modules_pr = client['salt_pr_code_change']
    # Retrieve all documents from the salt_workloads_module_coverage.module_coverage collection
    module_coverage_collection = db_salt_workloads_module_coverage['module_coverage']
    module_pr_collection = db_modules_pr['modules']
    

    # Initialize a set to store the PR numbers
    pr_numbers_set = set()

    # Iterate through each document in the module_coverage_collection
    for document in module_coverage_collection.find():
        module_name = document['module_name']
        
        # Query the modules collection for a document with the same module_name
        module_doc = module_pr_collection.find_one({'module_name': module_name})
        if module_doc:
            pr_numbers = module_doc['pr_numbers']
            pr_numbers_set.update(pr_numbers)

    print(len(pr_numbers_set))
    # write this set to a file 
    with open('execution_scenarios_related_pr.txt', 'w') as f:
        for item in pr_numbers_set:
            f.write("%s\n" % item)


a()