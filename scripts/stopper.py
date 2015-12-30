from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger


logger = xn_logger.get('test01_stopper', debug=True)
world = XNovaWorld_instance()

try:
    existing = world.script_command
    # if this fails, no such member exists, an exception will be raised
    # else, continue
    # world.script_test01_command = 'stop'
    world.script_command = 'stop'
    # world.script_test01_command = 'pn'
    logger.info('sent "stop" command to scripts.')
except AttributeError as ea:
    logger.info('probably script is not running.')
    pass
