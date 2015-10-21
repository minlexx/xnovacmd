# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords
from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


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

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetBuildingsParser, self).handle_data2(data, tag, attrs)
        #if tag == 'table'
        return  # def handle_data2()

    def handle_endtag(self, tag: str):
        super(PlanetBuildingsParser, self).handle_endtag(tag)
        return
