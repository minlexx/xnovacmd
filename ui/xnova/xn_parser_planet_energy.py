# -*- coding: utf-8 -*-

from .xn_parser import XNParserBase, safe_int, get_attribute
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


__doc__ = '''
Almost every page directly related to planet contains the display of
planet's current resources and energy info at the top:
- overview, buildings, researches, fleet, shipyard, defense, resources, merchant ...
- imperium, galaxy do not have it (they do not display single planet)
'''


class PlanetEnergyParser(XNParserBase):
    def __init__(self):
        super(PlanetEnergyParser, self).__init__()
        # public
        self.energy_left = 0
        self.energy_total = 0
        # internals
        self._in_eleft = False
        self._in_etot = False
        self.clear()

    def clear(self):
        self.energy_left = 0
        self.energy_total = 0
        # clear internals
        self._in_eleft = False
        self._in_etot = False

    def handle_starttag(self, tag: str, attrs: list):
        super(PlanetEnergyParser, self).handle_starttag(tag, attrs)
        if tag == 'div':
            div_title = get_attribute(attrs, 'title')
            if div_title is None:
                return
            if div_title == 'Энергетический баланс':
                self._in_eleft = True
            return
        if tag == 'span':
            span_title = get_attribute(attrs, 'title')
            if span_title is None:
                return
            if span_title == 'Выработка энергии':
                self._in_etot = True
            return

    def handle_endtag(self, tag: str):
        super(PlanetEnergyParser, self).handle_endtag(tag)
        if tag == 'div':
            if self._in_eleft:
                self._in_eleft = False
            return
        if tag == 'span':
            if self._in_etot:
                self._in_etot = False
            return

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetEnergyParser, self).handle_data2(data, tag, attrs)
        # if self._in_div_viewport_buildings:
        #    logger.debug('  handle_data2(tag={0}, data={1}, attrs={2})'.format(tag, data, attrs))
        if tag == 'span':
            if self._in_eleft:
                self.energy_left = safe_int(data)
                logger.debug('Got energy left: {0}'.format(self.energy_left))
            return
        if tag == 'font':
            if self._in_etot:
                self.energy_total = safe_int(data)
                logger.debug('Got energy total: {0}'.format(self.energy_total))
            return
        if tag == 'div':
            div_title = get_attribute(attrs, 'title')
            if div_title == 'Энергетический баланс':
                if data == '0':
                    self.energy_left = 0
                    logger.debug('Got energy left = 0 from div (no span)')

# <div title="Энергетический баланс"><span class="positive">5</span></div>
# <div title="Энергетический баланс">0</div>
# <span title="Выработка энергии" class="hidden-xs"><font color="#00ff00">12.515</font></span>
