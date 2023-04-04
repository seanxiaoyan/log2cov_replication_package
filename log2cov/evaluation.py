import db
import xml.etree.ElementTree as ET
import pymongo 
import os

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



