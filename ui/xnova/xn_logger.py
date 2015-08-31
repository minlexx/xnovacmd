import logging
import sys
import traceback

# global XNova Commander log message formatter
xn_log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')


# get "standard" logger for application, public api
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

#############################################
#   internal, unhandled exceptions logger   #
#############################################

uhe_logger = logging.getLogger(__name__)
uhe_logger.setLevel(logging.DEBUG)
uhe_stderr = logging.StreamHandler(stream=sys.stderr)
uhe_stderr.setLevel(logging.DEBUG)
uhe_fileh = logging.FileHandler('unhandled_exception.log', mode='wt', delay=True)
uhe_fileh.setLevel(logging.DEBUG)
uhe_stderr.setFormatter(xn_log_formatter)
uhe_fileh.setFormatter(xn_log_formatter)
uhe_logger.addHandler(uhe_fileh)
uhe_logger.addHandler(uhe_stderr)


def unhandled_exception_filter(exc_type, exc_value, exc_traceback):
    # skip ctrl+c, do we really need it in GUI app?
    if issubclass(exc_type, KeyboardInterrupt):
        # sys.exit(1)  # or, maybe ...
        # call original function
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    # get exception info as strings
    etb_s = traceback.format_exception(exc_type, exc_value, exc_traceback)
    # log
    uhe_logger.critical('Unhandled exception occured!')
    uhe_logger.critical('  Type: {0}'.format(str(exc_type)))
    uhe_logger.critical('  Value: {0}'.format(str(exc_value)))
    for line in etb_s:
        if line.endswith('\n'):
            line = line[:-1]
        uhe_logger.critical('  {0}'.format(line))


def handle_unhandled(do_handle: bool):
    if do_handle:
        sys.excepthook = unhandled_exception_filter
    else:
        sys.excepthook = sys.__excepthook__
