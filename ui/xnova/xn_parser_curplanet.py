# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords
from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class CurPlanetParser(XNParserBase):
    def __init__(self):
        super(CurPlanetParser, self).__init__()
        #
        self.in_planet_list = False
        self.in_planet_block = False
        self.in_hidden_sm = False
        self.data_count = 0
        # output data
        self.cur_planet_id = 0
        self.cur_planet_name = ''
        self.cur_planet_coords = XNCoords(0, 0, 0)

    def handle_starttag(self, tag: str, attrs: list):
        super(CurPlanetParser, self).handle_starttag(tag, attrs)
        if attrs is None:
            return
        if not self.in_planet_list:
            if tag == 'div':
                div_classes = get_tag_classes(attrs)
                if div_classes is None:
                    return  # we parse only elements with classes!
                if ('planet-sidebar' in div_classes) and ('planetList' in div_classes):
                    self.in_planet_list = True
            return
        if self.in_planet_list:
            if tag == 'div':
                div_classes = get_tag_classes(attrs)
                if div_classes is None:
                    return
                if ('planet' in div_classes) and ('type_1' in div_classes) and ('current' in div_classes):
                    self.in_planet_block = True
            if self.in_planet_block:
                if tag == 'div':
                    div_classes = get_tag_classes(attrs)
                    if div_classes is None:
                        return
                    if 'hidden-sm' in div_classes:
                        self.in_hidden_sm = True
                        self.data_count = 0  # prepare to receive data!
                    return
                if tag == 'a':
                    # find "<a href="javascript:" onclick="changePlanet(54450)" title="Arnon">"
                    a_onclick = get_attribute(attrs, 'onclick')
                    if a_onclick is not None:
                        match = re.search(r'changePlanet\((\d+)\)', a_onclick)
                        if match:
                            self.cur_planet_id = safe_int(match.group(1))
                            # logger.debug('Found cur planet id: {0}'.format(self.cur_planet_id))
            return

    def handle_data2(self, data: str, tag: str, attrs: list):
        if self.in_planet_list:
            if self.in_planet_block:
                if self.in_hidden_sm:
                    # logger.debug('data {0}: {1}'.format(self.data_count, data))
                    if self.data_count == 0:
                        # this is planet name
                        self.cur_planet_name = data
                        # logger.debug('Found cur planet name: {0}'.format(self.cur_planet_name))
                    elif self.data_count == 1:
                        # this is planet coords
                        self.cur_planet_coords.parse_str(data)
                        # logger.debug('Found cur planet coords: {0}'.format(self.cur_planet_coords))
                    self.data_count += 1
                    if self.data_count >= 2:
                        # exit processing, we found all we need
                        self.in_hidden_sm = False
                        self.in_planet_block = False
                        self.in_planet_list = False
        return  # def handle_data()

    def handle_endtag(self, tag: str):
        super(CurPlanetParser, self).handle_endtag(tag)
        if tag == 'html':
            logger.info('Found cur planet: #{0} {1} {2}'.format(
                self.cur_planet_id, self.cur_planet_name, str(self.cur_planet_coords)))
