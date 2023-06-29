import db
import pymongo
import pr_changed_fn
import csv
import os 
import csv

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
    if "modules" not in pr_code_changes_db.list_collection_names():
        coll_code_changes = pr_code_changes_db.get_collection("modules")
        coll_code_changes.create_index([("module_name", pymongo.ASCENDING)], unique=True)
    
    # example of location: "salt.runner@10"

    # Iterate over the csv file, which the first column is the PR number
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr_number = row["PR Number"]
            if not pr_number:
                print("PR number is empty, exit 1")
                exit(1)

            changed_files, file_name_map = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)

            collection = pr_code_changes_db.modules

            for file_name in changed_files:
                # If the file_name exists in file_name_map, it means the module name has been changed
                # We need to update the document where old module name was used
                if file_name in file_name_map:
                    new_file_name = file_name_map[file_name]
                    doc = collection.find_one({"module_name": file_name})
                    if doc is not None:
                        # Update the document with new module name, keeping the count same
                        collection.update_one(
                            {"_id": doc["_id"]},
                            {"$set": {"module_name": new_file_name}}
                        )
                    file_name = new_file_name  # Continue to count this under the new name

                collection.update_one(
                    {"module_name": file_name},
                    {"$addToSet": {"pr_numbers": pr_number}, "$setOnInsert": {"module_name": file_name}},
                    upsert=True  # Create a new document if no documents match the filter
                )



def sorting_modules():
    db_client = db.Connect.get_connection()
    code_change_db = db_client.get_database("salt_pr_code_changes")
    collection = code_change_db.modules

    # Load the collection of salt_workloads_module_coverage
    workload_db = db_client.get_database("salt_workloads_module_coverage")
    workload_module = workload_db.get_collection("module_coverage")

    # Extract module names from workload_module collection and store in a set
    module_names = {doc['module_name'] for doc in workload_module.find()}

    # Get the distinct count of PRs for each module in the collection
    module_pr_counts = [(doc['module_name'], len(doc['pr_numbers'])) for doc in collection.find()]

    # Sort modules by distinct count of PRs in descending order
    ranking = sorted(module_pr_counts, key=lambda x: x[1], reverse=True)

    # Prepare data for csv, only including module names from the loaded data
    csv_data = [(module_name, pr_count) for module_name, pr_count in ranking if module_name.replace('.__init__', '') not in module_names]

    # Write data to a csv file
    with open('ranking.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["module_name", "pr_count"])  # Write header
        writer.writerows(csv_data)  # Write data


if __name__ == "__main__":
    import utils 
    call_graph_location = '/projects/salt/salt_64038.json'
    project_root_dir = '/projects/salt'
    project_name = 'salt'
    modules_dir = os.path.join(project_root_dir, project_name)
    processed_call_graph = utils.get_call_graph(modules_dir, call_graph_location, project_name, out_dir="./salt_64038_processed.json")



   