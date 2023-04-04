
import re
import os

'''
Get all modules for generating AST
Exclude modules for testing
'''

def mod_path_dot(source_file_path, project_root_dir):
    '''
    convert module relative path to dot notation, trim of the file extension
    '''
    path = os.path.relpath(source_file_path, project_root_dir)
    return os.path.splitext(path)[0].replace("/", ".")

def get_file_path_all(dirname, file_extension, include_test=None):
    # get path to all file under a directory
    # dirname: absolute path of directory
    # file_extension: extension of the file
    modules = []
    if not include_test:
        pattern = f".*(\.{file_extension})$"
        invalid_pattern = "test_.*"
        for path, subdirs, files in os.walk(dirname, topdown=True):
            if 'test' in path:
                continue
            if files:
                for name in files :
                    if re.match(pattern, name) and not re.search(invalid_pattern, name):
                        module_name = os.path.join(path, name)
                        modules.append(module_name)
    else:
        for path, subdirs, files in os.walk(dirname, topdown=True):
            if files:
                for name in files :
                    if name.endswith(file_extension):
                        module_name = os.path.join(path, name)
                        modules.append(module_name)
    return modules

def get_test_file_paths(dirname, file_extension):
    # get path to all file under a directory
    # dirname: absolute path of directory
    # file_extension: extension of the file
    
    pattern = f"test.*(\.{file_extension})$"

    modules = []
    for path, subdirs, files in os.walk(dirname, topdown=True):

        if files:
            for name in files :
                
                if re.match(pattern, name):
                    module_path = os.path.join(path, name)                  
                    modules.append(module_path)
    return modules

if __name__ == "__main__":
    input = "salt.auth.__init__"

    if input.endswith("__init__"):
        input_mod = ".".join(input.split(".")[:-1])

    print(input_mod)