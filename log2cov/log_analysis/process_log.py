import re 
import os



def get_regex_alternative_group(source_code_root):
    '''
    Get the alternative group of modules that can be used in Fn get_log_sequence for regex
    Return the group
    '''
    group = "(?:"

    list_of_subdir_and_files = os.listdir(source_code_root)
    for i in list_of_subdir_and_files:
        if len(i.split(".")) > 1:
            # this is file
            if i.split(".")[1] == "py":
                name = i.split(".")[0]
                group += f"{name}|"
        else:
            # this is dir
            name = i.split(".")[0]
            group += f"{name}|{name}\.|"

    group = group[:-1]
    group += ")"
    return group

def get_log_sequence(log_file, project_name, alternative_group, thread_id_index):
    '''
    Function to get the log sequence from a log file.
    return a map that the key is the thread id and value is the log sequence of that thread id 
    '''
    log_seq_map = {} # key: thread id, value: log sequence
    pattern = f"\[{project_name}\.{alternative_group}[.\w]*@([0-9]+)\]"
    p = re.compile(pattern)
    with open(log_file, 'r') as f:
        for line in f:
            capture = p.search(line)
            if capture:
                result = capture.group(0)
                # trim off the white space
                result = result.rstrip().lstrip().replace('[','').replace(']','').replace(':','@')

                # get the thread id
                thread_id = line.split(' ')[thread_id_index].replace('[','').replace(']','')

                if thread_id not in log_seq_map:
                    log_seq_map[thread_id] = result
                else:
                    log_seq_map[thread_id] += result

             
            
    # adding extra space in the end of log sequence because we use "\D" in matching logRE
    res_map = {}
    for key, value in log_seq_map.items():
        res_map[key] = value + " "

    return res_map




def dump_log_seq(log_file, project_root_dir, project_name, thread_id_index):
    '''
    Function to convert log file to log sequence and dump to file
    '''
    # get alternative group to use in regex
    alternative_group = get_regex_alternative_group(os.path.join(project_root_dir, project_name))

    # get log sequence map 
    log_seq_map = get_log_sequence(log_file, project_name, alternative_group, thread_id_index)

    # dump log sequence to file
    log_sequence = ""

    for value in log_seq_map.values():
        # key: thread id, value: log sequence
        log_sequence += value


    with open(f"log_seq.txt", 'w+') as f:
        f.write(log_sequence)
