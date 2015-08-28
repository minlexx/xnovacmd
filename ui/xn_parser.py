# -*- coding: utf-8 -*-
import re
import html.parser

from .xn_data import XNovaAccountInfo, XNCoords

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


# converts string to int, silently ignoring errors
def safe_int(data: str):
    ret = 0
    try:
        ret = int(data.replace('.', ''))
    except ValueError as ve:
        ret = 0
    return ret


# extends html.parser.HTMLParser class
# by remembering tags path
class XNParserBase(html.parser.HTMLParser):
    def __init__(self):
        super(XNParserBase, self).__init__(strict=False, convert_charrefs=True)
        self._path = []

    def get_path(self):
        path = ''
        for tag in self._path:
            if path != '':
                path += '|'
            path += tag
        return path

    def _path_append(self, tag: str, attrs: list):
        # skip "meta" tags, xnova has unclosed meta tags!
        # also as <br> <input> instead of <br />, <input />
        skip_path_tags = ['meta', 'br', 'input']
        tag_classid = ''
        if len(attrs) > 0:
            # [('class', 'col-xs-4 text-center')] ...
            tag_class = ''
            tag_id = ''
            for attr in attrs:
                if attr[0] == 'id':
                    tag_id = '#' + attr[1]
                if attr[0] == 'class':
                    tag_class = '.' + attr[1]
            tag_classid = '{0}{1}'.format(tag_class, tag_id)
            tag_classid = tag_classid.strip()
        if tag not in skip_path_tags:
            self._path.append(tag + tag_classid)

    def handle_starttag(self, tag: str, attrs: list):
        super(XNParserBase, self).handle_starttag(tag, attrs)
        self._path_append(tag, attrs)
        self.handle_path(tag, attrs, self.get_path())

    def handle_endtag(self, tag: str):
        super(XNParserBase, self).handle_endtag(tag)
        if len(self._path) > 0:
            self._path.pop()

    def handle_data(self, data: str):
        super(XNParserBase, self).handle_data(data)

    def handle_path(self, tag: str, attrs: list, path: str):
        pass

    def parse_page_content(self, page: str):
        if page:
            self.feed(page)


# parses overview page
# gets account info
class OverviewParser(XNParserBase):
    def __init__(self):
        super(OverviewParser, self).__init__()
        self.in_player_data = False
        self.in_prom_level = False
        self.in_military_level = False
        self.in_credits = False
        self.in_fraction = False
        self.in_wins = False
        self.in_losses = False
        self.in_reflink = False
        self._data_prev = ''
        self._read_next = ''
        self.account = XNovaAccountInfo()

    def handle_path(self, tag: str, attrs: list, path: str):
        attrs_s = ''
        if len(attrs) > 0:
            attrs_s = ';  attrs: {0}'.format(str(attrs))
        if (tag == 'img') and (len(attrs) > 0):
            # logger.debug('path [{0}]: {1}{2}'.format(tag, path, attrs_s))
            if ('src', '/images/wins.gif') in attrs:
                self.in_wins = True
                # logger.debug('in_wins')
            if ('src', '/images/losses.gif') in attrs:
                self.in_losses = True
                # logger.debug('in_losses')
        if (tag == 'a') and (len(attrs) > 0):
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            if ('href', '?set=refers') in attrs:
                self.in_reflink = True

    def handle_data(self, data: str):
        data_s = data.strip()
        if len(data_s) < 1:
            return
        # logger.debug('data [{0}]:    path: [{1}]'.format(data_s, self.get_path()))
        if data_s == 'Игрок:':
            self.in_player_data = True
            self._data_prev = data_s
            return
        if data_s == 'Промышленный уровень':
            self.in_prom_level = True
            self._read_next = 'prom_level'
            return
        if data_s == 'Военный уровень':
            self.in_military_level = True
            self._read_next = 'mil_level'
            return
        if data_s == 'Кредиты':
            self.in_credits = True
            self._read_next = 'credits'
            return
        if data_s == 'Фракция:':
            self.in_fraction = True
            self._read_next = 'fr'
            return
        ###########################
        if self.in_player_data:
            if self._data_prev == 'Игрок:':
                self.account.login = data_s
                self._data_prev = ''
                logger.info('Player login: {0}'.format(data_s))
                return
            if self._data_prev == 'Постройки:':
                self.account.scores.buildings = safe_int(data_s)
                self._data_prev = ''
                logger.info('Buildings: {0}'.format(self.account.scores.buildings))
                return
            if self._data_prev == 'Флот:':
                self.account.scores.fleet = safe_int(data_s)
                self._data_prev = ''
                logger.info('Fleet: {0}'.format(self.account.scores.fleet))
                return
            if self._data_prev == 'Оборона:':
                self.account.scores.defense = safe_int(data_s)
                self._data_prev = ''
                logger.info('Defense: {0}'.format(self.account.scores.defense))
                return
            if self._data_prev == 'Наука:':
                self.account.scores.science = safe_int(data_s)
                self._data_prev = ''
                logger.info('Science: {0}'.format(self.account.scores.science))
                return
            if self._data_prev == 'Всего:':
                self.account.scores.total = safe_int(data_s)
                self._data_prev = ''
                logger.info('Total: {0}'.format(self.account.scores.total))
                return
            if self._data_prev == 'Место:':
                # logger.debug('Prev.was place: {0}'.format(data_s))
                self.account.scores.rank = safe_int(data_s)
                self._data_prev = 'Место_delta:'
                return
            if self._data_prev == 'Место_delta:':
                # logger.debug('Prev.was place_delta: {0}'.format(data_s))
                if data_s == '(':
                    self._data_prev = 'Место_delta(:'
                return
            if self._data_prev == 'Место_delta(:':
                # logger.debug('Prev.was Место_delta(: {0}'.format(data_s))
                try:
                    self.account.scores.rank_delta = int(data_s.replace('.', ''))
                except ValueError as ve:
                    logger.warn('OverviewParser failed to parse player rank delta: {0}'.format(str(ve)))
                self._data_prev = ''
                self.in_player_data = False
                logger.info('Rank: {0}, delta: {1}'.format(
                    self.account.scores.rank, self.account.scores.rank_delta))
                # logger.info(str(self.account.scores))
                # logger.info(str(self.account))
                return
            # none of above matches
            self._data_prev = data_s
            return
        # end in_player_data
        if self.in_prom_level:
            if self._read_next == 'prom_level':
                # [7 из 100]
                match = re.match(r'(\d+)\sиз\s(\d+)', data_s)
                if match:  # ('7', '100')
                    self.account.scores.industry_level = int(match.group(1))
                self._read_next = 'prom_exp'
                return
            if self._read_next == 'prom_exp':
                # [342 / 343 exp]
                match = re.match(r'(\d+)\s/\s(\d+)', data_s)
                if match:  # ('342', '343')
                    exp = int(match.group(1))
                    exp_m = int(match.group(2))
                    self.account.scores.industry_exp = (exp, exp_m,)
                self._read_next = ''
                self.in_prom_level = False
                return
            return
        # end in_prom_level
        if self.in_military_level:
            if self._read_next == 'mil_level':
                # [7 из 100]
                match = re.match(r'(\d+)\sиз\s(\d+)', data_s)
                if match:  # ('7', '100')
                    self.account.scores.military_level = int(match.group(1))
                self._read_next = 'mil_exp'
                return
            if self._read_next == 'mil_exp':
                # [342 / 343 exp]
                match = re.match(r'(\d+)\s/\s(\d+)', data_s)
                if match:  # ('342', '343')
                    exp = int(match.group(1))
                    exp_m = int(match.group(2))
                    self.account.scores.military_exp = (exp, exp_m,)
                self._read_next = ''
                self.in_military_level = False
                return
            return
        if self.in_credits:
            if self._read_next == 'credits':
                self.account.scores.credits = safe_int(data_s)
                self.in_credits = False
                self._read_next = ''
            return
        if self.in_fraction:
            if self._read_next == 'fr':
                self.account.scores.fraction = data_s
                self._read_next = ''
                self.in_fraction = False
        if self.in_wins:
            logger.info('wins: %s' % data_s)
            self.account.scores.wins = safe_int(data_s)
            self.in_wins = False
        if self.in_losses:
            logger.info('losses: %s' % data_s)
            self.account.scores.losses = safe_int(data_s)
            self.in_losses = False
        if self.in_reflink:
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            logger.info('Account referral link: [{0}]'.format(data_s))
            self.account.ref_link = data_s
            match = re.search(r'/\?(\d+)$', data_s)
            if match:
                self.account.id = safe_int(match.group(1))
            self.in_reflink = False


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

    def handle_data(self, data: str):
        data_s = data.strip()
        if len(data_s) < 1:
            return
        if data_s == 'Планета:':
            self.in_main_planet = True
            self.counter = 1
            return
        if data_s == 'Альянс:':
            self.in_alliance = True
            self.counter = 1
            return
        if data_s == 'Статистика игры':
            self.in_stats = True
            return
        if (data_s == 'Постройки') and self.in_stats:
            self._in = 'build'
            self.counter = 1
            return
        if (data_s == 'Иследования') and self.in_stats:
            self._in = 'science'
            self.counter = 1
            return
        if (data_s == 'Флот') and self.in_stats:
            self._in = 'fleet'
            self.counter = 1
            return
        if (data_s == 'Оборона') and self.in_stats:
            self._in = 'defense'
            self.counter = 1
            return
        if (data_s == 'Всего') and self.in_stats:
            self._in = 'totals'
            self.counter = 1
            return
        #######################
        if self.in_main_planet:
            if self.counter == 1:
                # "Jita [1:7:9]"
                match = re.search(r'^(.+)\[(\d+):(\d+):(\d+)\]$', data_s)
                if match:
                    self.main_planet_name = match.group(1).strip()
                    g = safe_int(match.group(2))
                    s = safe_int(match.group(3))
                    p = safe_int(match.group(4))
                    self.main_planet_coords.set_gsp(g, s, p)
                    logger.info('Got main planet: {0} {1}'.format(self.main_planet_name, self.main_planet_coords))
                self.counter = 0
                self.in_main_planet = False
            return
        if self.in_alliance:
            if self.counter == 1:
                self.alliance_name = data_s
                logger.info('Got alliance: {0}'.format(self.alliance_name))
            self.in_alliance = False
            self.counter = 0
            return
        if self._in == 'build':
            if self.counter == 1:
                self.buildings = safe_int(data_s)
            if self.counter == 2:
                self.buildings_rank = safe_int(data_s)
                logger.info('buildings {0} place {1}'.format(self.buildings, self.buildings_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'science':
            if self.counter == 1:
                self.science = safe_int(data_s)
            if self.counter == 2:
                self.science_rank = safe_int(data_s)
                logger.info('science {0} place {1}'.format(self.science, self.science_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'fleet':
            if self.counter == 1:
                self.fleet = safe_int(data_s)
            if self.counter == 2:
                self.fleet_rank = safe_int(data_s)
                logger.info('fleet {0} place {1}'.format(self.fleet, self.fleet_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'defense':
            if self.counter == 1:
                self.defense = safe_int(data_s)
            if self.counter == 2:
                self.defense_rank = safe_int(data_s)
                logger.info('defense {0} place {1}'.format(self.defense, self.defense_rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        if self._in == 'totals':
            if self.counter == 1:
                self.total = safe_int(data_s)
            if self.counter == 2:
                self.rank = safe_int(data_s)
                logger.info('total {0} rank {1}'.format(self.total, self.rank))
            self.counter += 1
            if self.counter >= 3:
                self.counter = 0
                self._in = ''
            return
        return
