class LogConfig:
  __conf = {
    "pattern": set(["Log", "log", "LOG", "_LOGGER"])    
  }


  @staticmethod
  def config(name):
    return LogConfig.__conf[name]
  
  
DB_NAME = None
TASK_NAME = None
LOG_FILE_PATH = None
PROJECT_ROOT_PATH = None
CALL_GRAPH_LOCATION = None
REVERSED_CALL_GRAPH_LOCATION = None
PR_NUMBER = None

def set_db_name(db_name):
    global DB_NAME
    DB_NAME = db_name

def set_task(task_name):
    global TASK_NAME
    TASK_NAME = task_name

def set_log_file_path(log_file_path):
    global LOG_FILE_PATH
    LOG_FILE_PATH = log_file_path

def set_project_root_path(project_root_path):
    global PROJECT_ROOT_PATH
    PROJECT_ROOT_PATH = project_root_path

def set_call_graph_location(call_graph_location):
    global CALL_GRAPH_LOCATION
    CALL_GRAPH_LOCATION = call_graph_location

def set_reversed_call_graph_location(reversed_call_graph_location):
    global REVERSED_CALL_GRAPH_LOCATION
    REVERSED_CALL_GRAPH_LOCATION = reversed_call_graph_location

def set_pr_number(pr_number):
    global PR_NUMBER
    PR_NUMBER = pr_number
