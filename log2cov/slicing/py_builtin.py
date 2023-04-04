import builtins

builtin_type_methods = set(dir(builtins))

# list of all builtin types
builtin_types = [int, float, str, bool, list, tuple, dict, set, frozenset, complex, type(None)]

for t in builtin_types:
    builtin_type_methods.update(dir(t))
