# -*- coding: utf-8 -*-
import re

from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


class TechtreeParser(XNParserBase):
    def __init__(self):
        super(TechtreeParser, self).__init__()
        self.techtree = []
        # internal
        self._in_cat = ''

    def add_item(self, gid: int, name: str):
        tt_tuple = (gid, name, self._in_cat)
        self.techtree.append(tt_tuple)
        logger.debug(' loaded {0}'.format(str(tt_tuple)))

    def handle_data2(self, data: str, tag: str, attrs: list):
        # trap all anchors of the following format:
        # <a href="?set=infos&gid=NNN
        # as simple as this.
        if tag == 'a':
            href = get_attribute(attrs, 'href')
            if href is None:
                return
            if href.startswith('?set=infos&gid='):
                # our client
                m = re.match(r'\?set=infos&gid=(\d+)', href)
                if m is not None:
                    gid = safe_int(m.group(1))
                    self.add_item(gid, data)
        # track current category
        # <div id="tabs-0" - buildings
        # <div id="tabs-15" - buildings special
        # <div id="tabs-20" - research
        # <div id="tabs-39" - fleet
        # <div id="tabs-59" - defense
        if tag == 'div':
            div_id = get_attribute(attrs, 'id')
            if div_id is None:
                return
            if div_id == 'tabs-0':
                self._in_cat = 'building'
            if div_id == 'tabs-20':
                self._in_cat = 'research'
            if div_id == 'tabs-39':
                self._in_cat = 'fleet'
            if div_id == 'tabs-59':
                self._in_cat = 'defense'
        pass
