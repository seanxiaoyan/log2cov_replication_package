class LogConfig:
  __conf = {
    "pattern": set(["Log", "log", "LOG", "_LOGGER"]),
    "log_file_path": "/data/homeassistant.log"
    
  }


  @staticmethod
  def config(name):
    return LogConfig.__conf[name]

