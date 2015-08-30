# -*- coding: utf-8 -*-
import re
import datetime


# this module will define/keep all static Xnova data models
# and basic classes


# XNova universe coordinates model
# [galaxy:solarsystem:planet]
class XNCoords:
    TYPE_PLANET = 1
    TYPE_DEBRIS_FIELD = 2
    TYPE_MOON = 3
    TYPE_WARBASE = 5

    def __init__(self):
        self.galaxy = 0
        self.system = 0
        self.position = 0
        self.target_type = self.TYPE_PLANET
        self.target_name = ''  # optional

    def __str__(self):
        name_str = '{0} '.format(self.target_name) if self.target_name != '' else ''
        coords_str = '[{0}:{1}:{2}]'.format(self.galaxy, self.system, self.position)
        type_str = ''  # default for planet coordinates
        if self.target_type == self.TYPE_DEBRIS_FIELD:
            type_str = ' field '
        elif self.target_type == self.TYPE_MOON:
            type_str = ' moon '
        elif self.target_type == self.TYPE_WARBASE:
            type_str = ' base '
        return '{0}{1}{2}'.format(name_str, type_str, coords_str)

    def set_gsp(self, g: int, s: int, p: int):
        self.galaxy = g
        self.system = s
        self.position = p

    def set_target_field(self):
        self.target_type = self.TYPE_DEBRIS_FIELD

    def set_target_moon(self):
        self.target_type = self.TYPE_MOON

    def set_target_base(self):
        self.target_type = self.TYPE_WARBASE

    def is_empty(self):
        return (self.galaxy == 0) and (self.system == 0) and (self.position == 0)

    def parse_str(self, s: str, raise_on_error=False):
        # '[1:23:456]'
        match = re.match('^\[(\d+):(\d+):(\d+)\]$', s)
        if match:
            self.galaxy = int(match.group(1))
            self.system = int(match.group(2))
            self.position = int(match.group(3))
        else:
            # '1:23:456'
            match = re.match('^(\d+):(\d+):(\d+)$', s)
            if match:
                self.galaxy = int(match.group(1))
                self.system = int(match.group(2))
                self.position = int(match.group(3))
            else:
                if raise_on_error:
                    raise ValueError('XCoords parse error: "{0}"'.format(s))
        return


class XNovaAccountScores:
    def __init__(self):
        self.rank = 0
        self.rank_delta = 0
        self.buildings = 0
        self.buildings_rank = 0  # collected from user info page
        self.fleet = 0
        self.fleet_rank = 0  # collected from user info page
        self.defense = 0
        self.defense_rank = 0  # collected from user info page
        self.science = 0
        self.science_rank = 0  # collected from user info page
        self.total = 0
        self.industry_level = 0
        self.industry_exp = (0, 0)
        self.military_level = 0
        self.military_exp = (0, 0)
        self.wins = 0
        self.losses = 0
        self.fraction = ''
        self.credits = 0

    def __str__(self):
        delta_str = '+{0}'.format(self.rank_delta)
        if self.rank_delta < 0:
            delta_str = '-{0}'.format(self.rank_delta)
        return '{0}({1}): {2} total'.format(self.rank, delta_str, self.total)


class XNovaAccountInfo:
    def __init__(self):
        self.email = '' # set from caller ? not from site
        # collected from overview page
        self.id = 0
        self.ref_link = ''
        self.login = ''
        self.scores = XNovaAccountScores()
        # collected from user info page
        self.main_planet_name = ''
        self.main_planet_coords = XNCoords()
        self.alliance_name = ''

    def __str__(self):
        return '{0} rank {1}'.format(self.login, self.scores)


class XNFlightShips:
    def __init__(self):
        self.mt = 0  # small transport
        self.bt = 0  # big transport
        self.li = 0  # light interceptor
        self.ti = 0  # heavy ceptor
        self.crus = 0  # cruiser
        self.link = 0  # linkor
        self.col = 0   # colonizator
        self.rab = 0   # refiner
        self.spy = 0   # spy
        self.bomber = 0  # bomber
        self.ss = 0     # solar satellite
        self.unik = 0   # destroyer
        self.zs = 0    # death star
        self.lk = 0    # linear cruiser
        self.warbase = 0  # warbase
        # fraction specific ships
        self.f_corvett = 0
        self.f_corsair = 0
        self.f_ceptor = 0
        self.f_dread = 0

    def __len__(self):
        total = self.mt + self.bt + self.li + self.ti + self.crus + self.link \
            + self.col + self.rab + self.spy + self.bomber + self.ss + self.unik \
            + self.zs + self.lk + self.warbase \
            + self.f_ceptor + self.f_corsair + self.f_corvett + self.f_dread
        return total

    def __str__(self):
        def sa(v, s):
            return '{0}: {1}; '.format(s, v) if v > 0 else ''
        ret = sa(self.mt, 'MT')
        ret += sa(self.bt, 'BT')
        ret += sa(self.li, 'LI')
        ret += sa(self.ti, 'TI')
        ret += sa(self.crus, 'CR')
        ret += sa(self.link, 'LINK')
        ret += sa(self.col, 'COL')
        ret += sa(self.rab, 'RAB')
        ret += sa(self.spy, 'SPY')
        ret += sa(self.bomber, 'BOMB')
        ret += sa(self.ss, 'ss')
        ret += sa(self.unik, 'UNIK')
        ret += sa(self.zs, 'DEATH STAR')
        ret += sa(self.lk, 'LK')
        ret += sa(self.warbase, 'BASE')
        ret += sa(self.f_ceptor, 'CEPTOR')
        ret += sa(self.f_corsair, 'CORSAIR')
        ret += sa(self.f_corvett, 'CORVETT')
        ret += sa(self.f_dread, 'DREAD')
        if ret.endswith('; '):
            ret = ret[0:-2]
        return ret


class XNFlightResources:
    def __init__(self):
        self.met = 0
        self.cry = 0
        self.deit = 0

    def __len__(self):
        return self.met + self.cry + self.deit

    def __str__(self):
        sme = 'Met: {0}'.format(str(self.met)) if self.met > 0 else ''
        scry = 'Cry: {0}'.format(str(self.cry)) if self.cry > 0 else ''
        sdeit = 'Deit: {0}'.format(str(self.deit)) if self.deit > 0 else ''
        ret = sme + ' ' + scry + ' ' + sdeit
        return ret.strip()


class XNFlight:
    FLIGHT_DIRS = ['flight', 'return']
    FLIGHT_MISSIONS = ['owndeploy', 'owntransport', 'ownattack', 'ownespionage',
                       'ownharvest', 'owncolony', 'ownfederation', 'ownmissile',
                       'owndestroy', 'ownhold',
                       # enemy/hostile missions
                       'attack', 'espionage', 'missile', 'destroy', 'federation']

    def __init__(self):
        self.ships = XNFlightShips()
        self.res = XNFlightResources()
        self.src = XNCoords()
        self.dst = XNCoords()
        self.mission = None
        self.direction = ''
        self.arrive_datetime = 0

    def __str__(self):
        s = '{0} {1}->{2} ({3}) {4}'.format(
            self.mission, str(self.src), str(self.dst), str(self.ships), str(self.res))
        if self.direction == 'return':
            s += ' return'
        s += (' @' + str(self.arrive_datetime))
        return s


class XNovaFraction:
    def __init__(self, name=None, race_id=None, ico=None):
        self.name = ''
        if name is not None:
            self.name = name
        self.race_id = 0
        if race_id > 0:
            self.race_id = race_id
        self.ico_name = ''
        if ico is not None:
            self.ico_name = ico


def fraction_from_name(name: str) -> XNovaFraction:
    if name == 'Конфедерация':
        ret = XNovaFraction('Конфедерация', 1, 'race1.gif')
        return ret
    elif name == 'Бионики':
        ret = XNovaFraction('Бионики', 2, 'race2.gif')
        return ret
    elif name == 'Сайлоны':
        ret = XNovaFraction('Сайлоны', 3, 'race3.gif')
        return ret
    elif name == 'Древние':
        ret = XNovaFraction('Древние', 4, 'race4.gif')
        return ret
    else:
        return None
