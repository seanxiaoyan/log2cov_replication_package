import db
from itertools import combinations


def check_agreement():
    # Connect to the MongoDB server, assuming it is running on your local machine (localhost) on port 27017
    client = db.Connect.get_connection()

    # Specify the names of your databases and collection
    source_db_name = 'salt_pr_impact'
    collection_name = 'impact'

    # Counter for disagreements
    disagreement_counter = 0

    # Iterate over the documents in the salt_docker.impact collection
    source_db = client[source_db_name]
    source_collection = source_db[collection_name]

    # cursor = source_collection.find({"PR_Number": "62809"})
    # for i in cursor:
    #     print(i)
    for doc in source_collection.find():
        if doc:
            pr_number = doc['PR_Number'] 
            total_lines = doc['total_lines']
            lines_impact_different = doc['lines_impact_different']

            if lines_impact_different > 0:
              
                disagreement_counter += 1
    print(f"Total number of PRs with disagreement: {disagreement_counter}")



def compare_coverage_db():
    client = db.Connect.get_connection()
    db1 = client['salt_statusnet']
    db2 = client['salt_salt']
    db3 = client['salt_docker']
    db4 = client['salt_nginx']
    db5 = client['salt_users']
    db6 = client['salt_openssh']

    coverage1 = {doc['location']: doc['covered'] for doc in db1['coverage'].find() if doc['covered'] != 'May'}
    coverage2 = {doc['location']: doc['covered'] for doc in db2['coverage'].find() if doc['covered'] != 'May'}
    coverage3 = {doc['location']: doc['covered'] for doc in db3['coverage'].find() if doc['covered'] != 'May'}
    coverage4 = {doc['location']: doc['covered'] for doc in db4['coverage'].find() if doc['covered'] != 'May'}
    coverage5 = {doc['location']: doc['covered'] for doc in db5['coverage'].find() if doc['covered'] != 'May'}
    coverage6 = {doc['location']: doc['covered'] for doc in db6['coverage'].find() if doc['covered'] != 'May'}

    all_coverages = [coverage1, coverage2, coverage3, coverage4, coverage5, coverage6]

    for i, coverage in enumerate(all_coverages):
        covered_in_current_db = {loc: status for loc, status in coverage.items() if status == 'Must'}
        covered_only_in_this = set(loc for loc, status in covered_in_current_db.items() if all(other_db.get(loc) == 'No' or other_db.get(loc) is None for other_db in all_coverages[:i] + all_coverages[i+1:]))
        print(f"In DB{i+1}, {len(covered_only_in_this)} documents are covered that are not covered in the other databases.")
        print(f"In DB{i+1}, {len(covered_in_current_db)} is Must covered")

def pairwise_compare():
    from itertools import combinations

def compare_coverage_db_pairwise():
    client = db.Connect.get_connection()
    db_names = ['salt_salt', 'salt_docker', 'salt_nginx', 'salt_users', 'salt_openssh']
    databases = {name: client[name] for name in db_names}

    coverages = {db_name: {doc['location']: doc['covered'] for doc in db['coverage'].find() if doc['covered'] != 'May'} for db_name, db in databases.items()}

    for db1_name, db2_name in combinations(db_names, 2):
        coverage1 = coverages[db1_name]
        coverage2 = coverages[db2_name]

        covered_in_db1 = {loc: status for loc, status in coverage1.items() if status == 'Must'}
        covered_in_db2 = {loc: status for loc, status in coverage2.items() if status == 'Must'}

        covered_only_in_db1 = set(loc for loc, status in covered_in_db1.items() if coverage2.get(loc) != 'Must')
        covered_only_in_db2 = set(loc for loc, status in covered_in_db2.items() if coverage1.get(loc) != 'Must')

        print(f"In {db1_name}, compared to {db2_name}, {len(covered_only_in_db1)} documents are covered that are not covered in the other database.")
        print(f"In {db2_name}, compared to {db1_name}, {len(covered_only_in_db2)} documents are covered that are not covered in the other database.")


def check_db():
    client = db.Connect.get_connection()
    salt_docker = client['salt_docker']
    
    # check if there exist any document which the location field match the pattern of "*cmdmod*"
    cursor = salt_docker['logRE'].find({"logRE": {"$regex": ".*cmdmod.*"}})
    for doc in cursor:
        print(doc)
    



if __name__ == "__main__":
    check_agreement()

    


