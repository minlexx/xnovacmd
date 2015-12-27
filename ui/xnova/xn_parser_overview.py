# -*- coding: utf-8 -*-
import re
import datetime

from .xn_data import XNAccountInfo, XNCoords, XNFlight, XNResourceBundle, XNShipsBundle
from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


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
                elif self._p == 'Межпланетная ракета:':
                    self.ships.mpr = value
                else:
                    # ValueError: Unknown ship type: "Межпланетная ракета:"
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
        # output data
        self.account = XNAccountInfo()
        self.flights = []
        self.server_time = datetime.datetime.today()
        self.new_messages_count = 0
        self.online_players = 0
        self.in_RO = False  # vacation mode
        # internals
        self._in_player_data = False
        self._in_prom_level = False
        self._in_military_level = False
        self._in_credits = False
        self._in_fraction = False
        self._in_wins = False
        self._in_losses = False
        self._in_reflink = False
        self._in_flight = False
        self._in_floten_time = False
        self._in_enemy_message_span = False
        self._data_prev = ''
        self._read_next = ''
        self._num_a_with_tooltip = 0
        self._num_a_with_galaxy = 0
        self._cur_flight = XNFlight()
        self._cur_flight_src_nametype = ('', 0)
        self._cur_flight_dst_nametype = ('', 0)
        self._in_server_time = False
        #
        self.clear()

    def clear(self):
        # output data
        self.account = XNAccountInfo()
        self.flights = []
        self.server_time = datetime.datetime.today()
        self.new_messages_count = 0
        self.online_players = 0
        self.in_RO = False  # vacation mode
        # internals
        self._in_player_data = False
        self._in_prom_level = False
        self._in_military_level = False
        self._in_credits = False
        self._in_fraction = False
        self._in_wins = False
        self._in_losses = False
        self._in_reflink = False
        self._in_flight = False
        self._in_floten_time = False
        self._in_enemy_message_span = False
        self._data_prev = ''
        self._read_next = ''
        self._num_a_with_tooltip = 0
        self._num_a_with_galaxy = 0
        self._cur_flight = XNFlight()
        self._cur_flight_src_nametype = ('', 0)
        self._cur_flight_dst_nametype = ('', 0)
        self._in_server_time = False

    def handle_starttag(self, tag: str, attrs: list):
        super(OverviewParser, self).handle_starttag(tag, attrs)
        if (tag == 'img') and (len(attrs) > 0):
            if ('src', '/images/wins.gif') in attrs:
                self._in_wins = True
            if ('src', '/images/losses.gif') in attrs:
                self._in_losses = True
            return
        if (tag == 'a') and (len(attrs) > 0):
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            if ('href', '?set=refers') in attrs:
                self._in_reflink = True
                return
            if self._in_flight:
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
                self._in_enemy_message_span = True
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
            self._in_flight = True
            self._num_a_with_tooltip = 0
            self._num_a_with_galaxy = 0
            # self._cur_flight = XNFlight()
            self._cur_flight.direction = flight_dir
            self._cur_flight.mission = flight_mission
            return
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
                self._in_server_time = True

    def add_flight(self):
        """
        Called when finally collected all information about the flight
        and data structure is ready to be added to parsed flights list
        :return: None
        """
        # validate this is flight:
        # 1) only having source/destination set
        if (not self._cur_flight.src.is_empty()) and (not self._cur_flight.dst.is_empty()):
            # 2) only actually having ships in it
            if len(self._cur_flight.ships) > 0:
                self.flights.append(self._cur_flight)
                logger.debug('+++ Added flight: {0}'.format(self._cur_flight))
        # Cleanup internal structures
        self._in_flight = False
        self._in_floten_time = False
        self._num_a_with_tooltip = 0
        self._num_a_with_galaxy = 0
        self._cur_flight = XNFlight()
        self._cur_flight_src_nametype = ('', 0)
        self._cur_flight_dst_nametype = ('', 0)

    def handle_endtag(self, tag: str):
        super(OverviewParser, self).handle_endtag(tag)
        if tag == 'span':
            # special case when enemy attack fleet, contains inner span tag
            if self._in_enemy_message_span:
                self._in_enemy_message_span = False
                return
            # flight end trigger moved to 'script' end tag handler, see below...
            # if self._in_flight:
            #    self._cur_flight.arrive_datetime = self._cur_flight_arrive_dt
            #    self.add_flight()
            return
        if (tag == 'div') and self._in_server_time:
            self._in_server_time = False
            return
        if tag == 'html':
            logger.info('Loaded total {0} flights.'.format(len(self.flights)))
        if tag == 'script':
            if self._in_flight and self._in_floten_time:
                self.add_flight()
                return

    def handle_data2(self, data: str, tag: str, attrs: list):
        # detect vacation mode
        if tag == 'font':
            # <font color="red">Включен режим отпуска! Функциональность игры ограничена.</font>
            font_color = get_attribute(attrs, 'color')
            if font_color is not None:
                if font_color == 'red':
                    if data == 'Включен режим отпуска! Функциональность игры ограничена.':
                        self.in_RO = True
                        return
        if data == 'Игрок:':
            self._in_player_data = True
            self._data_prev = data
            return
        if data == 'Промышленный уровень':
            self._in_prom_level = True
            self._read_next = 'prom_level'
            return
        if data == 'Военный уровень':
            self._in_military_level = True
            self._read_next = 'mil_level'
            return
        if data == 'Кредиты':
            self._in_credits = True
            self._read_next = 'credits'
            return
        if data == 'Фракция:':
            self._in_fraction = True
            self._read_next = 'fr'
            return
        ###########################
        if self._in_player_data:
            if self._data_prev == 'Игрок:':
                self.account.login = data
                self._data_prev = ''
                # logger.debug('Player login: {0}'.format(data))
                return
            if self._data_prev == 'Постройки:':
                self.account.scores.buildings = safe_int(data)
                self._data_prev = ''
                # logger.debug('Buildings: {0}'.format(self.account.scores.buildings))
                return
            if self._data_prev == 'Флот:':
                self.account.scores.fleet = safe_int(data)
                self._data_prev = ''
                # logger.debug('Fleet: {0}'.format(self.account.scores.fleet))
                return
            if self._data_prev == 'Оборона:':
                self.account.scores.defense = safe_int(data)
                self._data_prev = ''
                # logger.debug('Defense: {0}'.format(self.account.scores.defense))
                return
            if self._data_prev == 'Наука:':
                self.account.scores.science = safe_int(data)
                self._data_prev = ''
                # logger.debug('Science: {0}'.format(self.account.scores.science))
                return
            if self._data_prev == 'Всего:':
                self.account.scores.total = safe_int(data)
                self._data_prev = ''
                # logger.debug('Total: {0}'.format(self.account.scores.total))
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
                self._in_player_data = False
                logger.info('Account Rank: {0}, delta: {1}'.format(
                    self.account.scores.rank, self.account.scores.rank_delta))
                # logger.info(str(self.account.scores))
                # logger.info(str(self.account))
                return
            # none of above matches
            self._data_prev = data
            return
        # end in_player_data
        if self._in_prom_level:
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
                self._in_prom_level = False
                return
            return
        # end in_prom_level
        if self._in_military_level:
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
                self._in_military_level = False
                return
            return
        if self._in_credits:
            if self._read_next == 'credits':
                self.account.scores.credits = safe_int(data)
                self._in_credits = False
                self._read_next = ''
            return
        if self._in_fraction:
            if self._read_next == 'fr':
                self.account.scores.fraction = data
                self._read_next = ''
                self._in_fraction = False
        if self._in_wins:
            # logger.debug('wins: %s' % data)
            self.account.scores.wins = safe_int(data)
            self._in_wins = False
        if self._in_losses:
            # logger.debug('losses: %s' % data)
            self.account.scores.losses = safe_int(data)
            self._in_losses = False
        if self._in_reflink:
            # <th colspan="2"><a href="?set=refers">http://uni4.xnova.su/?71995</a>
            # logger.debug('Account referral link: [{0}]'.format(data))
            self.account.ref_link = data
            match = re.search(r'/\?(\d+)$', data)
            if match:
                self.account.id = safe_int(match.group(1))
            self._in_reflink = False
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
        if self._in_flight:
            if data == 'Ваш':
                self._cur_flight.is_our_fleet = True
            elif data == 'Чужой':
                self._cur_flight.is_our_fleet = False
            if not self._cur_flight.is_our_fleet:
                # in_flight: [игрока ScumWir]
                if data.startswith('игрока '):
                    self._cur_flight.enemy_name = data[7:]
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
            m = re.match(r'^отправленный  с военной базы (.+)$', data)
            if m:
                src_name = m.group(1)
                self._cur_flight_src_nametype = (src_name, XNCoords.TYPE_WARBASE)
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
            # fix for ownbase missions (displayed by server as missile missions)
            # in_flight data: [. Задание: Создать базу]
            # in_flight data: [Создать базу]
            m = re.search(r'Задание: Создать базу$', data)
            if m or (data == 'Создать базу'):
                self._cur_flight.mission = 'ownbase'
            # in_flight data: [. Задание: Межпланетная атака]
            m = re.search(r'Задание: Межпланетная атака$', data)
            if m:
                self._cur_flight.mission = 'ownmissile'
            # logger.debug('in_flight data: [{0}]'.format(data))
        if self._in_server_time:
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
                    self.new_messages_count = safe_int(data)
                    logger.info('new messages: {0}'.format(self.new_messages_count))
        # find current online players count
        if tag == 'a':
            # <a onclick="" title="Игроков в сети" style="color:green">35</a>
            a_style = get_attribute(attrs, 'style')
            a_title = get_attribute(attrs, 'title')
            if (a_title == 'Игроков в сети') and (a_style == 'color:green'):
                self.online_players = safe_int(data)
                logger.info('Online players = {0}'.format(self.online_players))
        if tag == 'script':
            # parse fleet remaining time more precisely
            # <script>FlotenTime('bxxfs2', 89118);</script>
            if data.startswith('FlotenTime('):
                self._in_floten_time = True
                data_parts = data.split(' ', 2)
                time_part = data_parts[1]  # "89118);"
                time_part = time_part[:-2]  # "89118"
                fleet_time_left_secs = safe_int(time_part)
                td_time_left = datetime.timedelta(seconds=fleet_time_left_secs)
                dt_arrive = self.server_time + td_time_left
                # store
                self._cur_flight.seconds_left = fleet_time_left_secs
                self._cur_flight.arrive_datetime = dt_arrive
                # logger.debug('    parsed FlotenTime: secs left: {0}; '
                #             ' arrive datetime: {1}'.format(fleet_time_left_secs, dt_arrive))
        return   # from def handle_data()

# own missile parser
# <span class="flight ownattack">Ваш <a href='javascript:;' class="tooltip"
#   data-tooltip-content='<table width=200><tr><td width=75% align=left>
#   <font color=white>Межпланетная ракета:<font></td><td width=25% align=right>
#   <font color=white>2<font></td></tr></table>'
# class="ownattack">флот</a> отправленный с планеты Tama
# <a href="?set=galaxy&amp;r=3&amp;galaxy=1&amp;system=34" ownattack >[1:34:11]</a>
# направляется к планете порта <a href="?set=galaxy&amp;r=3&amp;galaxy=1&amp;system=19"
# ownattack >[1:19:3]</a>. Задание: Межпланетная атака</span>

# in_flight: [Ваш]
# in_flight: [флот]
# ...
# in_flight: [Чужой]
# in_flight: [флот]
# in_flight: [игрока ScumWir]
# in_flight: [отправленный с луны Луна]
# in_flight: [[1:233:9]]
# [направляется к планете Tama]
# [[1:34:11]]
# [. Задание: Атаковать]
# [FlotenTime('bxxofs13', 4129);]
# +++ Added flight: attack Луна  (moon) [1:233:9] -> Tama [1:34:11] (LI: 1650)  @ 2015-12-27 12:57:32, 4129 secs left
