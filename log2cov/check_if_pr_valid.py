

import os
import sys 
import pr_changed_fn
import config
import db 
import update_cg
import utils


REPO_OWNER = "saltstack"
REPO_NAME = "salt"
GITHUB_TOKEN = "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"
CSV_FILE = "filtered_prs.csv"
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

if __name__ == "__main__":
    # check if PR is valid
    pr_number = sys.argv[1]
    project_root_dir = '/projects/salt'


    changed_files, lines_changed, functions_changed, pr_valid = pr_changed_fn.get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, pr_number, headers)


    # write pr_number and pr_valid to file
    with open('/data/pr_validation.txt', 'a') as f: 
        f.write(f"{pr_number} {pr_valid}\n")

    
    
    
    # update the call graph using the modified files
    # if changed_files is empty, exit
    if not changed_files:
        print(f"no changed files for this PR {pr_number}")
        exit()
    
    # 2. update the call graph using the modified files
    print("update call graph")
    cg_subset_path = '/tmp/salt.json'

    # make sure the cg_subset does not exist, otherwise remove it 
    if os.path.exists(cg_subset_path):
        os.remove(cg_subset_path)
    
    changed_modules = [os.path.join(project_root_dir, f) for f in changed_files if os.path.exists(os.path.join(project_root_dir, f))]
    update_cg.run_pycg('salt', changed_modules, cg_subset_path)

    # Process the sub call graph so the naming agree with the original call graph
    modules_dir = os.path.join(project_root_dir, 'salt')
    utils.get_call_graph(modules_dir, cg_subset_path, 'salt')



    # Update the origninal call graph with the sub call graph
    original_cg_path = '/log2cov/log2cov-out/call_graph/salt.json'
    update_cg.update_call_graph(original_cg_path, cg_subset_path)






