# -*- coding: utf-8 -*-
import unittest

from ui.xnova.xn_parser import parse_time_left_str, parse_build_total_time_sec
from ui.xnova.xn_parser_shipyard import parse_js_array_decl
from ui.xnova.xn_parser_planet_buildings import PlanetBuildingsAvailParser, \
    PlanetBuildingsProgressParser


def read_test_page(page_name: str) -> str:
    pages_dir = 'tests/test_pages/'
    fn = pages_dir + page_name
    ret = None
    with open(fn, mode='r', encoding='utf-8') as f:
        ret = f.read()
    return ret


class TestParser(unittest.TestCase):
    def test_time_left(self):
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

    def test_build_total_time(self):
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
        pass
