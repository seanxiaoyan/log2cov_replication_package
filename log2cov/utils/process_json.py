import json 
import os
import os.path
import sys 



def get_call_graph(modules_root_dir, call_graph_path, project_name, out_dir=None):
    """
    Processes the call graph json file and returns a path to processed call graph
    """
    if not os.path.exists(call_graph_path):
        print(f"call graph not exist, invalid path: {call_graph_path}")
        exit()

    # get immediate sub-directories of the project root directory. 
    # this is used to filter out the outside libraries and built-in functions from call graph
    name_entries = os.listdir(modules_root_dir)
    for i in range(len(name_entries)):
        name_entries[i] = name_entries[i].rsplit('.',1)[0]
    name_entries.append(project_name)
    # open original call graph
    f = open(call_graph_path)
    dic = json.load(f)

    #values is a list containing method names
    #remove unrelated method names in values
    new_dic = {}
    for key,val in dic.items(): 

        # filter out the outside libraries and built-in functions for caller
        if key.split('.')[0] not in name_entries:
            continue
        key = project_name + '.' + key if key.split('.')[0] != project_name else key
        # filter out the outside libraries and built-in functions for callee
        invalid_callees = []      
        for callee in val:
            if callee.split('.')[0] not in name_entries:
                invalid_callees.append(callee)
            
        values = [x for x in val if x not in invalid_callees]
        values_1 = [project_name + '.' + x for x in values if x.split('.')[0] != project_name] + [x for x in values if x.split('.')[0] == project_name]
        # add valid caller-callee pairs to new_dic
        new_dic[key] = values_1

    json_object = json.dumps(new_dic, indent = 4) 

    if out_dir is None:
        sub_path = os.path.basename(os.path.normpath(modules_root_dir))
        if not os.path.exists("log2cov-out/call_graph"):
            os.makedirs("log2cov-out/call_graph")
        out_path = f'log2cov-out/call_graph/{sub_path}.json'
        with open(out_path, "w+") as f: 
            f.write(json_object) 
    else:
        with open(out_dir, "w+") as f: 
            f.write(json_object) 
        out_path = out_dir
        
    return out_path


def reverse_call_graph(call_graph_dir, project_name):
    """
    Reverse the call graph and return the reversed call graph
    """

    if not os.path.exists(call_graph_dir):
        print(f"call graph not exist, invalid path: {call_graph_dir}")
        exit()

    # open original call graph
    f = open(call_graph_dir)
    dic = json.load(f)

    # reverse the call graph
    new_dic = {}
    for key,val in dic.items(): 
        for callee in val:
            if callee not in new_dic:
                new_dic[callee] = []
            new_dic[callee].append(key)

    json_object = json.dumps(new_dic, indent = 4) 

    # if "../out" does not exist, create it
    if not os.path.exists("log2cov-out/reversed_call_graph"):
        os.makedirs("log2cov-out/reversed_call_graph")
    out_path = f'log2cov-out/reversed_call_graph/{project_name}.json'
    with open(out_path, "w+") as f: 
        f.write(json_object) 
    
    return out_path

