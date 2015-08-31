# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords
from .xn_parser import XNParserBase, safe_int
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class ImperiumParser(XNParserBase):
    def __init__(self):
        super(ImperiumParser, self).__init__()

    def handle_starttag(self, tag: str, attrs: list):
        super(ImperiumParser, self).handle_starttag(tag, attrs)

    def handle_data2(self, data: str, tag: str, attrs: tuple):
        # logger.debug('data in tag [{0}]: [{1}]'.format(tag, data))
        return  # def handle_data()

    def handle_endtag(self, tag: str):
        super(ImperiumParser, self).handle_endtag(tag)
