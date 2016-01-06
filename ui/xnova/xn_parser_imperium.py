# -*- coding: utf-8 -*-
import re

from .xn_data import XNCoords, XNPlanet
from .xn_parser import XNParserBase, safe_int, get_attribute, get_tag_classes
from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


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
        # used to store planet energy_total, since we cannot
        # parse it from imperium pagem and overwriting it with zeroes
        self._planet_energy_totals = dict()
        self._planet_prev_res_max = dict()
        self._planet_prev_build_items = dict()

    def clear(self):
        self.in_imp_1 = False
        self.in_picdef = False
        self._phase = 'pics'
        self._phase_res = ''
        self._counter = 0
        # store state that will be otherwise cleared by imperium update
        self._planet_energy_totals = dict()
        self._planet_prev_res_max = dict()
        self._planet_prev_build_items = dict()
        self.save_previous_info()
        # somewhat output data
        self.planet_ids = []
        self.planet_pics = []
        self.planets = []

    def save_previous_info(self):
        logger.debug('saving prev. info about {0} planets...'.format(len(self.planets)))
        for pl in self.planets:
            self._planet_energy_totals[pl.planet_id] = pl.energy.energy_total
            self._planet_prev_res_max[pl.planet_id] = pl.res_max_silos
            self._planet_prev_build_items[pl.planet_id] = dict()
            self._planet_prev_build_items[pl.planet_id]['bi'] = pl.buildings_items
            self._planet_prev_build_items[pl.planet_id]['ri'] = pl.research_items
            self._planet_prev_build_items[pl.planet_id]['rfi'] = pl.researchfleet_items
            self._planet_prev_build_items[pl.planet_id]['si'] = pl.shipyard_tems
            self._planet_prev_build_items[pl.planet_id]['di'] = pl.defense_items
            self._planet_prev_build_items[pl.planet_id]['spi'] = pl.shipyard_progress_items

    def restore_previous_info(self):
        logger.debug('restoring prev. energy for {0} planets...'.format(len(self._planet_energy_totals)))
        # restore planets energy totals, res max silos
        for planet_id in self._planet_energy_totals.keys():
            for pl in self.planets:
                if pl.planet_id == planet_id:
                    pl.energy.energy_total = self._planet_energy_totals[planet_id]
                    pl.res_max_silos = self._planet_prev_res_max[pl.planet_id]
                    break
        # restore planet buildings items
        logger.debug('restoring prev. build items for {0} planets...'.format(len(self._planet_prev_build_items)))
        for planet_id in self._planet_prev_build_items.keys():
            for pl in self.planets:
                if pl.planet_id == planet_id:
                    pl.buildings_items = self._planet_prev_build_items[planet_id]['bi']
                    pl.research_items = self._planet_prev_build_items[planet_id]['ri']
                    pl.researchfleet_items = self._planet_prev_build_items[planet_id]['rfi']
                    pl.shipyard_tems = self._planet_prev_build_items[planet_id]['si']
                    pl.defense_items = self._planet_prev_build_items[planet_id]['di']
                    pl.shipyard_progress_items = self._planet_prev_build_items[planet_id]['spi']

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

    def set_phase(self, ph):
        self._phase = ph
        self._counter = 0

    def inc_counter_and_check_reset_phase(self):
        self._counter += 1
        if self._counter >= len(self.planets):
            self._counter = 0
            self._phase = ''

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
                            planet.detect_type_by_pic_url()
                            self.planets.append(planet)
                            self._counter += 1
                        # reset counter, it will count current planet to store info to
                        self._counter = 0
                    elif data == 'Координаты':
                        self.set_phase('coords')
                    elif data == 'Поля':
                        self.set_phase('fields')
                    elif data == 'Рудник металла':
                        self.set_phase('met_factory')
                    elif data == 'Рудник кристалла':
                        self.set_phase('cry_factory')
                    elif data == 'Синтезатор дейтерия':
                        self.set_phase('deit_factory')
                    elif data == 'Солнечная батарея':
                        self.set_phase('solar_station')
                    elif data == 'Термоядерный реактор':
                        self.set_phase('nuclear_station')
                    elif data == 'Фабрика роботов':
                        self.set_phase('robotics_factory')
                    elif data == 'Фабрика нанитов':
                        self.set_phase('nanites_factory')
                    elif data == 'Верфь':
                        self.set_phase('shipyard')
                    elif data == 'Склад металла':
                        self.set_phase('met_silo')
                    elif data == 'Склад кристалла':
                        self.set_phase('cry_silo')
                    elif data == 'Емкость дейтерия':
                        self.set_phase('deit_silo')
                    elif data == 'Лаборатория':
                        self.set_phase('lab')
                    elif data == 'Терраформер':
                        self.set_phase('terraformer')
                    elif data == 'Склад альянса':
                        self.set_phase('alliance_silo')
                    elif data == 'Ракетная шахта':
                        self.set_phase('rocket_silo')
                    elif data == 'Лунная база':
                        self.set_phase('lunar_base')
                    elif data == 'Сенсорная фаланга':
                        self.set_phase('lunar_phalanx')
                    elif data == 'Межгалактические врата':
                        self.set_phase('gates')
                    elif data == 'Малый транспорт':
                        self.set_phase('ship_mt')
                    elif data == 'Большой транспорт':
                        self.set_phase('ship_bt')
                    elif data == 'Лёгкий истребитель':
                        self.set_phase('ship_li')
                    elif data == 'Тяжёлый истребитель':
                        self.set_phase('ship_ti')
                    elif data == 'Крейсер':
                        self.set_phase('ship_crus')
                    elif data == 'Линкор':
                        self.set_phase('ship_link')
                    elif data == 'Колонизатор':
                        self.set_phase('ship_col')
                    elif data == 'Переработчик':
                        self.set_phase('ship_rab')
                    elif data == 'Шпионский зонд':
                        self.set_phase('ship_spy')
                    elif data == 'Бомбардировщик':
                        self.set_phase('ship_bomber')
                    elif data == 'Солнечный спутник':
                        self.set_phase('ship_ss')
                    elif data == 'Уничтожитель':
                        self.set_phase('ship_unik')
                    elif data == 'Звезда смерти':
                        self.set_phase('ship_zs')
                    elif data == 'Линейный крейсер':
                        self.set_phase('ship_lk')
                    elif data == 'Передвижная база':
                        self.set_phase('ship_warbase')
                    elif data == 'Корвет':
                        self.set_phase('ship_f_corvett')
                    elif data == 'Перехватчик':
                        self.set_phase('ship_f_ceptor')
                    elif data == 'Дредноут':
                        self.set_phase('ship_f_dread')
                    elif data == 'Корсар':
                        self.set_phase('ship_f_corsair')
                    elif data == 'Ракетная установка':
                        self.set_phase('def_ru')
                    elif data == 'Легкий лазер':
                        self.set_phase('def_ll')
                    elif data == 'Тяжёлый лазер':
                        self.set_phase('def_tl')
                    elif data == 'Пушка Гаусса':
                        self.set_phase('def_gauss')
                    elif data == 'Ионное орудие':
                        self.set_phase('def_ion')
                    elif data == 'Плазменное орудие':
                        self.set_phase('def_plasma')
                    elif data == 'Малый щитовой купол':
                        self.set_phase('def_small_dome')
                    elif data == 'Большой щитовой купол':
                        self.set_phase('def_big_dome')
                    elif data == 'Ракета-перехватчик':
                        self.set_phase('def_defender_rocket')
                    elif data == 'Межпланетная ракета':
                        self.set_phase('def_attack_rocket')
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
                elif self._phase == 'coords':
                    pass  # this case is handled, but no work is needed here
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
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'cry_factory':
                    self.planets[self._counter].buildings.cry_factory = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'deit_factory':
                    self.planets[self._counter].buildings.deit_factory = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'solar_station':
                    self.planets[self._counter].buildings.solar_station = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'nuclear_station':
                    self.planets[self._counter].buildings.nuclear_station = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'robotics_factory':
                    self.planets[self._counter].buildings.robotics_factory = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'nanites_factory':
                    self.planets[self._counter].buildings.nanites_factory = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'shipyard':
                    self.planets[self._counter].buildings.shipyard = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'met_silo':
                    self.planets[self._counter].buildings.met_silo = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'cry_silo':
                    self.planets[self._counter].buildings.cry_silo = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'deit_silo':
                    self.planets[self._counter].buildings.deit_silo = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'lab':
                    self.planets[self._counter].buildings.lab = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'terraformer':
                    self.planets[self._counter].buildings.terraformer = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'alliance_silo':
                    self.planets[self._counter].buildings.alliance_silo = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'rocket_silo':
                    self.planets[self._counter].buildings.rocket_silo = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'lunar_base':
                    self.planets[self._counter].buildings.lunar_base = safe_int(data)
                    if self.planets[self._counter].buildings.lunar_base > 0:
                        self.planets[self._counter].is_moon = True  # omg
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'lunar_phalanx':
                    self.planets[self._counter].buildings.lunar_phalanx = safe_int(data)
                    if self.planets[self._counter].buildings.lunar_phalanx > 0:
                        self.planets[self._counter].is_moon = True  # omg
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'gates':
                    self.planets[self._counter].buildings.gates = safe_int(data)
                    # dunno, may be moon, may be warbase :/
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_mt':
                    self.planets[self._counter].ships.mt = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_bt':
                    self.planets[self._counter].ships.bt = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_li':
                    self.planets[self._counter].ships.li = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_ti':
                    self.planets[self._counter].ships.ti = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_crus':
                    self.planets[self._counter].ships.crus = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_link':
                    self.planets[self._counter].ships.link = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_col':
                    self.planets[self._counter].ships.col = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_rab':
                    self.planets[self._counter].ships.rab = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_spy':
                    self.planets[self._counter].ships.spy = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_bomber':
                    self.planets[self._counter].ships.bomber = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_ss':
                    self.planets[self._counter].ships.ss = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_unik':
                    self.planets[self._counter].ships.unik = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_zs':
                    self.planets[self._counter].ships.zs = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_lk':
                    self.planets[self._counter].ships.lk = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_warbase':
                    self.planets[self._counter].ships.warbase = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_f_corvett':
                    self.planets[self._counter].ships.f_corvett = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_f_corsair':
                    self.planets[self._counter].ships.f_corsair = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_f_ceptor':
                    self.planets[self._counter].ships.f_ceptor = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'ship_f_dread':
                    self.planets[self._counter].ships.f_dread = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_ru':
                    self.planets[self._counter].defense.ru = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_ll':
                    self.planets[self._counter].defense.ll = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_tl':
                    self.planets[self._counter].defense.tl = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_gauss':
                    self.planets[self._counter].defense.gauss = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_ion':
                    self.planets[self._counter].defense.ion = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_plasma':
                    self.planets[self._counter].defense.plasma = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_small_dome':
                    self.planets[self._counter].defense.small_dome = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_big_dome':
                    self.planets[self._counter].defense.big_dome = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_defender_rocket':
                    self.planets[self._counter].defense.defender_rocket = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                elif self._phase == 'def_attack_rocket':
                    self.planets[self._counter].defense.attack_rocket = safe_int(data)
                    self.inc_counter_and_check_reset_phase()
                else:
                    if self._phase != '':
                        logger.debug('Unhandled data in phase [{0}]: [{1}]'.format(self._phase, data))
            return  # tag th
        if tag == 'a':
            href = get_attribute(attrs, 'href')
            if href is not None:
                if href.startswith('?set=galaxy&r=3'):
                    # coords link <a href="?set=galaxy&r=3&galaxy=1&system=7">1:7:9</a>
                    if self._phase == 'coords':
                        self.planets[self._counter].coords.parse_str(data)
                        logger.debug('planet[{0}].coords = {1}'.format(
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
            logger.debug('Loaded info about {0} planet(s)'.format(len(self.planets)))
            # for pl in self.planets:
            #    logger.debug('Planet {0} buildings: {1}'.format(str(pl), str(pl.buildings)))
            #    logger.debug('Planet {0} ships:     {1}'.format(str(pl), str(pl.ships)))
            #    logger.debug('Planet {0} defense:   {1}'.format(str(pl), str(pl.defense)))
            # restore some planets previous data
            self.restore_previous_info()
