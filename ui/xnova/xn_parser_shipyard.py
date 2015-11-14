# -*- coding: utf-8 -*-
import re
import datetime

from .xn_parser import XNParserBase, safe_int, get_attribute,\
    get_tag_classes, parse_time_left_str, parse_build_total_time_sec
from .xn_data import XNPlanetBuildingItem
from .xn_techtree import XNTechTree_instance
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class ShipyardShipsAvailParser(XNParserBase):
    def __init__(self):
        super(ShipyardShipsAvailParser, self).__init__()
        # public
        self.ships_avail = []
        # private
        self._cur_item = XNPlanetBuildingItem()
        self._in_div_viewport_buildings = False
        self._in_div_title = False
        self._in_div_actions = False
        self.clear()

    def clear(self):
        self.ships_avail = []
        # clear internals
        self._in_div_viewport_buildings = False
        self._in_div_title = False
        self._in_div_actions = False
        # current parsing building item
        self._cur_item = XNPlanetBuildingItem()

    def handle_starttag(self, tag: str, attrs: list):
        super(ShipyardShipsAvailParser, self).handle_starttag(tag, attrs)
        if tag == 'div':
            div_classes = get_tag_classes(attrs)
            if div_classes is None:
                return
            if ('viewport' in div_classes) and ('buildings' in div_classes):
                self._in_div_viewport_buildings = True
                return
            if 'title' in div_classes:
                self._in_div_title = True
                return
            if 'actions' in div_classes:
                self._in_div_actions = True
                return

    def handle_endtag(self, tag: str):
        super(ShipyardShipsAvailParser, self).handle_endtag(tag)
        if tag == 'div':
            if self._in_div_viewport_buildings and self._in_div_title and self._in_div_actions:
                self._in_div_viewport_buildings = False
                self._in_div_title = False
                self._in_div_actions = False
                # store build item to list
                self.ships_avail.append(self._cur_item)
                # log
                logger.debug(' -- Planet ship avail: (gid={0}) {1} x {2} build time {3} secs'.format(
                    self._cur_item.gid, self._cur_item.name,
                    self._cur_item.quantity, self._cur_item.seconds_total
                ))
                # clear current item from temp data
                self._cur_item = XNPlanetBuildingItem()
                return

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(ShipyardShipsAvailParser, self).handle_data2(data, tag, attrs)
        # if self._in_div_viewport_buildings:
        #    logger.debug('  handle_data2(tag={0}, data={1}, attrs={2})'.format(tag, data, attrs))
        if tag == 'a':
            if self._in_div_viewport_buildings and self._in_div_title and (not self._in_div_actions):
                # <a href=?set=infos&gid=202>Малый транспорт</a>
                a_href = get_attribute(attrs, 'href')
                if a_href is None:
                    return
                m = re.match(r'\?set=infos&gid=(\d+)', a_href)
                if m is None:
                    return
                gid = safe_int(m.group(1))
                # store info
                self._cur_item.name = data
                self._cur_item.gid = gid
                # logger.debug('   <a> in title: [{0}] gid=[{1}]'.format(data, gid))
        if tag == 'span':
            span_classes = get_tag_classes(attrs)
            if self._in_div_viewport_buildings and self._in_div_title and (not self._in_div_actions):
                if span_classes is None:
                    return
                if ('positive' in span_classes) or ('negative' in span_classes):
                    # (<span class="positive">302</span>)
                    # (<span class="negative">0</span>)
                    quantity = safe_int(data)
                    self._cur_item.quantity = quantity
                    # logger.debug('   quantity = [{0}]'.format(quantity))
        if tag == 'div':
            if self._in_div_actions:
                # <div class="actions">
                #   	Время: 3 мин. 27 с.
                if data.startswith('Время:'):
                    build_time = data[7:]
                    bt_secs = parse_build_total_time_sec(build_time)
                    # store info
                    self._cur_item.seconds_total = bt_secs
                    # logger.debug('   build time: [{0}] ({1} secs)'.format(build_time, bt_secs))


# example of inputs:
#    c = new Array(62307,207,'');
#    b = new Array('Звезда смерти','Колонизатор','');
def parse_js_array_decl(s: str) -> list:
    m = re.search(r'^(a|b|c) = new Array\(', s)
    if m is None:
        return None
    if not s.endswith(');'):
        return None
    s = s[14:-2]
    ret = []
    for ss in s.split(','):
        if ss == "''":  # skip empty strings ('')
            continue
        if ss.startswith("'") and ss.endswith("'"):  # quoted string
            sss = ss[1:-1]  # trim quotes
            ret.append(sss)
        else:  # int?
            i = safe_int(ss)
            ret.append(i)
    return ret


class ShipyardBuildsInProgressParser(XNParserBase):
    def __init__(self):
        super(ShipyardBuildsInProgressParser, self).__init__()
        self.server_time = datetime.datetime.now()
        self.shipyard_progress_items = []
        # internals
        self._cur_item = XNPlanetBuildingItem()
        self._in_form = False
        self._next_script = False
        self.clear()

    def clear(self):
        self.shipyard_progress_items = []
        self._cur_item = XNPlanetBuildingItem()
        self._in_form = False
        self._next_script = False

    def handle_starttag(self, tag: str, attrs: list):
        super(ShipyardBuildsInProgressParser, self).handle_starttag(tag, attrs)
        if tag == 'form':
            f_name = get_attribute(attrs, 'name')
            if f_name is None:
                return
            if f_name == 'Atr':
                self._in_form = True

    def handle_endtag(self, tag: str):
        super(ShipyardBuildsInProgressParser, self).handle_endtag(tag)
        if tag == 'form' and self._in_form:
            self._in_form = False
            self._next_script = True

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(ShipyardBuildsInProgressParser, self).handle_data2(data, tag, attrs)
        if tag == 'script' and self._next_script:
            self._next_script = False
            # vars
            position = -1     # [p = 0;] // position order in build queue
            time_passed = -1  # [g = 4;] // time passed since build start
            btimes = []  # [c = new Array(83,6,186,969,'');] // build times of individual items
            bnames = []  # [b = new Array('Корсар','Шпионский зонд','Крейсер','Передвижная база','');]
            bqs = []     # [a = new Array(12,30,16,1,'');]  // build quantites
            #
            lines = data.split('\n', maxsplit=10)
            for line in lines:
                line = line.strip()
                # logger.debug('[{0}]'.format(line))
                if line.startswith('g = '):
                    m = re.match(r'g = (\d+);', line)
                    if m is not None:
                        time_passed = safe_int(m.group(1))
                        # logger.debug('  got time_passed = {0}'.format(time_passed))
                if line.startswith('p = '):
                    m = re.match(r'p = (\d+);', line)
                    if m is not None:
                        position = safe_int(m.group(1)) + 1
                        # logger.debug('  got position = {0}'.format(position))
                if line.startswith('c = new Array('):
                    btimes = parse_js_array_decl(line)
                    # logger.debug('  got btimes = {0}'.format(str(btimes)))
                if line.startswith('b = new Array('):
                    bnames = parse_js_array_decl(line)
                    # logger.debug('  got bnames = {0}'.format(str(bnames)))
                if line.startswith('a = new Array('):
                    bqs = parse_js_array_decl(line)
                    # logger.debug('  got bqs = {0}'.format(str(bqs)))
            # get only first item from this queue
            if len(bnames) > 0:
                for i in range(len(bnames)):
                    self._cur_item.is_shipyard_item = True
                    self._cur_item.name = bnames[i]
                    self._cur_item.gid = XNTechTree_instance().find_gid_by_name(self._cur_item.name)
                    self._cur_item.quantity = bqs[i]  # level as quantity
                    self._cur_item.position = position + i
                    self._cur_item.seconds_total = bqs[i] * btimes[i]
                    self._cur_item.seconds_for_item = btimes[i]
                    if i == 0:
                        self._cur_item.seconds_left = self._cur_item.seconds_total - time_passed
                    else:
                        self._cur_item.seconds_left = self._cur_item.seconds_total
                    # calc end time (it should be set)
                    self._cur_item.dt_end = self.server_time + datetime.timedelta(
                        days=0, seconds=self._cur_item.seconds_left)
                    self.shipyard_progress_items.append(self._cur_item)
                    logger.info(' ...add ship in progress {0}'.format(str(self._cur_item)))
