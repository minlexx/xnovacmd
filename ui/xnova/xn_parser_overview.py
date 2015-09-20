# -*- coding: utf-8 -*-
import re
import datetime

from .xn_data import XNAccountInfo, XNCoords, XNFlight, XNResourceBundle, XNShipsBundle
from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


def _parse_flight_ships(s) -> XNShipsBundle:
    class _FSParser(XNParserBase):
        def __init__(self):
            super(_FSParser, self).__init__()
            self.ships = XNShipsBundle()
            self._p = ''

        def handle_data2(self, data: str, tag: str, attrs: list):
            value = safe_int(data)
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
                self._p = data

    parser = _FSParser()
    parser.parse_page_content(s)
    return parser.ships


def _parse_flight_resources(s) -> XNResourceBundle:
    class _FRParser(XNParserBase):
        def __init__(self):
            super(_FRParser, self).__init__()
            self.res = XNResourceBundle()
            self._c = 0

        def handle_data2(self, data: str, tag: str, attrs: list):
            self._c += 1
            if self._c == 2:
                self.res.met = safe_int(data)
            elif self._c == 4:
                self.res.cry = safe_int(data)
            elif self._c == 6:
                self.res.deit = safe_int(data)

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
        self.in_enemy_message_span = False
        self._data_prev = ''
        self._read_next = ''
        self._num_a_with_tooltip = 0
        self._num_a_with_galaxy = 0
        self.account = XNAccountInfo()
        self.flights = []
        self._cur_flight = XNFlight()
        self._cur_flight_arrive_dt = None
        self._cur_flight_src_nametype = ('', 0)
        self._cur_flight_dst_nametype = ('', 0)
        self.server_time = datetime.datetime.today()
        self.in_server_time = False

    def handle_starttag(self, tag: str, attrs: list):
        super(OverviewParser, self).handle_starttag(tag, attrs)
        if (tag == 'img') and (len(attrs) > 0):
            if ('src', '/images/wins.gif') in attrs:
                self.in_wins = True
            if ('src', '/images/losses.gif') in attrs:
                self.in_losses = True
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
                    # logger.debug('<a with tooltip:: [{0}]'.format(data_tooltip_content))
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
                    if href.startswith('?set=galaxy'):
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
            # check special span case that is send message to enemy attacker:
            # <span class='sprite skin_m'></span>
            if span_class == 'sprite skin_m':
                self.in_enemy_message_span = True
                return
            # check that span class is flight:
            #  class="return ownattack"
            #  class="flight ownattack"
            #  class="return owndeploy"
            classes = span_class.split(' ')
            flight_dir = ''
            flight_mission = ''
            for a_sclass in classes:
                if a_sclass in XNFlight.FLIGHT_DIRS:
                    flight_dir = a_sclass
                if a_sclass in XNFlight.FLIGHT_MISSIONS:
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
                # table row with flight info, or building
                self.in_flight_time = True
        # change flight time detection from "arrival time" in font tag
        # to "time left" in <div id="bxxfs2" class="z">8:59:9</div>
        # which comes just before the font tag
        if (tag == 'div') and (len(attrs) > 0):
            # try to find a server time, expressed in tag:
            # <div id="clock" class="pull-right">30-08-2015 12:10:08</div>
            # or try to find fleet arrival time, expressed in tag:
            # <div id="bxxfs2" class="z">8:59:9</div>
            div_id = ''
            div_class = ''
            for attr_tuple in attrs:
                if attr_tuple[0] == 'class':
                    div_class = attr_tuple[1]
                if attr_tuple[0] == 'id':
                    div_id = attr_tuple[1]
            # <div id="clock" class="pull-right">30-08-2015 12:10:08</div>
            if (div_class == 'pull-right') and (div_id == 'clock'):
                self.in_server_time = True
            # <div id="bxxfs2" class="z">8:59:9</div>
            if (div_class == 'z') and self.in_flight_time:
                self.in_flight_time_arrival = True

    def handle_endtag(self, tag: str):
        super(OverviewParser, self).handle_endtag(tag)
        if tag == 'span':
            # special case when enemy attack fleet, contains inner span tag
            if self.in_enemy_message_span:
                self.in_enemy_message_span = False
                return
            if self.in_flight:
                # save flight arrive time
                self._cur_flight.arrive_datetime = self._cur_flight_arrive_dt
                # validate this is flight
                if (not self._cur_flight.src.is_empty()) and (not self._cur_flight.dst.is_empty()):
                    # only having source/destination set
                    if len(self._cur_flight.ships) > 0:
                        # only actually having ships in it
                        self.flights.append(self._cur_flight)
                        logger.info('Flight: {0}'.format(self._cur_flight))
                # logger.debug('handle_endtag(span): ending flight')
                self.in_flight = False
                self._num_a_with_tooltip = 0
                self._num_a_with_galaxy = 0
                self._cur_flight = None
                self._cur_flight_arrive_dt = None
                self._cur_flight_src_nametype = ('', 0)
                self._cur_flight_dst_nametype = ('', 0)
            return
        # ^^ channged flight time detection from font tag to div
        if (tag == 'div') and self.in_flight_time_arrival and self.in_flight_time:
            # end processing of <div id="bxxfs2" class="z">8:59:9</div>
            self.in_flight_time = False
            self.in_flight_time_arrival = False
        if (tag == 'div') and self.in_server_time:
            self.in_server_time = False
            return

    def handle_data2(self, data: str, tag: str, attrs: list):
        # logger.debug('data [{0}]:    path: [{1}]'.format(data, self.get_path()))
        if data == 'Игрок:':
            self.in_player_data = True
            self._data_prev = data
            return
        if data == 'Промышленный уровень':
            self.in_prom_level = True
            self._read_next = 'prom_level'
            return
        if data == 'Военный уровень':
            self.in_military_level = True
            self._read_next = 'mil_level'
            return
        if data == 'Кредиты':
            self.in_credits = True
            self._read_next = 'credits'
            return
        if data == 'Фракция:':
            self.in_fraction = True
            self._read_next = 'fr'
            return
        ###########################
        if self.in_player_data:
            if self._data_prev == 'Игрок:':
                self.account.login = data
                self._data_prev = ''
                logger.info('Player login: {0}'.format(data))
                return
            if self._data_prev == 'Постройки:':
                self.account.scores.buildings = safe_int(data)
                self._data_prev = ''
                logger.info('Buildings: {0}'.format(self.account.scores.buildings))
                return
            if self._data_prev == 'Флот:':
                self.account.scores.fleet = safe_int(data)
                self._data_prev = ''
                logger.info('Fleet: {0}'.format(self.account.scores.fleet))
                return
            if self._data_prev == 'Оборона:':
                self.account.scores.defense = safe_int(data)
                self._data_prev = ''
                logger.info('Defense: {0}'.format(self.account.scores.defense))
                return
            if self._data_prev == 'Наука:':
                self.account.scores.science = safe_int(data)
                self._data_prev = ''
                logger.info('Science: {0}'.format(self.account.scores.science))
                return
            if self._data_prev == 'Всего:':
                self.account.scores.total = safe_int(data)
                self._data_prev = ''
                logger.info('Total: {0}'.format(self.account.scores.total))
                return
            if self._data_prev == 'Место:':
                # logger.debug('Prev.was place: {0}'.format(data))
                self.account.scores.rank = safe_int(data)
                self._data_prev = 'Место_delta:'
                return
            if self._data_prev == 'Место_delta:':
                # logger.debug('Prev.was place_delta: {0}'.format(data))
                if data == '(':
                    self._data_prev = 'Место_delta(:'
                return
            if self._data_prev == 'Место_delta(:':
                # logger.debug('Prev.was Место_delta(: {0}'.format(data))
                try:
                    self.account.scores.rank_delta = int(data.replace('.', ''))
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
            self._data_prev = data
            return
        # end in_player_data
        if self.in_prom_level:
            if self._read_next == 'prom_level':
                # [7 из 100]
                match = re.match(r'(\d+)\sиз\s(\d+)', data)
                if match:  # ('7', '100')
                    self.account.scores.industry_level = int(match.group(1))
                self._read_next = 'prom_exp'
                return
            if self._read_next == 'prom_exp':
                # [342 / 343 exp] OR
                # [714 / 1.728 exp]
                # just remove all '.' chars
                data_r = data.replace('.', '')
                match = re.match(r'(\d+)\s/\s(\d+)', data_r)
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
                match = re.match(r'(\d+)\sиз\s(\d+)', data)
                if match:  # ('7', '100')
                    self.account.scores.military_level = int(match.group(1))
                self._read_next = 'mil_exp'
                return
            if self._read_next == 'mil_exp':
                # [342 / 343 exp]
                data_r = data.replace('.', '')
                match = re.match(r'(\d+)\s/\s(\d+)', data_r)
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
                self.account.scores.credits = safe_int(data)
                self.in_credits = False
                self._read_next = ''
            return
        if self.in_fraction:
            if self._read_next == 'fr':
                self.account.scores.fraction = data
                self._read_next = ''
                self.in_fraction = False
        if self.in_wins:
            logger.info('wins: %s' % data)
            self.account.scores.wins = safe_int(data)
            self.in_wins = False
        if self.in_losses:
            logger.info('losses: %s' % data)
            self.account.scores.losses = safe_int(data)
            self.in_losses = False
        if self.in_reflink:
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            logger.info('Account referral link: [{0}]'.format(data))
            self.account.ref_link = data
            match = re.search(r'/\?(\d+)$', data)
            if match:
                self.account.id = safe_int(match.group(1))
            self.in_reflink = False
        if self._num_a_with_galaxy > 0:
            # logger.debug('{0}: galaxy ref [{1}]'.format(self._num_a_with_galaxy, data))
            xc = XNCoords()
            try:
                xc.parse_str(data, raise_on_error=True)
                if self._num_a_with_galaxy == 1:
                    self._cur_flight.src = xc
                    self._cur_flight.src.target_name = self._cur_flight_src_nametype[0]
                    self._cur_flight.src.target_type = self._cur_flight_src_nametype[1]
                elif self._num_a_with_galaxy == 2:
                    self._cur_flight.dst = xc
                    self._cur_flight.dst.target_name = self._cur_flight_dst_nametype[0]
                    self._cur_flight.dst.target_type = self._cur_flight_dst_nametype[1]
                    self._num_a_with_galaxy = 0  # stop here
            except ValueError:
                pass
        if self.in_flight:
            m = re.match(r'^отправленный с планеты (.+)$', data)
            if m:
                src_name = m.group(1)
                self._cur_flight_src_nametype = (src_name, XNCoords.TYPE_PLANET)
            m = re.match(r'^отправленный с луны (.+)$', data)
            if m:
                src_name = m.group(1)
                self._cur_flight_src_nametype = (src_name, XNCoords.TYPE_MOON)
            m = re.match(r'^отправленный с поля обломков (.+)$', data)
            if m:
                src_name = m.group(1)
                self._cur_flight_src_nametype = (src_name, XNCoords.TYPE_DEBRIS_FIELD)
            #  [отправленный  с координат]
            m = re.match(r'^отправленный  с координат$', data)
            if m:
                if self._cur_flight.mission == 'ownharvest':
                    self._cur_flight_src_nametype = ('', XNCoords.TYPE_DEBRIS_FIELD)
            m = re.match(r'^направляется к планете (.+)$', data)
            if m:
                dst_name = m.group(1)
                self._cur_flight_dst_nametype = (dst_name, XNCoords.TYPE_PLANET)
            m = re.match(r'^направляется к луне (.+)$', data)
            if m:
                dst_name = m.group(1)
                self._cur_flight_dst_nametype = (dst_name, XNCoords.TYPE_MOON)
            # if = [направляется к  координаты] = if colonize, can safely skip
            # also may be harvest? can determine by mission type detected before
            m = re.match(r'^направляется к  координаты$', data)
            if m:
                if self._cur_flight.mission == 'ownharvest':
                    self._cur_flight_dst_nametype = ('', XNCoords.TYPE_DEBRIS_FIELD)
            #  направляется к полю обломков Колония
            m = re.match(r'^направляется к полю обломков (.+)$', data)
            if m:
                dst_name = m.group(1)
                self._cur_flight_dst_nametype = (dst_name, XNCoords.TYPE_DEBRIS_FIELD)
            m = re.match(r'^возвращается на планету (.+)$', data)
            if m:
                dst_name = m.group(1)
                self._cur_flight_dst_nametype = (dst_name, XNCoords.TYPE_PLANET)
            # in_flight data: [. Задание: Создать базу]
            m = re.search(r'Задание: Создать базу$', data)
            if m:
                self._cur_flight.mission = 'ownbase'
            # logger.debug('in_flight data: [{0}]'.format(data))
        if self.in_flight_time and self.in_flight_time_arrival:
            # first in was arrival time: <font color="lime">13:59:31</font>
            # now, we try to parse "time left": <div id="bxxfs2" class="z">8:59:9</div>
            hour = 0
            minute = 0
            second = 0
            # 13:59:31  (hr:min:sec)
            match = re.search(r'(\d+):(\d+):(\d+)', data)
            if match:
                hour = safe_int(match.group(1))
                minute = safe_int(match.group(2))
                second = safe_int(match.group(3))
            else:
                # 8:31  (min:sec)
                match = re.search(r'(\d+):(\d+)', data)
                if match:
                    minute = safe_int(match.group(1))
                    second = safe_int(match.group(2))
                else:
                    # server sometimes sends remaining fleet time
                    # without seconds part: <div id="bxxfs4" class="z">38:</div>
                    match = re.search(r'(\d+):', data)
                    if match:
                        minute = safe_int(match.group(1))
                    else:
                        # just a number (seconds)
                        second = safe_int(data)
            if hour + minute + second > 0:
                # dt_now = datetime.datetime.today()
                # dt_arrive = datetime.datetime(dt_now.year, dt_now.month, dt_now.day,
                #                              hour=h, minute=m, second=s)
                # this method is more reliable:
                time_left = datetime.timedelta(seconds=second, minutes=minute, hours=hour)
                dt_arrive = self.server_time + time_left
                self._cur_flight_arrive_dt = dt_arrive
                # logger.debug('Fleet time left: {0}; calculated arrive datetime: {1}'.format(
                #    time_left, dt_arrive))
                return
        if self.in_server_time:
            # <div id="clock" class="pull-right">30-08-2015 12:10:08</div>
            match = re.search(r'(\d+)-(\d+)-(\d+)\s(\d+):(\d+):(\d+)', data)
            if match:
                day = safe_int(match.group(1))
                month = safe_int(match.group(2))
                year = safe_int(match.group(3))
                hour = safe_int(match.group(4))
                minute = safe_int(match.group(5))
                second = safe_int(match.group(6))
                self.server_time = datetime.datetime(year, month, day, hour, minute, second)
                logger.info('Got server time: {0}'.format(self.server_time))
        if tag == 'b':
            # <b id="new_messages">0</b>
            b_id = get_attribute(attrs, 'id')
            if b_id is not None:
                if b_id == 'new_messages':
                    new_messages = safe_int(data)
                    logger.info('new messages: {0}'.format(new_messages))
        return   # from def handle_data()
