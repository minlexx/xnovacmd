import logging
import sys

# global XNova Commander log message formatter
xn_log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')


# get "standard" logger for application
def get(name, debug=False):
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    # each module gets its own logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    # each module logger has its own handler attached
    log_handler = logging.StreamHandler(stream=sys.stdout)
    log_handler.setLevel(level)
    # but all loggers/handlers have the same global formatter
    log_handler.setFormatter(xn_log_formatter)
    logger.addHandler(log_handler)
    return logger
