# -*- coding: utf-8 -*-
import re
import datetime

from .xn_parser import XNParserBase, safe_int, get_attribute,\
    get_tag_classes, parse_build_total_time_sec
from .xn_data import XNPlanetBuildingItem
from .xn_techtree import XNTechTree_instance
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


class ResearchAvailParser(XNParserBase):
    def __init__(self):
        super(ResearchAvailParser, self).__init__()
        # public
        self.researches_avail = []
        self.server_time = datetime.datetime.today()
        # private
        self._cur_item = XNPlanetBuildingItem()
        self._in_div_viewport_buildings = False
        self._in_div_title = False
        self._in_div_actions = False
        self._in_div_overContent = False
        self._in_div_brp = False
        self._got_level = False
        self._img_resource = ''  # met, cry, deit, energy
        self.clear()

    def clear(self):
        self.researches_avail = []
        self.server_time = datetime.datetime.today()
        # clear internals
        self._in_div_viewport_buildings = False
        self._in_div_title = False
        self._in_div_actions = False
        self._in_div_overContent = False
        self._in_div_brp = False
        # current parsing building item
        self._cur_item = XNPlanetBuildingItem()
        self._got_level = False
        self._img_resource = ''

    def add_price(self, data: str):
        if self._img_resource == 'met':
            self._cur_item.cost_met = safe_int(data)
            logger.debug('    cost met: {0}'.format(self._cur_item.cost_met))
            return
        if self._img_resource == 'cry':
            self._cur_item.cost_cry = safe_int(data)
            logger.debug('    cost cry: {0}'.format(self._cur_item.cost_cry))
            return
        if self._img_resource == 'deit':
            self._cur_item.cost_deit = safe_int(data)
            logger.debug('    cost deit: {0}'.format(self._cur_item.cost_deit))
            return
        if self._img_resource == 'energy':
            self._cur_item.cost_energy = safe_int(data)
            logger.debug('    cost energy: {0}'.format(self._cur_item.cost_energy))
            return
        logger.error('Unknown current resource image: [{0}]'.format(self._img_resource))

    def handle_starttag(self, tag: str, attrs: list):
        super(ResearchAvailParser, self).handle_starttag(tag, attrs)
        if tag == 'div':
            div_classes = get_tag_classes(attrs)
            div_id = get_attribute(attrs, 'id')
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
            if 'overContent' in div_classes:
                self._in_div_overContent = True
                return
            if div_id == 'brp':
                self._in_div_brp = True
                return
            return
        if tag == 'img':
            if self._in_div_overContent:
                img_src = get_attribute(attrs, 'src')
                # logger.debug('img in div overContent [{0}]'.format(img_src))
                if img_src == 'skins/default/images/s_metall.png':
                    self._img_resource = 'met'
                if img_src == 'skins/default/images/s_kristall.png':
                    self._img_resource = 'cry'
                if img_src == 'skins/default/images/s_deuterium.png':
                    self._img_resource = 'deit'
                if img_src == 'skins/default/images/s_energie.png':
                    self._img_resource = 'energy'
            return

    def handle_endtag(self, tag: str):
        super(ResearchAvailParser, self).handle_endtag(tag)
        if tag == 'div':
            if self._in_div_viewport_buildings and self._in_div_title and \
                    self._in_div_actions and (not self._in_div_brp):
                self._in_div_viewport_buildings = False
                self._in_div_title = False
                self._in_div_actions = False
                self._in_div_overContent = False
                # store build item to list
                self.researches_avail.append(self._cur_item)
                # log
                logger.debug(' -- Planet research avail: (gid={0}) {1} lv {2} build time {3} secs'.format(
                    self._cur_item.gid, self._cur_item.name,
                    self._cur_item.level, self._cur_item.seconds_total
                ))
                # clear current item from temp data
                self._cur_item = XNPlanetBuildingItem()
                self._img_resource = ''
                self._got_level = False
                return

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(ResearchAvailParser, self).handle_data2(data, tag, attrs)
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
                logger.debug('    title: [{0}] gid=[{1}]'.format(data, gid))
        if tag == 'span':
            span_classes = get_tag_classes(attrs)
            if self._in_div_overContent:
                if span_classes is None:
                    return
                # not enough resources to build
                if ('resNo' in span_classes) and ('tooltip' in span_classes):
                    # logger.debug('    span resNo tooltip in div overContent: {0}'.format(data))
                    self.add_price(data)
                # have enough resources to build
                if 'resYes' in span_classes:
                    if data != 'Построить':
                        # logger.debug('    span resYes in div overContent: {0}'.format(data))
                        self.add_price(data)
        if tag == 'br':
            if self._in_div_actions:
                # <br>" Время: 1 д. 14 ч. 44 мин. 15 с. "
                if data.startswith('Время:'):
                    build_time = data[7:]
                    bt_secs = parse_build_total_time_sec(build_time)
                    # store info
                    self._cur_item.seconds_total = bt_secs
                    logger.debug('    build time: [{0}] ({1} secs)'.format(build_time, bt_secs))
        if tag == 'font':
            if self._in_div_actions:
                if not self._got_level:
                    self._got_level = True
                    self._cur_item.level = safe_int(data)
                    logger.debug('    level: [{0}]'.format(self._cur_item.level))
        if tag == 'script':
            if self._in_div_brp:
                logger.debug('    <script> in div actions, is in progress')
                self._in_div_brp = False
                lines = data.split('\n', maxsplit=6)
                if len(lines) < 6:
                    return
                # 6th line is "ss = 52632;" // seconds left for building to complete
                line = lines[5].strip()
                m = re.match(r'ss = (\d+);', line)
                if m is not None:
                    secs_left = safe_int(m.group(1))
                    dt_end = self.server_time + datetime.timedelta(seconds=secs_left)
                    self._cur_item.seconds_left = secs_left
                    self._cur_item.dt_end = dt_end
                    logger.debug('    in progress, seconds left = {0}, dt_end = {1}'.format(
                        secs_left, str(self._cur_item.dt_end)))
