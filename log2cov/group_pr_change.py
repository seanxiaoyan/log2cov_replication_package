import db
import pymongo
import pr_changed_fn
import csv
import os 

REPO_OWNER = "saltstack"
REPO_NAME = "salt"
GITHUB_TOKEN = "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"
CSV_FILE = "sample_results.csv"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

def analysis_code_change(csv_path):
    if not os.path.exists(csv_path):
        print("csv file does not exist")
        exit(1)

    db_client = db.Connect.get_connection()
    pr_code_changes_db = db_client.get_database("salt_pr_code_changes")
    # create index for the collection
    if "changed_fns" not in pr_code_changes_db.list_collection_names():
        coll_code_changes = pr_code_changes_db.get_collection("changed_fns")
        coll_code_changes.create_index([("fn_name", pymongo.ASCENDING)], unique=True)
    
    # example of location: "salt.runner@10"

    # Iterate over the csv file, which the first column is the PR number
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr_number = row["PR Number"]
            if not pr_number:
                print("PR number is empty, exit 1")
                exit(1)

            _, _, _, _, functions_get_changed = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)


            collection = pr_code_changes_db.changed_fns

            for fn_name in functions_get_changed:
                collection.update_one(
                    {"fn_name": fn_name},
                    {"$addToSet": {"pr_numbers": pr_number}, "$setOnInsert": {"fn_name": fn_name}},
                    upsert=True  # Create a new document if no documents match the filter
                )
                

            # for file_name in changed_files:
            #     # If the file_name exists in file_name_map, it means the module name has been changed
            #     # We need to update the document where old module name was used
            #     if file_name in file_name_map:
            #         old_file_name = file_name_map[file_name]
            #         doc = collection.find_one({"module_name": old_file_name})
            #         if doc is not None:
            #             # Update the document with new module name, keeping the count same
            #             collection.update_one(
            #                 {"_id": doc["_id"]},
            #                 {"$set": {"module_name": file_name}}
            #             )
            #         # file_name = new_file_name  # Continue to count this under the new name

            #     collection.update_one(
            #         {"module_name": file_name},
            #         {"$addToSet": {"pr_numbers": pr_number}, "$setOnInsert": {"module_name": file_name}},
            #         upsert=True  # Create a new document if no documents match the filter
            #     )



def sort_changed_function():
    db_client = db.Connect.get_connection()
    code_change_db = db_client.get_database("salt_pr_code_changes")
    collection = code_change_db.changed_fns



    # Get the distinct count of PRs for each module in the collection
    fn_pr_counts = [(doc['fn_name'], len(doc['pr_numbers'])) for doc in collection.find()]

    # Sort modules by distinct count of PRs in descending order
    ranking = sorted(fn_pr_counts, key=lambda x: x[1], reverse=True)

    # Prepare data for csv, only including module names from the loaded data
    csv_data = [(fn_name, pr_count) for fn_name, pr_count in ranking]

    # Write data to a csv file
    with open('changed_functions_ranking.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["fn_name", "pr_count"])  # Write header
        writer.writerows(csv_data)  # Write data



def count_total_pr_in_fn_set():

    module_names = []
    lines_read = 0
    with open('changed_functions_ranking.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if lines_read == 91: # read upto 92th line
                break
            module_names.append(row['module_name'])
            lines_read += 1
    

    db_client = db.Connect.get_connection()
    pr_code_changes_db = db_client.get_database("salt_pr_code_changes")
    collection = pr_code_changes_db.changed_fns

    pr_set  = set()
    for module_name in module_names:
        doc = collection.find_one({"fn_name": module_name})
        if doc is not None:
            pr_set.update(doc['pr_numbers'])
    
    print(len(pr_set))

if __name__ == "__main__":
    client = db.Connect.get_connection()
    d = client.get_database("salt_docker")
    col = d.get_collection("logRE")
    # qury a specific document
    # query = {"coverage": "salt.modules.cmdmod@446"}
    # location_range = ["salt.modules.cmdmod@{}".format(i) for i in range(258, 892)]

    query = {"logRE": {"$regex": ".*salt.modules.cmdmod@.*"}}

    docs = col.find(query)

    for doc in docs:
        print(doc['logRE'])
    # _, _, _, _, functions_get_changed = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, 63984, headers)
    # print(functions_get_changed)



    # sort_changed_function()