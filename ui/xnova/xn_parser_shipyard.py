# -*- coding: utf-8 -*-
import re
import datetime

from .xn_parser import XNParserBase, safe_int, get_attribute,\
    get_tag_classes, parse_time_left_str, parse_build_total_time_sec
from .xn_data import XNPlanetBuildingItem
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class ShipyardBuildingsAvailParser(XNParserBase):
    """
    TODO: incomplete and unused
    """
    def __init__(self):
        super(ShipyardBuildingsAvailParser, self).__init__()
        # public
        self.builds_avail = []
        # private
        self._cur_item = XNPlanetBuildingItem()
        self.clear()

    def clear(self):
        pass


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
        self.shipyard_items = []
        self.clear()

    def clear(self):
        self.shipyard_items = []
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
                        logger.debug('  got time_passed = {0}'.format(time_passed))
                if line.startswith('p = '):
                    m = re.match(r'p = (\d+);', line)
                    if m is not None:
                        position = safe_int(m.group(1)) + 1
                        logger.debug('  got position = {0}'.format(position))
                if line.startswith('c = new Array('):
                    btimes = parse_js_array_decl(line)
                    logger.debug('  got btimes = {0}'.format(str(btimes)))
                if line.startswith('b = new Array('):
                    bnames = parse_js_array_decl(line)
                    logger.debug('  got bnames = {0}'.format(str(bnames)))
                if line.startswith('a = new Array('):
                    bqs = parse_js_array_decl(line)
                    logger.debug('  got bqs = {0}'.format(str(bqs)))
            # get only first item from this queue
            if len(bnames) > 0:
                for i in range(len(bnames)):
                    self._cur_item.is_shipyard_item = True
                    self._cur_item.name = bnames[i]
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
                    self.shipyard_items.append(self._cur_item)
                    print(str(self._cur_item))
