import sys
import os
import logging
import time

from ui.xnova.xn_data import XNPlanet
from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova import xn_logger

logger = xn_logger.get('test01', debug=True)


world = XNovaWorld_instance()
planets = world.get_planets()

logger.info('Print planets:')
for planet in planets:
    logger.info(planet.name, planet.coords.coords_str())
logger.info('Done!')
