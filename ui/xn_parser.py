# -*- coding: utf-8 -*-
import re
import html.parser
import datetime

from .xn_data import XNovaAccountInfo, XNCoords, XNFlight, XNFlightResources, XNFlightShips

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


def _parse_flight_ships(s) -> XNFlightShips:
    class _FSParser(XNParserBase):
        def __init__(self):
            super(_FSParser, self).__init__()
            self.ships = XNFlightShips()
            self._p = ''

        def handle_data(self, data: str):
            data_s = data.strip()
            if len(data_s) < 1:
                return
            # logger.debug('FSParser: data: [{0}], prev=[{1}]'.format(data_s, self._p))
            value = safe_int(data_s)
            if value > 0:
                if self._p == 'Малый транспорт:':
                    self.ships.mt = value
                elif self._p == 'Большой транспорт:':
                    self.ships.bt = value
                elif self._p == 'Лёгкий истребитель:':
                    self.ships.li = value
                elif self._p == 'Тяжёлый истребитель:':
                    self.ships.ti = value
                elif self._p == 'Крейсер:':
                    self.ships.crus = value
                elif self._p == 'Линкор:':
                    self.ships.link = value
                elif self._p == 'Колонизатор:':
                    self.ships.col = value
                elif self._p == 'Переработчик:':
                    self.ships.rab = value
                elif self._p == 'Шпионский зонд:':
                    self.ships.spy = value
                elif self._p == 'Бомбардировщик:':
                    self.ships.bomber = value
                elif self._p == 'Солнечный спутник:':
                    self.ships.ss = value
                elif self._p == 'Уничтожитель:':
                    self.ships.unik = value
                elif self._p == 'Звезда смерти:':
                    self.ships.zs = value
                elif self._p == 'Линейный крейсер:':
                    self.ships.lk = value
                elif self._p == 'Передвижная база:':
                    self.ships.warbase = value
                elif self._p == 'Корсар:':
                    self.ships.f_corsair = value
                elif self._p == 'Корвет:':
                    self.ships.f_corvett = value
                elif self._p == 'Перехватчик:':
                    self.ships.f_ceptor = value
                elif self._p == 'Дредноут:':
                    self.ships.f_dread = value
                else:
                    raise ValueError('Unknown ship type: "{0}"'.format(self._p))
            else:
                self._p = data_s

    parser = _FSParser()
    parser.parse_page_content(s)
    return parser.ships


def _parse_flight_resources(s) -> XNFlightResources:
    class _FRParser(XNParserBase):
        def __init__(self):
            super(_FRParser, self).__init__()
            self.res = XNFlightResources()
            self._c = 0

        def handle_data(self, data: str):
            data_s = data.strip()
            if len(data_s) < 1:
                return
            self._c += 1
            # logger.debug('FRParser data [{0}] c={1}'.format(data_s, self._c))
            if self._c == 2:
                self.res.met = safe_int(data_s)
            elif self._c == 4:
                self.res.cry = safe_int(data_s)
            elif self._c == 6:
                self.res.deit = safe_int(data_s)

    parser = _FRParser()
    parser.parse_page_content(s)
    fr = parser.res
    return fr


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
        self.in_flight = False
        self.in_flight_time = False
        self.in_flight_time_arrival = False
        self._data_prev = ''
        self._read_next = ''
        self._num_a_with_tooltip = 0
        self._num_a_with_galaxy = 0
        self.account = XNovaAccountInfo()
        self.flights = []
        self._cur_flight = XNFlight()
        self._cur_flight_arrive_dt = None

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
            return
        if (tag == 'a') and (len(attrs) > 0):
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            if ('href', '?set=refers') in attrs:
                self.in_reflink = True
                return
            if self.in_flight:
                data_tooltip_content = ''
                href = ''
                for attr_tuple in attrs:
                    if attr_tuple[0] == 'data-tooltip-content':
                        data_tooltip_content = attr_tuple[1]
                    if attr_tuple[0] == 'href':
                        href = attr_tuple[1]
                # this may be flee compisition reference or resources jar
                if data_tooltip_content != '':
                    # <table width=200><tr><td width=75% align=left><font color=white>Малый транспорт:<font>
                    # </td><td width=25% align=right><font color=white>2<font>
                    # or ... <font color=white>Металл<font></td> ... <font color=white>18.000<font> ...
                    # logger.debug('tt: [{0}]'.format(data_tooltip_content))
                    self._num_a_with_tooltip += 1
                    if self._num_a_with_tooltip == 1:
                        fs = _parse_flight_ships(data_tooltip_content)
                        # logger.debug('  ships: {0}'.format(fs))
                        self._cur_flight.ships = fs
                    elif self._num_a_with_tooltip == 2:
                        fr = _parse_flight_resources(data_tooltip_content)
                        # logger.debug('  resources: {0}'.format(fr))
                        self._cur_flight.res = fr
                # or it may be a planet reference
                if href != '':
                    # logger.debug('<a href=[{0}]'.format(href))
                    # <a href="?set=galaxy&amp;r=3&amp;galaxy=3&amp;system=129"
                    if href.startswith('?set=galaxy&r=3&galaxy='):
                        # logger.debug('    galaxy reference? [{0}]'.format(href))
                        self._num_a_with_galaxy += 1
            return
        # handle flying fleets
        if (tag == 'span') and (len(attrs) > 0):
            span_class = ''
            for attr_tuple in attrs:
                if attr_tuple[0] == 'class':
                    span_class = attr_tuple[1]
            if span_class == '':
                # skip all <span> without class
                return
            # check that span class is flight:
            #  class="return ownattack"
            #  class="flight ownattack"
            #  class="return owndeploy"
            classes = span_class.split(' ')
            flight_dirs = ['flight', 'return']
            flight_missions = ['owndeploy', 'owntransport', 'ownattack', 'ownespionage',
                               'ownharvest', 'owncolony', 'ownfederation', 'ownmissile',
                               'owndestroy', 'ownhold']
            flight_dir = ''
            flight_mission = ''
            for a_sclass in classes:
                if a_sclass in flight_dirs:
                    flight_dir = a_sclass
                if a_sclass in flight_missions:
                    flight_mission = a_sclass
            if (flight_dir == '') or (flight_mission == ''):
                # this not span about flying fleet
                return
            # logger.debug('--> In flight: {0}'.format(str(classes)))  # ['return', 'owntransport']
            self.in_flight = True
            self._num_a_with_tooltip = 0
            self._num_a_with_galaxy = 0
            self._cur_flight = XNFlight()
            self._cur_flight.direction = flight_dir
            self._cur_flight.mission = flight_mission
            return
        if (tag == 'tr') and (len(attrs) > 0):
            tr_class = ''
            for attr_tuple in attrs:
                if attr_tuple[0] == 'class':
                    tr_class = attr_tuple[1]
            if (tr_class == 'flight') or (tr_class == 'return'):
                # table row with flight info, or building (TODO)
                self.in_flight_time = True
        if (tag == 'font') and (len(attrs) > 0):
            if self.in_flight_time:
                font_color = ''
                for attr_tuple in attrs:
                    if attr_tuple[0] == 'color':
                        font_color = attr_tuple[1]
                if font_color == 'lime':
                    self.in_flight_time_arrival = True
                    # <font color="lime">13:59:31</font>
                    # next data item will be arrival time

    def handle_endtag(self, tag: str):
        if tag == 'span':
            if self.in_flight:
                self.in_flight = False
                self._num_a_with_tooltip = 0
                self._num_a_with_galaxy = 0
                # save flight
                self._cur_flight.arrive_datetime = self._cur_flight_arrive_dt
                self.flights.append(self._cur_flight)
                logger.info('Flight: {0}'.format(self._cur_flight))
                self._cur_flight = None
                self._cur_flight_arrive_dt = None
                return
        if tag == 'font':
            if self.in_flight_time:
                if self.in_flight_time_arrival:
                    # end processing of <font color="lime">13:59:31</font>
                    self.in_flight_time = False
                    self.in_flight_time_arrival = False

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
        if self._num_a_with_galaxy > 0:
            # logger.debug('{0}: galaxy ref [{1}]'.format(self._num_a_with_galaxy, data_s))
            xc = XNCoords()
            try:
                xc.parse_str(data_s, raise_on_error=True)
                if self._num_a_with_galaxy == 1:
                    self._cur_flight.src = xc
                elif self._num_a_with_galaxy == 2:
                    self._cur_flight.dst = xc
                    self._num_a_with_galaxy = 0  # stop here
            except ValueError as ve:
                pass
        if self.in_flight_time and self.in_flight_time_arrival:
            # 13:59:31  (hr:min:sec)
            match = re.search(r'(\d+):(\d+):(\d+)', data_s)
            if match:
                h = safe_int(match.group(1))
                m = safe_int(match.group(2))
                s = safe_int(match.group(3))
                dt_now = datetime.datetime.today()
                dt_arrive = datetime.datetime(dt_now.year, dt_now.month, dt_now.day,
                                              hour=h, minute=m, second=s)
                self._cur_flight_arrive_dt = dt_arrive
                # logger.debug('arrive ts: {0}'.format(dt_arrive))
            return
        return   # from def handle_data()


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
        return  # def handle_data()
