# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords, XNPlanet
from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


class ImperiumParser(XNParserBase):
    def __init__(self):
        super(ImperiumParser, self).__init__()
        self.in_imp_1 = False
        self.in_picdef = False
        self._phase = 'pics'
        self._phase_res = ''
        self._counter = 0
        # somewhat output data
        self.planet_ids = []
        self.planet_pics = []
        self.planets = []

    def handle_starttag(self, tag: str, attrs: list):
        super(ImperiumParser, self).handle_starttag(tag, attrs)
        if not self.in_imp_1 and (tag == 'div'):
            div_class = get_tag_classes(attrs)
            if div_class is None:
                return
            if 'table-responsive' in div_class:
                self.in_imp_1 = True
            return
        if self.in_imp_1 and (tag == 'th'):
            th_width = get_attribute(attrs, 'width')
            if th_width is None:
                return
            if th_width == '75':
                self.in_picdef = True
            return
        if self.in_picdef and (tag == 'a'):
            href = get_attribute(attrs, 'href')
            if href is None:
                return
            m = re.search(r'\?set=overview&cp=(\d+)', href)
            if m:
                planet_id = safe_int(m.group(1))
                self.planet_ids.append(planet_id)
                # logger.debug('Found planet id: {0}'.format(planet_id))
        if self.in_picdef and (tag == 'img'):
            img_src = get_attribute(attrs, 'src')
            if img_src is None:
                return
            self.planet_pics.append(img_src)
            # logger.debug('Found planet img: {0}'.format(img_src))
        return

    def handle_data2(self, data: str, tag: str, attrs: list):
        # logger.debug('data in tag [{0}]: [{1}]'.format(tag, data))
        if not self.in_imp_1:
            return
        if tag == 'th':
            th_colspan = get_attribute(attrs, 'colspan')
            th_rowspan = get_attribute(attrs, 'rowspan')
            if th_colspan is not None:
                if th_colspan == '2':
                    if data == 'Название':
                        self._phase = 'titles'
                        # now switching to new parse phase
                        # initialize planets array, now we know how many planets do we have
                        self._counter = 0
                        for pid in self.planet_ids:
                            planet = XNPlanet()
                            planet.planet_id = pid
                            planet.pic_url = self.planet_pics[self._counter]
                            self.planets.append(planet)
                            self._counter += 1
                        # reset counter, it will count current planet to store info to
                        self._counter = 0
                    elif data == 'Координаты':
                        self._phase = 'coords'
                        self._counter = 0
                    elif data == 'Поля':
                        self._phase = 'fields'
                        self._counter = 0
                    elif data == 'Рудник металла':
                        self._phase = 'met_factory'
                        self._counter = 0
                    elif data == 'Рудник кристалла':
                        self._phase = 'cry_factory'
                        self._counter = 0
                    elif data == 'Синтезатор дейтерия':
                        self._phase = 'deit_factory'
                        self._counter = 0
                    elif data == 'Солнечная батарея':
                        self._phase = 'solar_station'
                        self._counter = 0
                    elif data == 'Термоядерный реактор':
                        self._phase = 'nuclear_station'
                        self._counter = 0
                    elif data == 'Фабрика роботов':
                        self._phase = 'robotics_factory'
                        self._counter = 0
                    elif data == 'Фабрика нанитов':
                        self._phase = 'nanites_factory'
                        self._counter = 0
                    elif data == 'Верфь':
                        self._phase = 'shipyard'
                        self._counter = 0
                    elif data == 'Склад металла':
                        self._phase = 'met_silo'
                        self._counter = 0
                    elif data == 'Склад кристалла':
                        self._phase = 'cry_silo'
                        self._counter = 0
                    elif data == 'Емкость дейтерия':
                        self._phase = 'deit_silo'
                        self._counter = 0
                    elif data == 'Лаборатория':
                        self._phase = 'lab'
                        self._counter = 0
                    elif data == 'Терраформер':
                        self._phase = 'terraformer'
                        self._counter = 0
                    elif data == 'Склад альянса':
                        self._phase = 'alliance_silo'
                        self._counter = 0
                    elif data == 'Ракетная шахта':
                        self._phase = 'rocket_silo'
                        self._counter = 0
                    elif data == 'Лунная база':
                        self._phase = 'lunar_base'
                        self._counter = 0
                    elif data == 'Сенсорная фаланга':
                        self._phase = 'lunar_phalanx'
                        self._counter = 0
                    elif data == 'Межгалактические врата':
                        self._phase = 'gates'
                        self._counter = 0
                    return  # <th colspan="2"> ... </th>
            if th_rowspan is not None:
                if th_rowspan == '5':
                    if data == 'на планете':
                        if self._phase == 'resources':
                            self._phase_res = ''
                if th_rowspan == '3':
                    if data == 'в час':
                        if self._phase == 'res_per_hour':
                            self._phase_res = ''
                if th_rowspan == '6':
                    if data == 'Производство':
                        self._phase = 'prod_powers'
                        self._phase_res = ''
            if (attrs is None) or (len(attrs) == 0):
                # empty <th> tag with no attributes
                # logger.debug('data in phase [{0}]: [{1}]'.format(self._phase, data))
                if self._phase == 'titles':
                    # save planet name both in planet object
                    # and in its coords object
                    self.planets[self._counter].name = data
                    self.planets[self._counter].coords = XNCoords(0, 0, 0)
                    self.planets[self._counter].coords.target_name = data  # optional, but...
                    # logger.debug('planet[{0}].name = {1}'.format(self._counter, data))
                    # move to next planet
                    self._counter += 1
                elif self._phase == 'fields':
                    m = re.match(r'(\d+)/(\d+)', data)
                    if m:
                        fields_busy = safe_int(m.group(1))
                        fields_total = safe_int(m.group(2))
                        self.planets[self._counter].fields_busy = fields_busy
                        self.planets[self._counter].fields_total = fields_total
                        # logger.debug('planet[{0}].fields = {1}/{2}'.format(
                        #    self._counter, fields_busy, fields_total))
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = 'res_current'
                        self._phase_res = ''
                elif self._phase == 'res_current':
                    if data == 'Металл':
                        self._phase_res = 'met'
                    elif data == 'Кристалл':
                        self._phase_res = 'cry'
                    elif data == 'Дейтерий':
                        self._phase_res = 'deit'
                    elif data == 'Энергия':
                        self._phase_res = 'energy'
                    elif data == 'Заряд':
                        self._phase_res = 'charge'
                        # logger.debug('START charge')
                    else:
                        # logger.debug(data)
                        value = safe_int(data)
                        if self._phase_res == 'met':
                            self.planets[self._counter].res_current.met = value
                        elif self._phase_res == 'cry':
                            self.planets[self._counter].res_current.cry = value
                        elif self._phase_res == 'deit':
                            self.planets[self._counter].res_current.deit = value
                        elif self._phase_res == 'energy':
                            self.planets[self._counter].energy.energy_left = value
                        # log only if there was assignment
                        if self._phase_res != '':
                            # logger.debug('planet[{0}].{1}.{2} = {3}'.format(
                            #    self._counter, self._phase, self._phase_res, value))
                            self._counter += 1
                        if self._counter >= len(self.planets):
                            self._counter = 0
                            self._phase_res = ''
                elif self._phase == 'res_per_hour':
                    if data == 'Металл':
                        self._phase_res = 'met'
                    elif data == 'Кристалл':
                        self._phase_res = 'cry'
                    elif data == 'Дейтерий':
                        self._phase_res = 'deit'
                    else:
                        value = safe_int(data)
                        if self._phase_res == 'met':
                            self.planets[self._counter].res_per_hour.met = value
                        elif self._phase_res == 'cry':
                            self.planets[self._counter].res_per_hour.cry = value
                        elif self._phase_res == 'deit':
                            self.planets[self._counter].res_per_hour.deit = value
                        if self._phase_res != '':
                            # logger.debug('planet[{0}].{1}.{2} = {3}'.format(
                            #    self._counter, self._phase, self._phase_res, value))
                            self._counter += 1
                        if self._counter >= len(self.planets):
                            self._counter = 0
                            if self._phase_res == 'deit':
                                # logger.debug('STOP res_per_hour')
                                self._phase = ''
                            self._phase_res = ''
                elif self._phase == 'prod_powers':
                    # logger.debug('prod_powers data [{0}]'.format(data))
                    if data == 'Металл':
                        self._phase_res = 'met'
                    elif data == 'Кристаллы':
                        self._phase_res = 'cry'
                    elif data == 'Дейтерий':
                        self._phase_res = 'deit'
                    elif data == 'Солн. ст.':
                        self._phase_res = 'solar'
                    elif data == 'Терм. ст.':
                        self._phase_res = 'nuclear'
                    elif data == 'Спутники':
                        self._phase_res = 'ss'
                    # logger.debug('prod_powers data [{0}] phase_res: {1}'.format(data, self._phase_res))
                elif self._phase == 'met_factory':
                    self.planets[self._counter].buildings.met_factory = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'cry_factory':
                    self.planets[self._counter].buildings.cry_factory = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'deit_factory':
                    self.planets[self._counter].buildings.deit_factory = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'solar_station':
                    self.planets[self._counter].buildings.solar_station = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'nuclear_station':
                    self.planets[self._counter].buildings.nuclear_station = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'robotics_factory':
                    self.planets[self._counter].buildings.robotics_factory = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'nanites_factory':
                    self.planets[self._counter].buildings.nanites_factory = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'shipyard':
                    self.planets[self._counter].buildings.shipyard = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'met_silo':
                    self.planets[self._counter].buildings.met_silo = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'cry_silo':
                    self.planets[self._counter].buildings.cry_silo = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'deit_silo':
                    self.planets[self._counter].buildings.deit_silo = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'lab':
                    self.planets[self._counter].buildings.lab = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'terraformer':
                    self.planets[self._counter].buildings.terraformer = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'alliance_silo':
                    self.planets[self._counter].buildings.alliance_silo = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'rocket_silo':
                    self.planets[self._counter].buildings.rocket_silo = safe_int(data)
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'lunar_base':
                    self.planets[self._counter].buildings.lunar_base = safe_int(data)
                    if self.planets[self._counter].buildings.lunar_base > 0:
                        self.planets[self._counter].is_moon = True  # omg
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'lunar_phalanx':
                    self.planets[self._counter].buildings.lunar_phalanx = safe_int(data)
                    if self.planets[self._counter].buildings.lunar_phalanx > 0:
                        self.planets[self._counter].is_moon = True  # omg
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                elif self._phase == 'gates':
                    self.planets[self._counter].buildings.gates = safe_int(data)
                    # dunno, may be moon, may be warbase :/
                    self._counter += 1
                    if self._counter >= len(self.planets):
                        self._counter = 0
                        self._phase = ''
                #else:
                #    if self._phase != '':
                #        logger.debug('data in phase [{0}]: [{1}]'.format(self._phase, data))
            return  # tag th
        if tag == 'a':
            href = get_attribute(attrs, 'href')
            if href is not None:
                if href.startswith('?set=galaxy&r=3'):
                    # coords link <a href="?set=galaxy&r=3&galaxy=1&system=7">1:7:9</a>
                    if self._phase == 'coords':
                        self.planets[self._counter].coords.parse_str(data)
                        logger.info('planet[{0}].coords = {1}'.format(
                            self._counter, self.planets[self._counter].coords))
                        self._counter += 1
        if (tag == 'font') and (self._phase == 'res_current') and (self._phase_res == 'charge'):
            # logger.debug('planet[{0}].energy.charge_percent = {1}'.format(self._counter, data))
            self.planets[self._counter].energy.charge_percent = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase = 'res_per_hour'
                self._phase_res = ''
                # logger.debug('END charge')
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'met'):
            # logger.debug('planet[{0}].prod_powers.met = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.met = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'cry'):
            # logger.debug('planet[{0}].prod_powers.cry = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.cry = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'deit'):
            # logger.debug('planet[{0}].prod_powers.deit = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.deit = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'solar'):
            # logger.debug('planet[{0}].prod_powers.solar = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.solar = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'nuclear'):
            # logger.debug('planet[{0}].prod_powers.nuclear = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.nuclear = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
        if (tag == 'font') and (self._phase == 'prod_powers') and (self._phase_res == 'ss'):
            # logger.debug('planet[{0}].prod_powers.ss = {1}'.format(self._counter, data))
            self.planets[self._counter].prod_powers.ss = safe_int(data)
            self._counter += 1
            if self._counter >= len(self.planets):
                self._counter = 0
                self._phase_res = ''
                self._phase = ''
                # logger.debug('END prod_powers')
        return  # def handle_data()

    def handle_endtag(self, tag: str):
        super(ImperiumParser, self).handle_endtag(tag)
        if self.in_picdef and (tag == 'th'):
            self.in_picdef = False
            return
        if tag == 'html':
            logger.info('Loaded info about {0} planet(s)'.format(len(self.planets)))
            return
