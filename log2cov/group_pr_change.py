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
OUTPUT_FILE = "num_changed_files.png"

def analysis_code_change(csv_path):
    if not os.path.exists(csv_path):
        print("csv file does not exist")
        exit(1)

    db_client = db.Connect.get_connection()
    pr_code_changes_db = db_client.get_database("salt_pr_code_changes")
    # create index for the collection
    if "location" not in pr_code_changes_db.list_collection_names():
        coll_code_changes = pr_code_changes_db.get_collection("modules")
        coll_code_changes.create_index([("location", pymongo.ASCENDING)], unique=True)
    
    # example of location: "salt.runner@10"

    # Iterate over the csv file, which the first column is the PR number
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pr_number = row["PR Number"]
            if not pr_number:
                print("PR number is empty, exit 1")
                exit(1)

            changed_files, lines_changed, changed_fn = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)

            # Iterate over changed lines
            for line in lines_changed:
                # Query the coverage collection
                result = pr_code_changes_db.code_changes.find_one({"location": line})
            
                # If the line is not in the collection, insert it
                if not result:
                    doc_to_insert = {"location" : line}
                    pr_code_changes_db.code_changes.insert_one(doc_to_insert)
            
if __name__ == "__main__":
    analysis_code_change(CSV_FILE)


   