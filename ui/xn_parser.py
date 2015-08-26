import html.parser

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


# extends html.parser.HTMLParser class
# by remembering tags path
class XNParserBase(html.parser.HTMLParser):
    def __init__(self):
        super(XNParserBase, self).__init__(strict=False, convert_charrefs=True)
        self._path = []

    def get_path(self):
        path = ''
        for tag in self._path:
            if path != '':
                path += '|'
            path += tag
        return path

    def _path_append(self, tag: str, attrs: list):
        # skip "meta" tags, xnova has unclosed meta tags!
        # also as <br> <input> instead of <br />, <input />
        skip_path_tags = ['meta', 'br', 'input']
        tag_classid = ''
        if len(attrs) > 0:
            # [('class', 'col-xs-4 text-center')] ...
            tag_class = ''
            tag_id = ''
            for attr in attrs:
                if attr[0] == 'id':
                    tag_id = '#' + attr[1]
                if attr[0] == 'class':
                    tag_class = '.' + attr[1]
            tag_classid = '{0}{1}'.format(tag_class, tag_id)
            tag_classid = tag_classid.strip()
        if tag not in skip_path_tags:
            self._path.append(tag + tag_classid)

    def handle_starttag(self, tag: str, attrs: list):
        super(XNParserBase, self).handle_starttag(tag, attrs)
        self._path_append(tag, attrs)
        self.handle_path(tag, attrs, self.get_path())

    def handle_endtag(self, tag: str):
        super(XNParserBase, self).handle_endtag(tag)
        if len(self._path) > 0:
            self._path.pop()

    def handle_data(self, data: str):
        super(XNParserBase, self).handle_data(data)

    def handle_path(self, tag: str, attrs: list, path: str):
        pass

    def parse_page_content(self, page: str):
        if page:
            self.feed(page)


# parses overview page
class OverviewParser(XNParserBase):
    def __init__(self):
        super(OverviewParser, self).__init__()

    def handle_path(self, tag: str, attrs: list, path: str):
        attrs_s = ''
        if len(attrs) > 0:
            attrs_s = ';  attrs: {0}'.format(str(attrs))
        logger.debug('path [{0}]: {1}{2}'.format(tag, path, attrs_s))

    def handle_data(self, data: str):
        data_s = data.strip()
        if len(data_s) > 0:
            logger.debug('data [{0}]:    path: [{1}]'.format(data_s, self.get_path()))
