import requests
import db
import ast
import base64
import difflib
import json 
import os 

class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions = set()

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

def get_functions_from_code(code, prefix):
    tree = ast.parse(code)
    visitor = FunctionVisitor()
    visitor.visit(tree)
    return {f"{prefix}.{function}" for function in visitor.functions}

def get_modified_lines(diff):
    modified_lines = set()
    in_hunk = False
    line_number_base = None
    line_number_changed = None
    for line in diff:
        # A hunk starts with "@@" and ends with "@@".
        if line.startswith("@@"):
            in_hunk = not in_hunk
            if in_hunk:
                hunk_header = line.split(" ", 2)
                base_range = hunk_header[1].split(",")
                changed_range = hunk_header[2].split(",")

                line_number_base = int(base_range[0][1:])
                line_number_changed = int(changed_range[0][1:])
            continue

        if not in_hunk:
            continue

        if line.startswith("+"):
            modified_lines.add(line_number_changed)
            line_number_changed += 1
        elif line.startswith("-"):
            line_number_base += 1
        else:
            line_number_base += 1
            line_number_changed += 1

    return modified_lines


def get_changed_functions(base_code, modified_lines, prefix, prev_name=None):
    modified_functions = set()
    if prev_name:
        pass

    else:
        # if the file is not renamed, then we need to compare the functions in the base and changed files

        base_functions = get_functions_from_code(base_code, prefix)

        for function in base_functions:
            function_name = function.split('.')[-1]
            tree_of_change = ast.parse(base_code)
            for item in ast.walk(tree_of_change):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == function_name:
                    start_line = item.lineno
                    end_line = item.end_lineno
                    if any(line in modified_lines for line in range(start_line, end_line + 1)):
                        modified_functions.add(function)

    return modified_functions

def get_changed_functions_in_pr(repo_owner, repo_name, pr_number, headers):
    """
    Mine the changed functions in a PR.
    Return a tuple of 5 sets: 
    added functions, 
    deleted functions, 
    modified functions, 
    changed file names (in dot format)
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    pr_data = response.json()

    base_sha = pr_data["base"]["sha"]
    head_sha = pr_data["head"]["sha"]

    # Compare the base and head commit
    comparison_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/compare/{base_sha}...{head_sha}"
    response = requests.get(comparison_url, headers=headers)
    comparison_data = response.json()

    changed_file_names = set()
    lines_get_changed = set()
    functions_get_changed = set()

    # load module coverage for workloads
    col_module_coverage = db.Connect.get_connection().get_database('salt_workloads_module_coverage').get_collection("module_coverage")

    is_valid_pr = False


    for file in comparison_data["files"]:
        if not file["filename"].startswith("salt/") or not file["filename"].endswith(".py"):
            continue


        file_name = file["filename"].replace("/", ".").rstrip(".py")
        prev_file_name = None

        # Get base and changed file contents
        if file["status"] == "deleted":
            base_code = file["patch"]
            changed_code = ""
        else:
            response = requests.get(file["contents_url"], headers=headers)
            content = response.json()["content"]
            changed_code = base64.b64decode(content).decode('utf-8')
            base_code = ""

            if file["status"] not in ("added", "renamed"):
                url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file['filename']}?ref={base_sha}"
            elif file["status"] == "renamed":
                url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file['previous_filename']}?ref={base_sha}"
                prev_file_name = file['previous_filename'].replace("/", ".").rstrip(".py")

            if file["status"] != "added":
                response = requests.get(url, headers=headers)
                if response.status_code != 200:
                    print(f"Request to {url} failed with status code {response.status_code}")
                else:
                    try:
                        response_json = response.json()
                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON from response: {response.text}")
                    else:
                        if "content" in response_json:
                            base_content = response_json["content"]
                            base_code = base64.b64decode(base_content).decode('utf-8')

        res_lines, res_lines_number = get_lines_changed(base_code, changed_code, file_name, prev_file_name)
        lines_get_changed.update(res_lines)
        res_changed_fn = get_changed_functions(base_code, res_lines_number, file_name, prev_file_name)
        functions_get_changed.update(res_changed_fn)
      
        changed_file_names.add(file["filename"])

        '''
        Check if the PR is valid, valid means that the pr code change touch the workloads coverage
        '''
        # check if prev_file_name exists in col_module_coverage, if so replace it with file_name
        
        query_name = prev_file_name if prev_file_name else file_name

        
        existing_doc = col_module_coverage.find_one({"module_name": query_name})

        if existing_doc:
            # If a document with module_name exists in the collection,
            # the PR is valid and we should update the module_name if necessary
            is_valid_pr = True


            if prev_file_name:

                col_module_coverage.update_one(
                    {"_id": existing_doc["_id"]},
                    {"$set": {"module_name": file_name}}
                )

    
   

    return changed_file_names, lines_get_changed, functions_get_changed, is_valid_pr



def get_lines_changed(base_code, changed_code, file_name, prev_file_name=None):
    """
    we parse the 'diff' string that represents the changes made in a file. A 'diff' is a representation of changes between two sets of code. It shows what was removed and what was added.

    The 'diff' string is represented as a list of lines. Each line can be a removed line (starting with '-'), an added line (starting with '+'), a unchanged line (starting with ' '), or a header line (starting with '@@'). Header lines indicate the range of changes in the old and new file, respectively.

    First, we initialize a set to store all changed line numbers. For each line in the diff, we check the first character to determine what type of line it is. If it's a header line, we parse the line range from it for both the base file and the changed file. We also set a hunk_start variable to keep track of the first line of the current change set.

    If the line starts with '-', it's a removed line. We record the line number in the base file, which is calculated by adding the line's index within the change set (i - diff.index("@@ -" + hunk_header[1] + " +" + hunk_header[2] + " @@")) to hunk_start.

    If the line starts with '+', it's an added line. We record the line number in the changed file. Since an added line can affect the code in the surrounding lines, we also record the line number before and after the added line if they exist. This is achieved by adding or subtracting 1 from the line number and checking if these lines are within the range of the changed file.

    If the line starts with ' ', it's an unchanged line. We still need to update the line numbers in both the base file and the changed file, but we don't record these line numbers since the lines themselves haven't changed.

    Finally, we return the set of all recorded line numbers, representing all lines that are affected by the changes in the 'diff'.

    This approach ensures that we capture all lines of code that are directly changed, as well as surrounding lines that may be affected by these changes, in both the base file and the changed file. By using the line ranges indicated by the header lines, we can accurately track the line numbers in the base and changed file separately, handling cases where lines are added or removed.
    This approach provides a thorough and precise way of identifying the impact of a set of changes within a file.
    """
    diff = list(difflib.unified_diff(base_code.splitlines(), changed_code.splitlines()))
    changed_lines = set()
    changed_lines_number = set()
    in_hunk = False
    hunk_start_base = None
    hunk_start_changed = None
    prev_line_base = None
    next_line_base = None
    base_file_name = prev_file_name if prev_file_name else file_name

    for i, line in enumerate(diff):
        if line.startswith("@@"):
            in_hunk = True
            hunk_header = line.split(" ", 2)
            base_range = hunk_header[1].split(",")
            changed_range = hunk_header[2].split(",")
            hunk_start_base = int(base_range[0][1:])
            hunk_start_changed = int(changed_range[0][1:])
            hunk_line_base = hunk_start_base
            hunk_line_changed = hunk_start_changed
            next_line_base = hunk_line_base + 1
            continue

        if not in_hunk:
            continue

        if line.startswith("-"):
            # Delete line in the base file
            changed_lines.add(base_file_name + "@" + str(hunk_line_base))
            changed_lines_number.add(hunk_line_base)
            prev_line_base = hunk_line_base
            hunk_line_base += 1
            next_line_base = hunk_line_base
        elif line.startswith("+"):
            # Add line in the changed file
            if prev_line_base is not None:
                changed_lines.add(base_file_name + "@" + str(prev_line_base))
                changed_lines_number.add(hunk_line_base)
            if next_line_base is not None and next_line_base != hunk_line_base:
                changed_lines.add(base_file_name + "@" + str(next_line_base))
                changed_lines_number.add(hunk_line_base)
            hunk_line_changed += 1
        else:
            # Unchanged line
            prev_line_base = hunk_line_base
            hunk_line_base += 1
            hunk_line_changed += 1
            next_line_base = hunk_line_base + 1

    return changed_lines, changed_lines_number


if __name__ == '__main__':

    REPO_OWNER = "saltstack"
    REPO_NAME = "salt"
    GITHUB_TOKEN = "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"
    CSV_FILE = "filtered_prs.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    OUTPUT_FILE = "num_changed_files.png"
    original_cg_path = '/log2cov/log2cov-out/call_graph/salt.json'

   
    import update_cg
    changed_files, lines_changed, functions_changed = get_changed_functions_in_pr(REPO_OWNER, REPO_NAME, 62482, headers)
    print(changed_files)
    print(lines_changed)
    print(functions_changed)
    caller_functions_of_changed_functions = update_cg.get_affected_functions(original_cg_path, list(functions_changed))
    print(caller_functions_of_changed_functions)
    for i in caller_functions_of_changed_functions:
        entry = os.path.join("log2cov-out/AST/salt", *i.split('.')[:-1], i.split('.')[-1] + ".txt")
        print(entry)
        print(os.path.exists(entry))
  
    # """update callgraph with renamed functions"""

    # """remove logRes assoiciated with functions related to deleted functions"""
    # import update_cg 
    # import os 

    # call_graph = '/home/x439xu/evaluation/replication/candidate_repos/data/salt.json'
    # d = {'salt.serializers.toml.serialize', 'salt.serializers.toml.deserialize'}

    # affected_fns_del = update_cg.get_affected_functions(call_graph, d)
    # d |= affected_fns_del

    # for i in d:
    #     components = i.split('.')
    #     entry = os.path.join("log2cov-out/AST/salt", *components[:-1], components[-1] + ".txt")
    #     print(entry)
    #     # remove logres of entry in db 
        
    #     # remove entry on disk
    #     # os.remove(entry)

  

    # # program_analysis_ast for changed_file_names (make sure this replace existing ast files)
    

    # # - Update logres: delete the logRes associated to the changed functions
    # #                    perform program_analysis_logre.py on the changed functions (using added, deleted, modified), this step add new logRes
    # # - using updated logRes to get coverage database


