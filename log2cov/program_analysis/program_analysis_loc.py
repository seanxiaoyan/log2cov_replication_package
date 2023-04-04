import db
import pymongo 
import concurrent.futures 
import utils
from itertools import repeat
from functools import partial

def get_loc_all_modules(project_name, port_number):
    modules = utils.get_module_names(project_name, 'py')
    # loc database
    db_loc = db.Connect.get_connection().get_database(f'{project_name}').get_collection("loc")
    # create Single Index for loc database
    db_loc.create_index([("location", pymongo.ASCENDING)], unique=True)
    # store loc in loc database
    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(utils.process_file_loc, modules, repeat(project_name), repeat(port_number))

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def update_must_not_coverage(project_name, port_number):
    db_loc = db.Connect.get_connection().get_database(f'{project_name}').get_collection("loc")
    cursor = db_loc.find() # find all docuements in loc

    update_partial = partial(update_by_chunk, project_name=project_name, port_number=port_number)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(update_partial, list(chunks(list(cursor),1000)))


def update_by_chunk(chunk, project_name, port_number):
    db_coverage = db.Connect.get_connection().get_database(f'{project_name}').get_collection("coverage")
    docs_to_insert = []
    for doc in chunk:
        location = doc['location']
        doc_location = db_coverage.find_one({'location': location})
        if not doc_location:
            doc_to_insert = {
                'location': location,
                'covered': 'No'
            }
            docs_to_insert.append(doc_to_insert)
    result = db_coverage.insert_many(docs_to_insert, ordered=False)
    msg = f"{len(result.inserted_ids)} docs have been inserted "
    print(msg)
