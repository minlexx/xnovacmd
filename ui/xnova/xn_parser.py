# -*- coding: utf-8 -*-
import html.parser

from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# converts string to int, silently ignoring errors
def safe_int(data: str):
    ret = 0
    try:
        ret = int(data.replace('.', ''))
    except ValueError:
        ret = 0
    return ret


# extends html.parser.HTMLParser class
# by remembering tags path
class XNParserBase(html.parser.HTMLParser):
    def __init__(self):
        super(XNParserBase, self).__init__(strict=False, convert_charrefs=True)
        self._last_tag = ''
        self._last_attrs = list()

    def handle_starttag(self, tag: str, attrs: list):
        super(XNParserBase, self).handle_starttag(tag, attrs)
        self._last_tag = tag
        self._last_attrs = attrs

    def handle_endtag(self, tag: str):
        super(XNParserBase, self).handle_endtag(tag)
        self._last_tag = ''
        self._last_attrs = list()

    def handle_data(self, data: str):
        super(XNParserBase, self).handle_data(data)
        data_s = data.strip()
        if len(data_s) < 1:
            return
        self.handle_data2(data_s, self._last_tag, self._last_attrs)

    def handle_data2(self, data: str, tag: str, attrs: list):
        pass

    def parse_page_content(self, page: str):
        if page:
            self.feed(page)
