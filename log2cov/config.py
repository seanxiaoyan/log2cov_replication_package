class LogConfig:
  __conf = {
    "pattern": set(["Log", "log", "LOG", "_LOGGER"]),
    "log_file_path": "/data/homeassistant.log"
    
  }


  @staticmethod
  def config(name):
    return LogConfig.__conf[name]
  
  
DB_NAME = None
TASK_NAME = None

def set_db_name(db_name):
    global DB_NAME
    DB_NAME = db_name

def set_task(task_name):
    global TASK_NAME
    TASK_NAME = task_name

def set_log_seq_path(log_seq_path):
    global LOG_SEQ_PATH
    LOG_SEQ_PATH = log_seq_path