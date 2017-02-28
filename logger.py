import logging, time
import sys
import logging.handlers
import os
LOG_FILE_PATH = "log/all.log"
log_dir = os.path.dirname(LOG_FILE_PATH)
if log_dir and not os.path.isdir(log_dir):
    os.mkdir(log_dir)

FILE_LOG_LEVEL = "DEBUG"

CONSOLE_LOG_LEVEL = "INFO"

MEMORY_LOG_LEVEL = "ERROR"

URGENT_LOG_LEVEL = "CRITICAL"

MAPPING = {"CRITICAL": 50,
           "ERROR": 40,
           "WARNING": 30,
           "INFO": 20,
           "DEBUG": 10,
           "NOTSET": 0,
           }


class Logger:
    """
    This logger contains three handlers:
    1.RotatingFileHandler, handler for logging to a set of files, which switches from one file
      to the next when the current file reaches a certain size.
    2.StreamHandler, writes logging records, appropriately formatted to a stream
    """

    def __init__(self,log_file, file_level, console_level):
        self.file_level = file_level
        self.logger = logging.getLogger("InternetSimulator")
        self.fh = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=1024 * 1024 * 10, backupCount=10,
                                                       encoding="utf-8")
        self.ch = logging.StreamHandler()
        self.config(file_level, console_level)

    def config(self, file_level, console_level):
        """
        Settings of the logger object.
        Types of handlers and their log level,log format are defined.
        """
        self.fh.setLevel(MAPPING[file_level])
        self.logger.setLevel(MAPPING[file_level])

        self.fh.setLevel(MAPPING[file_level])

        self.ch.setLevel(MAPPING[console_level])

        formatter = logging.Formatter("%(asctime)s *%(levelname)s* : %(message)s", '%Y-%m-%d %H:%M:%S')
        self.ch.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.ch)
        self.logger.addHandler(self.fh)

    @staticmethod
    def get_date():
        return time.strftime('%Y-%m-%d', time.localtime(time.time()))

    @staticmethod
    def hang_process():
        a = raw_input("Do you want to continue y/n ?")
        if a != "y":
            sys.exit(0)

    def debug(self, msg):
        """
        Record debug level message
        """
        if msg is not None:
            self.logger.debug(msg)

    def info(self, msg):
        """
        Record info level message
        """
        if msg is not None:
            self.logger.info(msg)

    def warning(self, msg):
        """
        Record warning level message
        """
        if msg is not None:
            self.logger.warning(msg)

    def error(self, msg):
        """
        Record error level message
        """
        if msg is not None:
            self.logger.error(msg)

    def critical(self, msg):
        """
        Record critical level message
        """
        if msg is not None:
            self.logger.critical(msg)


##########################################################################
# Note, if you want to use this module, just import this LOG instance.
##########################################################################
LOG = Logger(LOG_FILE_PATH, FILE_LOG_LEVEL, CONSOLE_LOG_LEVEL)
