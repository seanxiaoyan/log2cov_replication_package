import program_analysis.program_analysis_ast as program_analysis_ast
import program_analysis.program_analysis_logre as program_analysis_logre
import log_analysis.process_log as process_log
import utils
import db
import mocking.mock_solution as mock_solution
import os
import pymongo
import sys 
import pr_changed_fn
import update_cg
import config


REPO_OWNER = "saltstack"
REPO_NAME = "salt"
GITHUB_TOKEN = "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"
CSV_FILE = "filtered_prs.csv"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}
OUTPUT_FILE = "num_changed_files.png"

if __name__ == "__main__":
    pr_number = sys.argv[1]
    workload_name = sys.argv[2]

    db_name = 'salt' + '_' + workload_name
    config.set_db_name(db_name)

    db_port = os.environ.get("MONGO_PORT")

    #      Impact Analysis



    print("get modified files in a PR")
    changed_files, lines_changed = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)



    # *** query the code changes in DB to see whether the change touches the code that the workloads cover

    db_workload = db.Connect.get_connection().get_database(config.DB_NAME)
    # create index for collection "impact"
    if "impact" not in db_workload.list_collection_names():
        coll_impact = db_workload.get_collection("impact")
        coll_impact.create_index([("PR_Number", pymongo.ASCENDING)], unique=True)
    # Flag to track if the change impacts coverage
    impact = "N"
    # Iterate over changed lines
    for line in lines_changed:
        # Query the coverage collection
        result = db_workload.coverage.find_one({"location": line, "covered": "Must"})
        
        if result:
            impact = "Y"
            break
    # Insert document into the impact collection
    # catch duplicatekeyerror
    try:
        db_workload.impact.insert_one({"PR_Number" : pr_number, "impact" : impact})
    except pymongo.errors.DuplicateKeyError:
        pass