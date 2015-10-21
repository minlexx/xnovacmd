# -*- coding: utf-8 -*-
import re
# import datetime

from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes, parse_time_left_str
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class PlanetBuildingsParser(XNParserBase):
    def __init__(self):
        super(PlanetBuildingsParser, self).__init__()
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
                       hours: int, minutes: int, seconds: int,
                       remove_link: str):
        binfo = dict(
            position=position,  # sequence number in queue, starting from 1
            name=building, level=level,
            hours=hours, minutes=minutes, seconds=seconds,
            remove_link=remove_link
        )
        self.builds_in_progress.append(binfo)
        # logging
        time_str = ''
        if hours + minutes + seconds > 0:
            time_str = 'end {0:02}:{1:02}:{2:02}'.format(hours, minutes, seconds)
        rl_str = ''
        if remove_link != '':
            rl_str = ' in queue, remove_link=[{0}]'.format(remove_link)
        logger.info(' ... {0}: [{1}] lv {2}, {3}{4}'.format(
            position, building, level, time_str, rl_str
        ))

    def handle_starttag(self, tag: str, attrs: list):
        super(PlanetBuildingsParser, self).handle_starttag(tag, attrs)
        tag_id = get_attribute(attrs, 'id')
        # <table class="table" id="building">
        if tag == 'table':
            if tag_id == 'building':
                self.in_curbuild_table = True

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetBuildingsParser, self).handle_data2(data, tag, attrs)
        tag_classes = get_tag_classes(attrs)
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
            if tag == 'div':
                # <div class="positive">21.10 21:41:33</div>
                if tag_classes is not None:
                    if 'positive' in tag_classes:
                        hour, minute, second = parse_time_left_str(data)
                        # td = datetime.timedelta(seconds=second, minutes=minute, hours=hour)
                        # end_dt = datetime.datetime.now() + td
                        # logger.debug('end time [{0}:{1}:{2}]'.format(hour, minute, second))
                        self.add_build_info(self._position, self._building, self._level, hour, minute, second, '')
            if tag == 'a':
                # <a href="?set=buildings&listid=2&cmd=remove&planet=54450">Удалить</a>
                a_href = get_attribute(attrs, 'href')
                if a_href is not None:
                    remove_link = a_href
                    self.add_build_info(self._position, self._building, self._level, 0, 0, 0, remove_link)
        return  # def handle_data2()

    def handle_endtag(self, tag: str):
        super(PlanetBuildingsParser, self).handle_endtag(tag)
        if self.in_curbuild_table:
            if tag == 'table':
                self.in_curbuild_table = False
        return
