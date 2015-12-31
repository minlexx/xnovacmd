# -*- coding: utf-8 -*-

import re
from .xn_parser import XNParserBase, safe_int, get_attribute
from .xn_data import XNResourceBundle
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


__doc__ = '''
Almost every page directly related to planet contains the display of
planet's current resources and energy info at the top:
- overview, buildings, researches, fleet, shipyard, defense, resources, merchant ...
- imperium, galaxy do not have it (they do not display single planet)
'''


class PlanetEnergyResParser(XNParserBase):
    def __init__(self):
        super(PlanetEnergyResParser, self).__init__()
        # public
        self.energy_left = 0
        self.energy_total = 0
        self.res_current = XNResourceBundle()
        self.res_max_silos = XNResourceBundle()
        self.res_per_hour = XNResourceBundle()
        # internals
        self._in_eleft = False
        self._in_etot = False
        self.clear()

    def clear(self):
        self.energy_left = 0
        self.energy_total = 0
        self.res_current = XNResourceBundle()
        self.res_max_silos = XNResourceBundle()
        self.res_per_hour = XNResourceBundle()
        # clear internals
        self._in_eleft = False
        self._in_etot = False

    def handle_starttag(self, tag: str, attrs: list):
        super(PlanetEnergyResParser, self).handle_starttag(tag, attrs)
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
        super(PlanetEnergyResParser, self).handle_endtag(tag)
        if tag == 'div':
            if self._in_eleft:
                self._in_eleft = False
            return
        if tag == 'span':
            if self._in_etot:
                self._in_etot = False
            return

    def handle_data2(self, data: str, tag: str, attrs: list):
        super(PlanetEnergyResParser, self).handle_data2(data, tag, attrs)
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
        if tag == 'script':
            script_type = get_attribute(attrs, 'type')
            if script_type is None:
                return
            if script_type == 'text/javascript':
                # var ress = new Array(5827, 14614, 4049);
                # var max = new Array(180000,180000,180000);
                # var production = new Array(0.95805555555556, 0.44055555555556, 0.010277777777778);
                if data.startswith('var ress = new Array('):
                    # logger.debug('[{0}]'.format(data))
                    m = re.search(r'var ress = new Array\((\d+), (\d+), (\d+)\);', data)
                    if m is not None:
                        self.res_current.met = safe_int(m.group(1))
                        self.res_current.cry = safe_int(m.group(2))
                        self.res_current.deit = safe_int(m.group(3))
                        logger.debug('Got planet res_current: {0}'.format(str(self.res_current)))
                    m = re.search(r'var max = new Array\((\d+),(\d+),(\d+)\);', data)
                    if m is not None:
                        self.res_max_silos.met = safe_int(m.group(1))
                        self.res_max_silos.cry = safe_int(m.group(2))
                        self.res_max_silos.deit = safe_int(m.group(3))
                        logger.debug('Got planet res_max: {0}'.format(str(self.res_max_silos)))
                    m = re.search(r'var production = new Array\(([\d\.]+), ([\d\.]+), ([\d\.]+)\);', data)
                    if m is not None:
                        try:
                            met_per_second = float(m.group(1))
                            cry_per_second = float(m.group(2))
                            deit_per_second = float(m.group(3))
                            self.res_per_hour.met = int(met_per_second * 3600)
                            self.res_per_hour.cry = int(cry_per_second * 3600)
                            self.res_per_hour.deit = int(deit_per_second * 3600)
                            logger.debug('Got planet res per hour: {0}'.format(str(self.res_per_hour)))
                        except ValueError as e:
                            logger.warn('Failed to convert to float some of: {0}, {1}, {2}'.format(
                                m.group(1), m.group(2), m.group(3)))


# <div title="Энергетический баланс"><span class="positive">5</span></div>
# <div title="Энергетический баланс">0</div>
# <span title="Выработка энергии" class="hidden-xs"><font color="#00ff00">12.515</font></span>

# <script type="text/javascript">
#   var ress = new Array(2265601, 4207911, 426557);
#   var max = new Array(11062500,11062500,6937500);
#   var production = new Array(14.3925, 7.2386111111111, 2.4711111111111);
#   timeouts['res_count'] = window.setInterval(XNova.updateResources, 1000);
#   var serverTime = 1451535635000 - Djs + (timezone + 6) * 1800000;
# </script>
