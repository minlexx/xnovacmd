# -*- coding: utf-8 -*-
import re

from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class PlanetBuildingsParser(XNParserBase):
    def __init__(self):
        super(PlanetBuildingsParser, self).__init__()
        # output vars
        self.builds_in_progress = []
        # state vars
        self.in_curbuild_table = False

    def clear(self):
        self.builds_in_progress = []

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
                logger.debug('[{0}]'.format(data))
                position = 0
                building = ''
                level = 0
                # first, before ':' token is position
                # next comes sapce, followed by all other chars
                m = re.search(r'(\d)+:\s+(.+)', data)
                if m is not None:
                    position = int(m.group(1))
                    building = m.group(2)
                    bs = building.split(' ')  # bs = ['Рудник', 'металла', '26']
                    # the last item in 'bs' is building level
                    level = safe_int(bs.pop())
                    building = ' '.join(bs)  # join building name back, without level
                    binfo = dict(position=position, name=building, level=level)
                    self.builds_in_progress.append(binfo)
            if tag == 'div':
                # <div class="positive">21.10 21:41:33</div>
                if tag_classes is not None:
                    if 'positive' in tag_classes:
                        logger.debug('end time [{0}]'.format(data))
        return  # def handle_data2()

    def handle_endtag(self, tag: str):
        super(PlanetBuildingsParser, self).handle_endtag(tag)
        if self.in_curbuild_table:
            if tag == 'table':
                self.in_curbuild_table = False
        return
