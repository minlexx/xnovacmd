# -*- coding: utf-8 -*-
import unittest

from ui.xnova.xn_parser import parse_time_left_str, parse_build_total_time_sec

from ui.xnova.xn_parser_techtree import TechtreeParser
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_imperium import ImperiumParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_fleet import FleetsMaxParser

from ui.xnova.xn_parser_planet_buildings import PlanetBuildingsAvailParser, \
    PlanetBuildingsProgressParser
from ui.xnova.xn_parser_shipyard import parse_js_array_decl


def read_test_page(page_name: str) -> str:
    pages_dir = 'tests/test_pages/'
    fn = pages_dir + page_name
    ret = None
    with open(fn, mode='r', encoding='utf-8') as f:
        ret = f.read()
    return ret


class TestParser(unittest.TestCase):
    def test_parse_time_left(self):
        # with days
        t = parse_time_left_str('1:3:25:50')
        self.assertEqual(t, (27, 25, 50))
        # days with no seconds
        t = parse_time_left_str('1:3:25:')
        self.assertEqual(t, (27, 25, 0))
        # hh:mm:ss
        t = parse_time_left_str('8:59:9')
        self.assertEqual(t, (8, 59, 9))
        # mm:ss
        t = parse_time_left_str('8:31')
        self.assertEqual(t, (0, 8, 31))
        # mm:ss with no seconds
        t = parse_time_left_str('38:')
        self.assertEqual(t, (0, 38, 0))
        # only seconds
        t = parse_time_left_str('12')
        self.assertEqual(t, (0, 0, 12))

    def test_parse_build_total_time(self):
        # with days
        secs = parse_build_total_time_sec('2 д. 3 ч. 51 мин. 30 с.')
        self.assertEqual(secs, 2*24*3600 + 3*3600 + 51*60 + 30)
        # with hours
        secs = parse_build_total_time_sec('4 ч. 1 мин. 50 с.')
        self.assertEqual(secs, 14510)
        # with mins, secs
        secs = parse_build_total_time_sec('34 мин. 54 с.')
        self.assertEqual(secs, 2094)
        # secs
        secs = parse_build_total_time_sec('41 с.')
        self.assertEqual(secs, 41)

    def test_parse_js_array_decl(self):
        # random string
        self.assertIsNone(parse_js_array_decl('abc'))
        # not full string
        s = 'c = new Array('
        self.assertIsNone(parse_js_array_decl('c = new Array('))
        # simple ints array
        self.assertEqual(parse_js_array_decl('c = new Array(11,123,4567);'), [11, 123, 4567])
        # simple strings array
        self.assertEqual(parse_js_array_decl("b = new Array('Корсар','Звезда смерти');"),
                         ['Корсар', 'Звезда смерти'])
        # test skip empty parts
        self.assertEqual(parse_js_array_decl("c = new Array(11,123,4567,'');"), [11, 123, 4567])

    def test_parse_building_downgrade(self):
        content = read_test_page('building_downgrade.html')
        self.assertIsNotNone(content)
        parser = PlanetBuildingsProgressParser()
        parser.parse_page_content(content)
        self.assertEqual(len(parser.builds_in_progress), 1)
        self.assertTrue(parser.builds_in_progress[0].is_downgrade)

    def test_parse_techtree(self):
        ttp = TechtreeParser()
        content = read_test_page('techtree.html')
        self.assertIsNotNone(content)
        ttp.parse_page_content(content)
        self.assertEqual(len(ttp.techtree), 65)
        self.assertEqual(ttp.techtree[0], (1, 'Рудник металла', 'building'))
        self.assertEqual(ttp.techtree[12], (33, 'Терраформер', 'building'))
        self.assertEqual(ttp.techtree[len(ttp.techtree)-1], \
            (503, 'Межпланетная ракета', 'defense'))

    def test_parse_self_user_info(self):
        content = read_test_page('self_user_info.html')
        self.assertIsNotNone(content)
        uip = UserInfoParser()
        uip.parse_page_content(content)
        #
        self.assertEqual(uip.buildings, 1398715)
        self.assertEqual(uip.buildings_rank, 48)
        self.assertEqual(uip.fleet, 101486)
        self.assertEqual(uip.fleet_rank, 43)
        self.assertEqual(uip.defense, 105220)
        self.assertEqual(uip.defense_rank, 65)
        self.assertEqual(uip.science, 400604)
        self.assertEqual(uip.science_rank, 47)
        self.assertEqual(uip.total, 2006024)
        self.assertEqual(uip.rank, 52)
        self.assertEqual(uip.main_planet_name, 'Arnon')
        self.assertEqual(uip.main_planet_coords.coords_str(), '[1:7:9]')
        self.assertEqual(uip.alliance_name, 'Fury')

    def test_parse_fleetsmax(self):
        parser = FleetsMaxParser()
        content = read_test_page('fleet.html')
        self.assertIsNotNone(content)
        parser.parse_page_content(content)
        self.assertEqual(parser.fleets_cur, 6)
        self.assertEqual(parser.fleets_max, 14)
        self.assertEqual(parser.expeditions_cur, 0)
        self.assertEqual(parser.expeditions_max, 2)

    def test_parse_imperium(self):
        content = read_test_page('imperium.html')
        self.assertIsNotNone(content)
        parser = ImperiumParser()
        parser.parse_page_content(content)
        planets = parser.planets
        #
        self.assertEqual(len(planets), 13)
        self.assertEqual(planets[0].name, 'Osmon')
        self.assertEqual(planets[0].coords.coords_str(), '[1:7:6]')
        self.assertEqual(planets[0].is_base, False)
        self.assertEqual(planets[0].is_moon, False)
        self.assertEqual(planets[2].is_base, True)
        self.assertEqual(planets[12].name, 'Geminate')
        #
        self.assertEqual(planets[2].planet_id, 69255)
        self.assertEqual(planets[1].pic_url,
            'skins/default/planeten/small/s_normaltempplanet08.jpg')
        self.assertEqual(planets[3].fields_busy, 183)
        self.assertEqual(planets[3].fields_total, 209)
        # check resources
        self.assertEqual(planets[4].res_current.met, 99669)
        self.assertEqual(planets[4].res_current.cry, 27001)
        self.assertEqual(planets[4].res_current.deit, 27142)
        # rph
        self.assertEqual(planets[5].res_per_hour.met, 45426)
        self.assertEqual(planets[5].res_per_hour.cry, 26029)
        self.assertEqual(planets[5].res_per_hour.deit, 7790)
        # energy left
        self.assertEqual(planets[7].energy.energy_left, 25)

