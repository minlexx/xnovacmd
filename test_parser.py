#!/usr/bin/python3
import datetime
from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_imperium import ImperiumParser
from ui.xnova.xn_parser_curplanet import CurPlanetParser
from ui.xnova.xn_parser_galaxy import GalaxyParser
from ui.xnova.xn_parser_planet_buildings import PlanetBuildingsProgressParser, PlanetBuildingsAvailParser
from ui.xnova.xn_parser_shipyard import ShipyardShipsAvailParser, ShipyardBuildsInProgressParser
from ui.xnova.xn_parser_research import ResearchAvailParser
from ui.xnova.xn_parser_techtree import TechtreeParser
from ui.xnova.xn_parser_planet_energy import PlanetEnergyParser

from ui.xnova.xn_logger import get as xn_logger_get

logger = xn_logger_get(__name__, debug=True)


def main():
    cacher = XNovaPageCache()
    cacher.save_load_encoding = 'UTF-8'  # force encoding
    cacher.load_from_disk_cache(clean=True)
    #
    # parse overview
    content = cacher.get_page('overview')
    p1 = OverviewParser()
    p1.parse_page_content(content)
    server_time = p1.server_time
    #
    # parse user info
    content = cacher.get_page('self_user_info')
    p2 = UserInfoParser()
    p2.parse_page_content(content)
    #
    # parse imperium
    p3 = ImperiumParser()
    content = cacher.get_page('imperium')
    p3.parse_page_content(content)
    #
    # current planet
    p4 = CurPlanetParser()
    content = cacher.get_page('overview')  # can be almost any page, overview or imperium is fine
    p4.parse_page_content(content)
    #
    # galaxy
    gp = GalaxyParser()
    content = cacher.get_page('galaxy_1_7')
    gp.parse_page_content(content)
    if gp.script_body != '':
        gp.unscramble_galaxy_script()
        logger.info('Galaxy rows follow:')
        logger.info(gp.galaxy_rows)
    #
    # planet buildings
    pbp = PlanetBuildingsProgressParser()
    pba = PlanetBuildingsAvailParser()
    content = cacher.get_page('buildings_57862')  # Geminate
    pba.parse_page_content(content)
    pbp.parse_page_content(content)
    logger.info('Planet buildings follow:')
    for ba in pba.builds_avail:
        logger.info(str(ba))
    logger.info('Planet builds in progress follow:')
    for bp in pbp.builds_in_progress:
        logger.info(str(bp))
    #
    # planet shipyard
    content = cacher.get_page('shipyard_57064')  # Tama's shipyard
    psyp = ShipyardBuildsInProgressParser()
    psyp.server_time = server_time
    psyp.parse_page_content(content)
    # planet ships available
    psap = ShipyardShipsAvailParser()
    psap.parse_page_content(content)
    logger.info('Planet ships available follow:')
    for sa in psap.ships_avail:
        logger.info(str(sa))
    # planet defenses
    psyp.clear()
    psyp.server_time = server_time
    psyp.parse_page_content(cacher.get_page('defense_57064'))  # Tama's defenses
    psap.clear()
    psap.parse_page_content(cacher.get_page('defense_57064'))  # Tama's defenses
    logger.info('Planet defense available follow:')
    for sa in psap.ships_avail:
        logger.info(str(sa))
    #
    # planet researches available
    content = cacher.get_page('research_57064')  # Tama
    prap = ResearchAvailParser()
    prap.server_time = server_time
    prap.parse_page_content(content)
    logger.info('Planet researches available follow:')
    for ra in prap.researches_avail:
        logger.info(str(ra))
    #
    # techtree
    ttp = TechtreeParser()
    content = cacher.get_page('techtree')
    ttp.parse_page_content(content)
    #
    # planet energy parser test
    pep = PlanetEnergyParser()
    content = cacher.get_page('shipyard_57064')  # can be any overview, research or shipyard page
    pep.parse_page_content(content)
    logger.info('Parsed planet energy status: {0}/{1}'.format(pep.energy_left, pep.energy_total))

if __name__ == "__main__":
    main()
