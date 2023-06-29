import json
import pr_changed_fn
import subprocess
import os 


project_name = 'salt'


def update_call_graph(old_call_graph_file, increment_call_graph_file, changed_modules, file_name_map):
    updated = False
    changed_mods = ['.'.join(m.replace('/', '.').split('.')[:-1]) for m in changed_modules]



    # Load the old call graph
    with open(old_call_graph_file, 'r') as f:
        old_call_graph = json.load(f)

    # Load the increment call graph
    with open(increment_call_graph_file, 'r') as f:
        increment_call_graph = json.load(f)


    # firstly handle file renaming, delete all the callers of which the file is renamed
    renamed_mods = [file_name_map[f] for f in changed_mods if f in file_name_map]
    keys_to_delete = {k for k in old_call_graph if any(k == dm or k.startswith(dm + '.') for dm in renamed_mods)}

    # Create updated cg for handling renaming
    old_call_graph_updated = {k: v for k, v in old_call_graph.items() if k not in keys_to_delete}


    # Update the updated old call graph with the incremental call graph
    # Only update the caller that is in the changed files
    for key, val in increment_call_graph.items():
        key_valid = False

        for mod in changed_mods:
            if key.startswith(mod + '.') or key == mod:
                key_valid = True
                break
        if key_valid:
            updated = True
            old_call_graph_updated[key] = val  # insert or replace

    if updated:
        # Overwrite the old call graph file with the updated call graph
        with open(old_call_graph_file, 'w') as f:
            json.dump(old_call_graph_updated, f, indent = 4)



def run_pycg(package_name, filenames, output=None):
    command = ["pycg", "--package", package_name]

    input_files = [i for i in filenames if i.endswith(".py")]

    # Append all filenames to the command
    command.extend(input_files)

    if output is not None:
        command.extend(["-o", output])

    # Run the command
    subprocess.run(command, check=True, cwd="/projects/salt")




def get_caller_functions(call_graph, func, visited=set()):
    callers = set()
    for caller, callees in call_graph.items():
        if func in callees:
            callers.add(caller)
            if caller not in visited:
                visited.add(caller)
                callers |= get_caller_functions(call_graph, caller, visited)
    return callers

def get_affected_functions(call_graph_path, modified_functions):
    with open(call_graph_path, 'r') as f:
        call_graph = json.load(f)

    affected_functions = set()
    visited = set()

    for func in modified_functions:
    
        affected_functions |= get_caller_functions(call_graph, func, visited)

    return list(affected_functions)



def rename_callgraph_functions(callgraph_file, function_rename_mapping):
    # Load the call graph
    with open(callgraph_file, 'r') as f:
        callgraph = json.load(f)

    # Create a new call graph dictionary
    new_callgraph = {}

    for caller, callees in callgraph.items():
        # If caller is in the function rename mapping, rename it
        if caller in function_rename_mapping:
            caller = function_rename_mapping[caller]

        new_callees = []
        for callee in callees:
            # If callee is in the function rename mapping, rename it
            if callee in function_rename_mapping:
                callee = function_rename_mapping[callee]
            new_callees.append(callee)

        # Assign the renamed callees to the caller in the new call graph
        new_callgraph[caller] = new_callees

    return new_callgraph

if __name__ == "__main__":
    




    REPO_OWNER = "saltstack"
    REPO_NAME = "salt"
    GITHUB_TOKEN = "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"
    CSV_FILE = "filtered_prs.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    OUTPUT_FILE = "num_changed_files.png"





    cg_subset_path = '/tmp/salt.json'
    # make sure the cg_subset does not exist, otherwise remove it 
    if os.path.exists(cg_subset_path):
        os.remove(cg_subset_path)
    changed_files = {'salt/renderers/tomlmod.py', 'salt/serializers/tomlmod.py'}
    project_root_dir = '/projects/salt'
    changed_modules = [os.path.join(project_root_dir, f) for f in changed_files if os.path.exists(os.path.join(project_root_dir, f))]

    print(changed_modules)
    run_pycg('salt', list(changed_modules), cg_subset_path)



    # fn_set = {'serializers.toml.__virtual__'}
    # cg = '/home/x439xu/evaluation/replication/candidate_repos/data/salt.json'
    # print(get_affected_functions(cg, fn_set))


  
    # """update callgraph with renamed functions"""


    # # Usage
    # run_pycg("my_entry_point.py", package="my_package", output="output.json")

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
