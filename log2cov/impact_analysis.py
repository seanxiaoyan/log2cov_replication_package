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

    db_port = os.environ.get("MONGO_PORT")

    #      Impact Analysis

    print("get modified files in a PR")
    changed_files, lines_changed, changed_fn = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)


    # *** query the code changes in DB to see whether the change touches the code that the workloads cover

    db_workload_list = ["salt_docker", "salt_maven", "salt_nginx", "salt_postgres"]
    
    # Flag to track if the change impacts coverage
    total_lines = 0
    lines_impact_different = 0 
    db_impact = db.Connect.get_connection().get_database("salt_pr_impact")
    if "impact" not in db_impact.list_collection_names():
        coll_impact = db_impact.get_collection("impact")
        coll_impact.create_index([("PR_Number", pymongo.ASCENDING)], unique=True)


    doc_to_insert = {"PR_Number" : pr_number}

    # Iterate over changed lines
    for line in lines_changed:
        total_lines += 1

        num_workload_hit = 0 
        for db_name in db_workload_list:
            db_workload = db.Connect.get_connection().get_database(db_name)
        
            # Query the coverage collection
            result = db_workload.coverage.find_one({"location": line, "covered": "Must"})
    
            if result:
                if line not in doc_to_insert:
                    doc_to_insert[line] = [db_name]
                else:
                    doc_to_insert[line].append(db_name)
                                
                num_workload_hit += 1
        
        if num_workload_hit < len(db_workload_list) and num_workload_hit != 0:
            lines_impact_different += 1

    # Insert document into the impact collection
    # catch duplicatekeyerror
    try:
        doc_to_insert["total_lines"] = total_lines
        doc_to_insert["lines_impact_different"] = lines_impact_different
        db_impact.impact.insert_one(doc_to_insert)
    except pymongo.errors.DuplicateKeyError:
        pass