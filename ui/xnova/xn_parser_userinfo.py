# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords
from .xn_parser import XNParserBase, safe_int
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


class UserInfoParser(XNParserBase):
    def __init__(self):
        super(UserInfoParser, self).__init__()
        # output vars
        self.buildings = 0
        self.buildings_rank = 0
        self.fleet = 0
        self.fleet_rank = 0
        self.defense = 0
        self.defense_rank = 0
        self.science = 0
        self.science_rank = 0
        self.total = 0
        self.rank = 0
        self.main_planet_name = ''
        self.main_planet_coords = XNCoords()
        self.alliance_name = ''
        # internal state vars
        self.in_main_planet = False
        self.in_alliance = False
        self.in_stats = False
        self._in = ''
        self.counter = 0

    def handle_data2(self, data: str, tag: str, attrs: list):
        if data == 'Планета:':
            self.in_main_planet = True
            self.counter = 1
            return
        if data == 'Альянс:':
            self.in_alliance = True
            self.counter = 1
            return
        if data == 'Статистика игры':
            self.in_stats = True
            return
        if (data == 'Постройки') and self.in_stats:
            self._in = 'build'
            self.counter = 1
            return
        if (data == 'Иследования') and self.in_stats:
            self._in = 'science'
            self.counter = 1
            return
        if (data == 'Флот') and self.in_stats:
            self._in = 'fleet'
            self.counter = 1
            return
        if (data == 'Оборона') and self.in_stats:
            self._in = 'defense'
            self.counter = 1
            return
        if (data == 'Всего') and self.in_stats:
            self._in = 'totals'
            self.counter = 1
            return
        #######################
        if self.in_main_planet:
            if self.counter == 1:
                # "Jita [1:7:9]"
                match = re.search(r'^(.+)\[(\d+):(\d+):(\d+)\]$', data)
                if match:
                    self.main_planet_name = match.group(1).strip()
                    g = safe_int(match.group(2))
                    s = safe_int(match.group(3))
                    p = safe_int(match.group(4))
                    self.main_planet_coords.set_gsp(g, s, p)
                    logger.debug('Got main planet: {0} {1}'.format(self.main_planet_name, self.main_planet_coords))
                self.counter = 0
                self.in_main_planet = False
            return
        if self.in_alliance:
            if self.counter == 1:
                self.alliance_name = data
                logger.debug('Got alliance: {0}'.format(self.alliance_name))
            self.in_alliance = False
            self.counter = 0
            return
        if self._in == 'build':
            if self.counter == 1:
                self.buildings = safe_int(data)
            if self.counter == 2:
                self.buildings_rank = safe_int(data)
                logger.debug('buildings {0} place {1}'.format(self.buildings, self.buildings_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'science':
            if self.counter == 1:
                self.science = safe_int(data)
            if self.counter == 2:
                self.science_rank = safe_int(data)
                logger.debug('science {0} place {1}'.format(self.science, self.science_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'fleet':
            if self.counter == 1:
                self.fleet = safe_int(data)
            if self.counter == 2:
                self.fleet_rank = safe_int(data)
                logger.debug('fleet {0} place {1}'.format(self.fleet, self.fleet_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'defense':
            if self.counter == 1:
                self.defense = safe_int(data)
            if self.counter == 2:
                self.defense_rank = safe_int(data)
                logger.debug('defense {0} place {1}'.format(self.defense, self.defense_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'totals':
            if self.counter == 1:
                self.total = safe_int(data)
            if self.counter == 2:
                self.rank = safe_int(data)
                logger.debug('total {0} rank {1}'.format(self.total, self.rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        return  # def handle_data()

