from ui.xnova.xn_world import XNovaWorld_instance
from ui.xnova.xn_data import XNPlanet, XNPlanetBuildingItem
from ui.xnova import xn_logger


logger = xn_logger.get('test01_stopper', debug=True)
world = XNovaWorld_instance()


def energy_need_for_gid(gid: int, level: int) -> int:
    if (gid == 1) or (gid == 2) or (gid == 12):
        e = (10 * level) * (1.1 ** level)
        return round(e)
    if gid == 3:
        e = (20 * level) * (1.1 ** level)
        return round(e)
    return -1


try:
    planets = world.get_planets()
    if len(planets) > 0:
        planet = planets[0]
        for bitem in planet.buildings_items:
            e = energy_need_for_gid(bitem.gid, bitem.level)
            if e != -1:
                print('{0} lv {1} need {2} energy'.format(bitem.name, bitem.level, e))
except Exception as ex:
    logger.exception('Exception happened')
