#!/usr/bin/python3
from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_imperium import ImperiumParser
from ui.xnova.xn_parser_curplanet import CurPlanetParser
from ui.xnova.xn_parser_galaxy import GalaxyParser
from ui.xnova.xn_parser_planet_buildings import PlanetBuildingsParser


def main():
    # load file
    cacher = XNovaPageCache()
    cacher.load_from_disk_cache(clean=True)
    content = cacher.get_page('overview')
    # parse overview
    p1 = OverviewParser()
    p1.parse_page_content(content)
    # parse user info
    content = cacher.get_page('self_user_info')
    p2 = UserInfoParser()
    p2.parse_page_content(content)
    # parse imperium
    p3 = ImperiumParser()
    content = cacher.get_page('imperium')
    p3.parse_page_content(content)
    # current planet
    p4 = CurPlanetParser()
    content = cacher.get_page('overview')  # can be almost any page, overview or imperium is fine
    p4.parse_page_content(content)
    # galaxy
    gp = GalaxyParser()
    content = cacher.get_page('galaxy_1_7')
    gp.parse_page_content(content)
    if gp.script_body != '':
        gp.unscramble_galaxy_script()
        print(gp.galaxy_rows)
    # planet buildings
    pbp = PlanetBuildingsParser()
    content = cacher.get_page('buildings_54450')
    pbp.parse_page_content(content)
    print(pbp.builds_in_progress)

if __name__ == "__main__":
    main()
