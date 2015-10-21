# -*- coding: utf-8 -*-
import re
import html.parser

from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# converts string to int, silently ignoring errors
def safe_int(data: str):
    ret = 0
    if data == '-':  # indicates as "None", return 0
        return ret
    try:
        ret = int(data.replace('.', ''))
    except ValueError:
        ret = 0
    return ret


# get attribute value from tag attributes
def get_attribute(attrs: list, attr_name: str) -> str:
    """
    Gets attribute value from tag attributes, or None if not found
    :param attrs: attributes list as get from http_parser.handle_starttag()
    :param attr_name: attribute to search for
    :return: given attribute value (str), or None if not found
    """
    if attrs is None:
        return None
    # attrs: list of tuples: [(attr_name1, attr_value2), (), ... ]
    for attr_tuple in attrs:
        if attr_tuple[0] == attr_name:
            return attr_tuple[1]
    return None


def get_tag_classes(attrs: list) -> list:
    """
    Get tag class as list of strings, or None if not set
    :param attrs: attrs list, from handle_starttag()
    :return: strings list, classes if found or None
    """
    a_class = get_attribute(attrs, 'class')
    if a_class is None:
        return None
    cls_list = a_class.split(' ')
    return cls_list


# examples of valid inputs:
#    "8:59:9", "13:59:31" - treated as (hr:min:sec)
#    "8:31" - treated as (min:sec)
#    "38:"  - also min:sec, with empty seconds part
#    "12"   - only seconds.
# returns tuple (hours, minutes, seconds)
#  or (0, 0, 0) on error
def parse_time_left_str(data: str) -> tuple:
    hour = 0
    minute = 0
    second = 0
    # 13:59:31  (hr:min:sec)
    match = re.search(r'(\d+):(\d+):(\d+)', data)
    if match:
        hour = safe_int(match.group(1))
        minute = safe_int(match.group(2))
        second = safe_int(match.group(3))
    else:
        # 8:31  (min:sec)
        match = re.search(r'(\d+):(\d+)', data)
        if match:
            minute = safe_int(match.group(1))
            second = safe_int(match.group(2))
        else:
            # server sometimes sends remaining fleet time
            # without seconds part: <div id="bxxfs4" class="z">38:</div>
            match = re.search(r'(\d+):', data)
            if match:
                minute = safe_int(match.group(1))
            else:
                # just a number (seconds)
                second = safe_int(data)
    return hour, minute, second


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
        if page is not None:
            self.feed(page)
