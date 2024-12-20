from logging import getLogger, Formatter, StreamHandler, FileHandler, DEBUG, INFO

# Setup for the custom logger

#logger formatter setup
logger_formatter = Formatter(fmt="[{asctime}] - [MODULE]: {module} -> [FUNCTION]: {funcName} - [LEVEL]: {levelname} -> {message}", style="{")

# stream handler setup
logger_console_handler = StreamHandler()
logger_console_handler.setFormatter(logger_formatter)
logger_console_handler.setLevel(DEBUG)

# file handler setup
logger_file_handler = FileHandler(filename="autotyper.log", mode="w")
logger_file_handler.setLevel(INFO)
logger_file_handler.setFormatter(logger_formatter)

# logger setup
logger = getLogger("autotyper")
logger.setLevel(DEBUG)
logger.addHandler(logger_console_handler)
logger.addHandler(logger_file_handler)