import shutil
import os 

def clean_output(project_name):
    out_path_ast = os.path.join("log2cov-out", "AST", project_name)
    out_path_log_seq = os.path.join("log2cov-out", "log_sequence", project_name)
    
    # remove directory
    if os.path.exists(out_path_ast):
        shutil.rmtree(out_path_ast)
    if os.path.exists(out_path_log_seq):
        shutil.rmtree(out_path_log_seq)

    out_path_reversed_call_graph = os.path.join("log2cov-out", "reversed_call_graph", project_name) + ".json"
    out_path_call_graph = os.path.join("log2cov-out", "call_graph", project_name) + ".json"

    # remove file
    if os.path.exists(out_path_reversed_call_graph):
        os.remove(out_path_reversed_call_graph)
    if os.path.exists(out_path_call_graph):
        os.remove(out_path_call_graph)
