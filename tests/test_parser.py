# -*- coding: utf-8 -*-
import unittest

from ui.xnova.xn_parser import parse_time_left_str, \
    parse_build_total_time_sec

from ui.xnova.xn_data import XNCoords, XNFlight, \
    XNPlanetBuildingItem, XNPlanet

from ui.xnova.xn_parser_techtree import TechtreeParser
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_imperium import ImperiumParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_fleet import FleetsMaxParser
from ui.xnova.xn_parser_curplanet import CurPlanetParser
from ui.xnova.xn_parser_planet_energy import PlanetEnergyResParser
from ui.xnova.xn_parser_galaxy import GalaxyParser

from ui.xnova.xn_parser_planet_buildings import \
    PlanetBuildingsAvailParser, PlanetBuildingsProgressParser
from ui.xnova.xn_parser_shipyard import parse_js_array_decl, \
    ShipyardShipsAvailParser, ShipyardBuildsInProgressParser
from ui.xnova.xn_parser_research import ResearchAvailParser


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
        self.assertEqual(parse_js_array_decl('c = new Array(11,123,4567);'), \
                         [11, 123, 4567])
        # simple strings array
        self.assertEqual(parse_js_array_decl(
                    "b = new Array('Корсар','Звезда смерти');"),
                    ['Корсар', 'Звезда смерти'])
        # test skip empty parts
        self.assertEqual(parse_js_array_decl("c = new Array(11,123,4567,'');"), \
                         [11, 123, 4567])

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

    def test_parse_overview_1(self):
        content = read_test_page('overview.html')
        self.assertIsNotNone(content)
        parser = OverviewParser()
        parser.parse_page_content(content)
        #
        self.assertEqual(str(parser.server_time), '2016-01-06 16:06:16')
        self.assertEqual(parser.new_messages_count, 0)
        self.assertEqual(parser.online_players, 51)
        self.assertFalse(parser.in_RO)
        self.assertEqual(parser.account.login, 'minlexx')
        self.assertEqual(parser.account.ref_link, \
            'http://uni4.xnova.su/?71995')
        self.assertEqual(parser.account.id, 71995)
        #
        self.assertEqual(parser.account.scores.buildings, 1398843)
        self.assertEqual(parser.account.scores.fleet, 110307)
        self.assertEqual(parser.account.scores.defense, 105220)
        self.assertEqual(parser.account.scores.science, 400604)
        self.assertEqual(parser.account.scores.total, 2014973)
        self.assertEqual(parser.account.scores.rank, 52)
        self.assertEqual(parser.account.scores.rank_delta, 0)
        self.assertEqual(parser.account.scores.industry_level, 33)
        self.assertEqual(parser.account.scores.industry_exp, (18043, 35937))
        self.assertEqual(parser.account.scores.military_level, 25)
        self.assertEqual(parser.account.scores.military_exp, (575, 625))
        self.assertEqual(parser.account.scores.credits, 63)
        self.assertEqual(parser.account.scores.fraction, 'Древние')
        self.assertEqual(parser.account.scores.wins, 1399)
        self.assertEqual(parser.account.scores.losses, 29)

    def test_parse_overview_flights(self):
        content = read_test_page('overview.html')
        self.assertIsNotNone(content)
        parser = OverviewParser()
        parser.parse_page_content(content)
        #
        flights = parser.flights
        #
        self.assertEqual(len(flights), 10)
        #
        # check first flight very very tightly
        self.assertEqual(flights[0].mission, 'owndeploy')
        self.assertEqual(flights[0].direction, 'return')
        self.assertEqual(flights[0].src.target_name, 'Geminate')
        self.assertEqual(flights[0].src.target_type, XNCoords.TYPE_PLANET)
        self.assertEqual(flights[0].src.galaxy, 4)
        self.assertEqual(flights[0].src.system, 100)
        self.assertEqual(flights[0].src.position, 5)
        self.assertEqual(flights[0].dst.target_name, 'Rens')
        self.assertEqual(flights[0].dst.target_type, XNCoords.TYPE_PLANET)
        self.assertEqual(flights[0].dst.galaxy, 3)
        self.assertEqual(flights[0].dst.system, 130)
        self.assertEqual(flights[0].dst.position, 5)
        self.assertTrue(flights[0].is_our_fleet)
        self.assertEqual(flights[0].seconds_left, 53)
        self.assertEqual(flights[0].enemy_name, '')
        # check resources
        self.assertEqual(flights[0].res.met, 0)
        self.assertEqual(flights[0].res.cry, 0)
        self.assertEqual(flights[0].res.deit, 1000000)
        # check ships
        self.assertEqual(flights[0].ships.mt, 3000)
        self.assertEqual(flights[0].ships.bt, 150)
        self.assertEqual(flights[0].ships.li, 0)
        self.assertEqual(flights[0].ships.ti, 0)
        self.assertEqual(flights[0].ships.rab, 50)
        #
        # flight 2 direction
        self.assertEqual(flights[1].direction, 'flight')
        #
        # flight 3 mission
        self.assertEqual(flights[2].mission, 'ownbase')
        # flight 3 src type
        self.assertEqual(flights[2].src.target_type, XNCoords.TYPE_WARBASE)
        self.assertEqual(flights[2].src.target_name, 'SG Tama')
        self.assertEqual(flights[2].ships.f_corsair, 2474)
        #
        # flight 5 mission
        self.assertEqual(flights[4].mission, 'owntransport')
        #
        # flight 4 enemy attack
        self.assertEqual(flights[3].mission, 'attack')
        self.assertEqual(flights[3].direction, 'flight')
        self.assertEqual(flights[3].seconds_left, 1472)
        self.assertEqual(flights[3].is_our_fleet, False)
        self.assertEqual(flights[3].enemy_name, 'ScumWir')
        self.assertEqual(flights[3].src.target_name, 'Луна')
        self.assertEqual(flights[3].src.target_type, XNCoords.TYPE_MOON)
        self.assertEqual(flights[3].src.galaxy, 1)
        self.assertEqual(flights[3].src.system, 233)
        self.assertEqual(flights[3].src.position, 9)
        self.assertEqual(flights[3].dst.target_name, 'Tama')
        self.assertEqual(flights[3].dst.target_type, XNCoords.TYPE_PLANET)
        self.assertEqual(flights[3].dst.galaxy, 1)
        self.assertEqual(flights[3].dst.system, 34)
        self.assertEqual(flights[3].dst.position, 11)
        self.assertEqual(flights[3].res.met, 0)
        self.assertEqual(flights[3].res.cry, 0)
        self.assertEqual(flights[3].res.deit, 0)
        self.assertEqual(flights[3].ships.mt, 0)
        self.assertEqual(flights[3].ships.li, 1650)
        self.assertEqual(flights[3].is_hostile(), True)

    def test_parse_current_planet(self):
        content = read_test_page('overview.html')
        self.assertIsNotNone(content)
        parser = CurPlanetParser()
        parser.parse_page_content(content)
        #
        self.assertEqual(parser.cur_planet_id, 57064)
        self.assertEqual(parser.cur_planet_name, 'Tama')
        self.assertEqual(parser.cur_planet_coords.coords_str(), \
            '[1:34:11]')

    def test_parse_planet_energy_and_resources(self):
        content = read_test_page('overview.html')
        self.assertIsNotNone(content)
        parser = PlanetEnergyResParser()
        parser.parse_page_content(content)
        #
        self.assertEqual(parser.energy_left, 32)
        self.assertEqual(parser.energy_total, 13911)
        self.assertEqual(parser.res_current.met, 52366)
        self.assertEqual(parser.res_current.cry, 597882)
        self.assertEqual(parser.res_current.deit, 40792)
        self.assertEqual(parser.res_per_hour.met, 51813)
        self.assertEqual(parser.res_per_hour.cry, 26058)
        self.assertEqual(parser.res_per_hour.deit, 9390)
        self.assertEqual(parser.res_max_silos.met, 11062500)
        self.assertEqual(parser.res_max_silos.cry, 6937500)
        self.assertEqual(parser.res_max_silos.deit, 6937500)

    def test_parse_galaxy(self):
        content = read_test_page('galaxy_5_62.html')
        self.assertIsNotNone(content)
        parser = GalaxyParser()
        parser.parse_page_content(content)
        #
        galaxy_rows = parser.galaxy_rows
        #
        self.assertIsNone(galaxy_rows[0])
        self.assertIsNone(galaxy_rows[1])
        self.assertIsNone(galaxy_rows[2])
        # check 3rd planet every field
        self.assertIsNotNone(galaxy_rows[3])
        self.assertIsInstance(galaxy_rows[3], dict)
        self.assertEqual(galaxy_rows[3]['ally_planet'], 0)
        self.assertIsNone(galaxy_rows[3]['luna_temp'])
        self.assertEqual(galaxy_rows[3]['metal'], 0)
        self.assertEqual(galaxy_rows[3]['id_planet'], 82160)
        self.assertIsNone(galaxy_rows[3]['ally_web'])
        self.assertIsNone(galaxy_rows[3]['type'])
        self.assertEqual(galaxy_rows[3]['avatar'], 7)
        self.assertEqual(galaxy_rows[3]['image'], 'trockenplanet18')
        self.assertEqual(galaxy_rows[3]['onlinetime'], 0)
        self.assertEqual(galaxy_rows[3]['username'], 'ElvenShadow')
        self.assertEqual(galaxy_rows[3]['parent_planet'], 0)
        self.assertEqual(galaxy_rows[3]['ally_id'], 0)
        self.assertEqual(galaxy_rows[3]['name'], 'Андромеда')
        self.assertIsNone(galaxy_rows[3]['luna_diameter'])
        self.assertEqual(galaxy_rows[3]['crystal'], 0)
        self.assertIsNone(galaxy_rows[3]['ally_members'])
        self.assertEqual(galaxy_rows[3]['sex'], 1)
        self.assertEqual(galaxy_rows[3]['planet_type'], 1)
        self.assertEqual(galaxy_rows[3]['user_id'], 114604)
        self.assertEqual(galaxy_rows[3]['race'], 2)
        self.assertIsNone(galaxy_rows[3]['ally_name'])
        self.assertEqual(galaxy_rows[3]['destruyed'], 0)
        self.assertEqual(galaxy_rows[3]['total_points'], 3509)
        self.assertIsNone(galaxy_rows[3]['luna_id'])
        self.assertEqual(galaxy_rows[3]['last_active'], 55)
        self.assertEqual(galaxy_rows[3]['planet'], 3)
        self.assertEqual(galaxy_rows[3]['user_image'], '114604_1451805300.jpg')
        self.assertEqual(galaxy_rows[3]['authlevel'], 0)
        self.assertIsNone(galaxy_rows[3]['luna_destruyed'])
        self.assertIsNone(galaxy_rows[3]['ally_tag'])
        self.assertEqual(galaxy_rows[3]['banaday'], 0)
        self.assertEqual(galaxy_rows[3]['total_rank'], 179)
        self.assertIsNone(galaxy_rows[3]['luna_name'])
        self.assertEqual(galaxy_rows[3]['urlaubs_modus_time'], 0)
        # 5th planet is (i) player
        self.assertEqual(galaxy_rows[5]['onlinetime'], 1)
        # 6th planet is (U) player, has ally
        self.assertEqual(galaxy_rows[6]['urlaubs_modus_time'], 1)
        self.assertEqual(galaxy_rows[6]['ally_web'], '')
        self.assertEqual(galaxy_rows[6]['ally_id'], 6)
        self.assertEqual(galaxy_rows[6]['ally_members'], 7)
        self.assertEqual(galaxy_rows[6]['ally_name'], \
            'Великолепный МИФ или мифитерия Ж')
        self.assertEqual(galaxy_rows[6]['ally_tag'], 'МиФ')
        # 8th planet has moon
        self.assertEqual(galaxy_rows[8]['luna_diameter'], 8660)
        self.assertEqual(galaxy_rows[8]['luna_id'], 55144)
        self.assertEqual(galaxy_rows[8]['luna_destruyed'], 0)
        self.assertEqual(galaxy_rows[8]['luna_name'], 'Мамба')
        self.assertEqual(galaxy_rows[8]['luna_temp'], 47)
