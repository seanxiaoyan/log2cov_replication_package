import db
import xml.etree.ElementTree as ET
import pymongo 
import os
import multiprocessing

port = os.environ.get("MONGO_PORT")

def xml_to_db(xml_file, project_name, test_type):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    db_ = db.Connect.get_connection().get_database('ground_truth')

    
    coll = db_.get_collection(project_name + '_' + test_type)
    # create Single Index for coverage database
    coll.create_index([("location", pymongo.ASCENDING)], unique=True)
    line_count = 0
    docs = []
    for cls in root.iter('class'):
        name = cls.attrib['filename']
        for ln in cls.iter('line'):
            lino = ln.attrib['number']
            if ln.attrib['hits'] == '0':
                covered = 'No'
            else:
                covered = 'Must'
            location = name.rsplit('.',1)[0].replace('/','.') + '@' + lino
            location = location.replace('.__init__', '')
            if location.split('.')[0] != project_name:
                location = project_name + '.' + location
            line_count += 1
            doc = {
                'location': location,
                'covered': covered
            }
            docs.append(doc)
    inserted = coll.insert_many(docs)
    print(len(docs))
    print(f"inserted {len(inserted.inserted_ids)} lines")
    print(f"total {line_count} lines")


    
            

def validate_resolved_may(db_name, project_name, test_type):
    db_ = db.Connect.get_connection().get_database(db_name)
    db_ground_truth = db.Connect.get_connection().get_database('ground_truth')
    ground_truth = db_ground_truth.get_collection(project_name + '_' + test_type)
    resolved_may_cursor = db_.resolved_may.find()
    true_count = 0
    false_count = 0
    no_ground_truth = 0
    for document in resolved_may_cursor:
        location = document['location']
        query = {"location" : {'$eq' : location}}
        cursor = ground_truth.find(query)
        if len(list(cursor)) == 0:
            no_ground_truth += 1
            # print(location)
            continue
        cursor.rewind()

        for doc in cursor:
            if doc['covered'] == document['covered']:
                true_count += 1
            else:
                print(f"Location: {location}, Ground truth: {doc['covered']}, Predicted: {document['covered']}")
                false_count += 1
    resolved_may_cursor.rewind()
    num_resolved = len(list(resolved_may_cursor))

    # print accuracy in percentage
    print(f"Project: {project_name}, Test type: {test_type}, Accuracy: {(true_count + no_ground_truth) / num_resolved * 100}%")




def get_coverage_stats(coverage_db_name):
    db.utils.get_coverage_stats(coverage_db_name) 


def validate_coverage(flag, project_name, coverage_db_name, test_type=None):
    db_ = db.Connect.get_connection().get_database(coverage_db_name)
    coll = db_.coverage

    num_must = coll.count_documents({"covered" : {'$eq' : 'Must'}})
    num_must_not = coll.count_documents({"covered" : {'$eq' : 'No'}})
    num_may = coll.count_documents({"covered" : {'$eq' : 'May'}})

    db_ground_truth = db.Connect.get_connection().get_database('ground_truth')
    ground_truth = db_ground_truth.get_collection(project_name + '_' + test_type)

    query = {"covered" : {'$eq' : flag}}

    cursor = db_.coverage.find(query)

    count_mis_flag =0
    no_ground_truth = 0

    for document in cursor:
        location = document['location']
        covered = document['covered']
        doc_ground_truth = ground_truth.find_one({'location': location})
        if not doc_ground_truth:
            no_ground_truth += 1
            print(location)
            continue
        covered_ground_truth = doc_ground_truth['covered']
        if flag == 'May':
            if covered_ground_truth == 'Must':
                count_mis_flag += 1
        else:
            if covered != covered_ground_truth:
                print(location)
                count_mis_flag += 1

    if flag == 'Must':
        # calculate the accuracy of must
        print(f"Accuracy of Must (no ground truth as correct): {100 * round((num_must - count_mis_flag)/num_must, 2)}%")
        print(f"Accuracy of Must (no ground truth as incorrect): {100 * round((num_must - count_mis_flag - no_ground_truth)/num_must, 2)}%")

    elif flag == 'No':
        print(f"Accuracy of Must-Not (no ground truth as correct): {100 * round((num_must_not - count_mis_flag)/num_must_not, 2)}%")
        print(f"Accuracy of Must-Not (no ground truth as incorrect): {100 * round((num_must_not - count_mis_flag - no_ground_truth)/num_must_not, 2)}%")
    
    else:
        print(f"Percentage of May that is covered (no ground truth as May): {100 * round(count_mis_flag/num_may, 2)}%")
        print(f"Percentage of May that is covered (no ground truth as not May): {100 * round(count_mis_flag/(num_may-no_ground_truth), 2)}%\n")


def enrich_db():
    db_unit = db.Connect.get_connection().get_database('salt_docker')
    print("salt_docker")
    db.get_coverage_stats('salt_docker')
    print("salt_maven")
    db.get_coverage_stats('salt')
    coll_workload1 = db_unit.get_collection('coverage')
    pool = multiprocessing.Pool(processes=8)
    cursor = coll_workload1.find()
    # process_coverage_partial = partial(process_coverage, workload2_db_name = 'salt_unit')
    result = pool.map(compare_coverage, list(chunks(list(cursor),1000)))
    pool.close()
    pool.join()


    must_must = 0
    must_may = 0
    must_no = 0
    may_must = 0
    may_may = 0
    may_no = 0
    no_must = 0
    no_may = 0
    no_no = 0

    for i in result:
        must_must += i['must_must']
        must_may += i['must_may']
        must_no += i['must_no']
        may_must += i['may_must']
        may_may += i['may_may']
        may_no += i['may_no']
        no_must += i['no_must']
        no_may += i['no_may']
        no_no += i['no_no']


    print("must_must", must_must)
    print("must_may", must_may)
    print("must_no", must_no)
    print("may_must", may_must)
    print("may_may", may_may)
    print("may_no", may_no)
    print("no_must", no_must)
    print("no_may", no_may)
    print("no_no", no_no)

def compare_coverage(chunk):
    client = db.connect.Connect.get_connection()
    integration_coverage = client.get_database('salt').get_collection('coverage')
    

    dic = {
        'must_must': 0,
        'must_may': 0,
        'must_no': 0,
        'may_must': 0,
        'may_may': 0,
        'may_no': 0,
        'no_must': 0,
        'no_may': 0,
        'no_no': 0
        
    }

    # for each document in the chunk. compare it with the document in other db
    for document_unit in chunk:
        location_unit = document_unit['location']
        covered_unit = document_unit['covered']
        doc_integration = integration_coverage.find_one({'location': location_unit})
        if not doc_integration:
            if covered_unit == 'Must':
                dic['must_no'] += 1
            elif covered_unit == 'May':
                dic['may_no'] += 1
            else:
                dic['no_no'] += 1
            continue


        covered_integration = doc_integration['covered']


        if covered_unit == 'Must':
            if covered_integration == 'Must':
                
                    dic['must_must'] += 1

            elif covered_integration == 'No':
                    dic['must_no'] += 1
            elif covered_integration == 'May':
                    dic['must_may'] += 1
                    # dic['integration_may_only'] += 1
        elif covered_unit == 'May': #  may be covered in unit
            if covered_integration == 'Must':
             
                    dic['may_must'] += 1
                    # dic['unit_may_only'] += 1

            elif covered_integration == 'No':
                    dic['may_no'] += 1

            elif covered_integration == 'May':
                    dic['may_may'] += 1
                    
        else:
            if covered_integration == 'Must':
             
                    dic['no_must'] += 1

            elif covered_integration == 'No':
                    dic['no_no'] += 1

            elif covered_integration == 'May':
                    dic['no_may'] += 1

    return dic     

def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def process_coverage(db_workload_1, db_workload_2):
    # add the location that is in workload1 db but not in workload2 db

    docs_1 = db_workload_1.find()
    docs_2 = db_workload_2.find()

    docs_to_insert_to_2 = []
    for doc_workload1 in docs_1:
        location = doc_workload1['location']
        doc_workload2 = db_workload_2.find_one({'location': location})
        if doc_workload2:
            continue
        doc = {
            'location': location,
            'covered': 'No',
        }
        docs_to_insert_to_2.append(doc)
    if docs_to_insert_to_2: 
        db_workload_2.insert_many(docs_to_insert_to_2)
    
    docs_to_insert_to_1 = []
    for doc_workload2 in docs_2:
        location = doc_workload2['location']
        doc_workload1 = db_workload_1.find_one({'location': location})
        if doc_workload1:
            continue
        doc = {
            'location': location,
            'covered': 'No',
        }
        docs_to_insert_to_1.append(doc)
    if docs_to_insert_to_1:
        db_workload_1.insert_many(docs_to_insert_to_1)

    return 1

if __name__ == '__main__':
    db_docker = db.Connect.get_connection().get_database('salt_docker')
    db_nginx = db.Connect.get_connection().get_database('salt')
    process_coverage(db_docker.get_collection('coverage'), db_nginx.get_collection('coverage'))
    enrich_db()