import json

def traverse_call_graph(call_graph, func, visited=set()):
    if func not in visited:
        visited.add(func)
        if func in call_graph:
            for callee in call_graph[func]:
                traverse_call_graph(call_graph, callee, visited)
    return visited

def get_affected_functions(call_graph_path, modified_functions):
    with open(call_graph_path, 'r') as f:
        call_graph = json.load(f)
    affected_functions = set()
    for func in modified_functions:
        affected_functions |= traverse_call_graph(call_graph, func)
