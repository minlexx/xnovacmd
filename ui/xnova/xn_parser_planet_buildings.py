# -*- coding: utf-8 -*-
import re
import datetime

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
                       dt_end: datetime.datetime = None,
                       remove_link: str = None):
        binfo = dict(
            position=position,  # sequence number in queue, starting from 1
            name=building, level=level,
            dt_end=dt_end,
            remove_link=remove_link
        )
        self.builds_in_progress.append(binfo)
        # logging
        time_str = ''
        if dt_end is not None:
            time_str = 'end {0}'.format(str(dt_end))
        rl_str = ''
        if remove_link is not None:
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
        super(PlanetBuildingsParser, self).handle_endtag(tag)
        if self.in_curbuild_table:
            if tag == 'table':
                self.in_curbuild_table = False
        return
