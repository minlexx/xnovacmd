# -*- coding: utf-8 -*-
import re
import datetime

from .xn_parser import XNParserBase, safe_int, get_attribute,\
    get_tag_classes, parse_time_left_str, parse_build_total_time_sec
from .xn_data import XNPlanetBuildingItem
from .xn_techtree import XNTechTree_instance
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


class PlanetBuildingsAvailParser(XNParserBase):
    def __init__(self):
        super(PlanetBuildingsAvailParser, self).__init__()
        # public
        self.builds_avail = []
        # private
        self._cur_item = XNPlanetBuildingItem()
        self.clear()

    def clear(self):
        self.builds_avail = []
        # clear internals
        self._in_div_viewport_buildings = False
        self._in_div_title = False
        self._in_div_actions = False
        # current parsing building item
        self._cur_item = XNPlanetBuildingItem()

    def handle_starttag(self, tag: str, attrs: list):
        super(PlanetBuildingsAvailParser, self).handle_starttag(tag, attrs)
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
        super(PlanetBuildingsAvailParser, self).handle_endtag(tag)
        if tag == 'div':
            if self._in_div_viewport_buildings and self._in_div_title and self._in_div_actions:
                self._in_div_viewport_buildings = False
                self._in_div_title = False
                self._in_div_actions = False
                # store build item to list
                self.builds_avail.append(self._cur_item)
                # log
                logger.debug(' -- Planet building avail: (gid={1}) {0} lv {2}, upgrade time {3} secs'.format(
                    self._cur_item.name, self._cur_item.gid,
                    self._cur_item.level, self._cur_item.seconds_total
                ))
                # logger.debug('-------------------------')
                # clear current item from temp data
                self._cur_item = XNPlanetBuildingItem()
                return

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetBuildingsAvailParser, self).handle_data2(data, tag, attrs)
        # if self._in_div_viewport_buildings:
        #    logger.debug('  handle_data2(tag={0}, data={1}, attrs={2})'.format(tag, data, attrs))
        if tag == 'a':
            if self._in_div_viewport_buildings and self._in_div_title and (not self._in_div_actions):
                # <a href=?set=infos&gid=1>Рудник металла</a>
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
            if self._in_div_actions:
                if span_classes is None:
                    return
                if 'positive' in span_classes:
                    # <span class="positive">27</span>
                    level = safe_int(data)
                    # store info about level, only if it is not stored yet
                    if self._cur_item.level == 0:
                        self._cur_item.level = level
                        # logger.debug('   level = [{0}]'.format(level))
        if tag == 'br':
            if self._in_div_actions:
                # <br>" Время: 1 д. 14 ч. 44 мин. 15 с. "
                if data.startswith('Время:'):
                    build_time = data[7:]
                    bt_secs = parse_build_total_time_sec(build_time)
                    # store info
                    self._cur_item.seconds_total = bt_secs
                    # logger.debug('   build time: [{0}] ({1} secs)'.format(build_time, bt_secs))


class PlanetBuildingsProgressParser(XNParserBase):
    def __init__(self):
        super(PlanetBuildingsProgressParser, self).__init__()
        # output vars
        self.builds_in_progress = []
        # state vars
        self.in_curbuild_table = False
        self._position = 0
        self._building = ''
        self._level = 0

    def clear(self):
        self.builds_in_progress = []

    def add_build_info(self,
                       position: int,
                       building: str, level: int,
                       dt_end: datetime.datetime = None,
                       remove_link: str = None):
        bitem = XNPlanetBuildingItem()
        bitem.name = building
        bitem.gid = XNTechTree_instance().find_gid_by_name(building)
        bitem.level = level
        bitem.position = position
        bitem.remove_from_queue_link = remove_link
        bitem.set_end_time(dt_end)  # also calculates seconds_left, if possible
        self.builds_in_progress.append(bitem)
        # logging
        logger.info(' ...add build item: {0}'.format(str(bitem)))

    def handle_starttag(self, tag: str, attrs: list):
        super(PlanetBuildingsProgressParser, self).handle_starttag(tag, attrs)
        tag_id = get_attribute(attrs, 'id')
        # <table class="table" id="building">
        if tag == 'table':
            if tag_id == 'building':
                self.in_curbuild_table = True

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetBuildingsProgressParser, self).handle_data2(data, tag, attrs)
        # tag_classes = get_tag_classes(attrs)
        # <td class="c" width="50%"> 1: Рудник металла 26 </td>
        if self.in_curbuild_table:
            if tag == 'td':
                # logger.debug('[{0}]'.format(data))
                self._position = 0
                self._building = ''
                self._level = 0
                # first, before ':' token is position
                # next comes sapce, followed by all other chars
                m = re.search(r'(\d)+:\s+(.+)', data)
                if m is not None:
                    self._position = int(m.group(1))
                    building = m.group(2)
                    bs = building.split(' ')  # bs = ['Рудник', 'металла', '26']
                    # the last item in 'bs' is building level
                    self._level = safe_int(bs.pop())
                    self._building = ' '.join(bs)  # join building name back, without level
            if tag == 'script':
                script_type = get_attribute(attrs, 'type')
                if (script_type is not None) and (script_type == 'text/javascript'):
                    # <script type="text/javascript">BuildTimeout(429966, 1, 69255, 0);</script>
                    # first argument to BuildTimeout is (possibly) seconds left
                    # third is planet_id
                    if data.startswith('BuildTimeout'):
                        m = re.match(r'BuildTimeout\((\d+),', data)
                        if m is not None:
                            secs_left = safe_int(m.group(1))
                            td = datetime.timedelta(seconds=secs_left)
                            dt_now = datetime.datetime.today()
                            dt_end = dt_now + td
                            # logger.debug('dt_now={0}, td={1}, dt_end={2}'.format(dt_now, td, dt_end))
                            self.add_build_info(self._position, self._building, self._level, dt_end)
            if tag == 'a':
                # remove from queue (Architector only)
                # <a href="?set=buildings&listid=2&cmd=remove&planet=54450">Удалить</a>
                a_href = get_attribute(attrs, 'href')
                if a_href is not None:
                    remove_link = a_href
                    self.add_build_info(self._position, self._building, self._level, None, remove_link)
        return  # def handle_data2()

    def handle_endtag(self, tag: str):
        super(PlanetBuildingsProgressParser, self).handle_endtag(tag)
        if self.in_curbuild_table:
            if tag == 'table':
                self.in_curbuild_table = False
        return
