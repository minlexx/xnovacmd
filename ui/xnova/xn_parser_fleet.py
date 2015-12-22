# -*- coding: utf-8 -*-
import re
from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


__doc__ = '''
For now, only get current/maximum number of fleets,
current/maximum number of expeditions
from ?set=fleet page
'''


class FleetsMaxParser(XNParserBase):
    def __init__(self):
        super(FleetsMaxParser, self).__init__()
        # public
        self.fleets_max = 0
        self.fleets_cur = 0
        self.expeditions_max = 0
        self.expeditions_cur = 0
        # internals
        self.clear()

    def clear(self):
        self.fleets_max = 0
        self.fleets_cur = 0
        self.expeditions_max = 0
        self.expeditions_cur = 0
        # clear internals

    def handle_starttag(self, tag: str, attrs: list):
        super(FleetsMaxParser, self).handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str):
        super(FleetsMaxParser, self).handle_endtag(tag)

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(FleetsMaxParser, self).handle_data2(data, tag, attrs)
        if tag == 'td':
            td_align = get_attribute(attrs, 'align')
            if td_align is None:
                return
            if td_align == 'left':
                m = re.match(r'Флоты (\d+) из (\d+)', data)
                if m is not None:
                    self.fleets_cur = safe_int(m.group(1))
                    self.fleets_max = safe_int(m.group(2))
                    logger.debug('Got fleets count: {0}/{1}'.format(
                            self.fleets_cur, self.fleets_max))
                    return
            if td_align == 'right':
                m = re.match(r'(\d+)/(\d+) Экспедиции', data)
                if m is not None:
                    self.expeditions_cur = safe_int(m.group(1))
                    self.expeditions_max = safe_int(m.group(2))
                    logger.debug('Got expeditions count: {0}/{1}'.format(
                            self.expeditions_cur, self.expeditions_max))
                    return

# <td align="left">
# Флоты 9 из 14						</td>
# <td align="right">
# 0/2 Экспедиции						</td>
