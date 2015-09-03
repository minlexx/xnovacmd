# -*- coding: utf-8 -*-
import re

"""This module will define/keep all static Xnova data models
and basic classes
"""


class XNCoords:
    """
    XNova universe coordinates data model
    can parse strings like "[galaxy:solarsystem:planet]"
    also holds exact target object type - planet, moon, or debris field
    """
    TYPE_PLANET = 1
    TYPE_DEBRIS_FIELD = 2
    TYPE_MOON = 3
    TYPE_WARBASE = 5

    def __init__(self, g=0, s=0, p=0):
        self.galaxy = g
        self.system = s
        self.position = p
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


class XNAccountScores:
    """
    All user account statistics
    """
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


class XNAccountInfo:
    """
    Holds information about user profile (name, main planet) and statistics
    """
    def __init__(self):
        self.email = '' # set from caller ? not from site
        # collected from overview page
        self.id = 0
        self.ref_link = ''
        self.login = ''
        self.scores = XNAccountScores()
        # collected from user info page
        self.main_planet_name = ''
        self.main_planet_coords = XNCoords()
        self.alliance_name = ''

    def __str__(self):
        return '{0} rank {1}'.format(self.login, self.scores)


class XNShipsBundle:
    """
    Holds information about ships bundle
    for example, in flight, on planet's orbit, etc
    """
    def __init__(self):
        self.mt = 0  # small transport
        self.bt = 0  # big transport
        self.li = 0  # light interceptor
        self.ti = 0  # heavy ceptor
        self.crus = 0  # cruiser
        self.link = 0  # linkor
        self.col = 0   # colonizer
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
        """
        :return total ships count in bundle
        """
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


class XNResourceBundle:
    """
    Hold information about resources bundle, used in many situations:
    - resources on planet
    - resources in flight inside ships
    """
    def __init__(self, m=0, c=0, d=0):
        self.met = m
        self.cry = c
        self.deit = d

    def __len__(self):
        """
        :return Total resource count, sum of met+cry+deit
        """
        return self.met + self.cry + self.deit

    def __format__(self, format_spec):
        """ Format_spec accepts:
         {m} metal count
         {c} crystal count
         {d} deit count
         {M} metal count, or empty string if 0
         {C} crystal count, or empty string if 0
         {D} deit count, or empty string if 0
         """
        met_e = '' if self.met == 0 else str(self.met)
        cry_e = '' if self.cry == 0 else str(self.cry)
        deit_e = '' if self.deit == 0 else str(self.deit)
        ret = format_spec
        ret = ret.replace('{m}', str(self.met))
        ret = ret.replace('{c}', str(self.cry))
        ret = ret.replace('{d}', str(self.deit))
        ret = ret.replace('{M}', met_e)
        ret = ret.replace('{C}', cry_e)
        ret = ret.replace('{D}', deit_e)
        return ret

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
        self.ships = XNShipsBundle()
        self.res = XNResourceBundle()
        self.src = XNCoords()
        self.dst = XNCoords()
        self.mission = None
        self.direction = ''
        self.arrive_datetime = 0

    @staticmethod
    def is_hostile_mission(mission_str):
        if mission_str in ['attack', 'espionage', 'missile', 'destroy', 'federation']:
            return True
        return False

    def __str__(self):
        s = '{0} {1}->{2} ({3}) {4}'.format(
            self.mission, str(self.src), str(self.dst), str(self.ships), str(self.res))
        if self.direction == 'return':
            s += ' return'
        s += (' @' + str(self.arrive_datetime))
        return s


class XNFraction:
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


def fraction_from_name(name: str) -> XNFraction:
    if name == 'Конфедерация':
        ret = XNFraction('Конфедерация', 1, 'race1.gif')
        return ret
    elif name == 'Бионики':
        ret = XNFraction('Бионики', 2, 'race2.gif')
        return ret
    elif name == 'Сайлоны':
        ret = XNFraction('Сайлоны', 3, 'race3.gif')
        return ret
    elif name == 'Древние':
        ret = XNFraction('Древние', 4, 'race4.gif')
        return ret
    else:
        return None


class XNBuildingsBundle:
    """
    holds info about planet's buildings levels
    """
    def __init__(self):
        self.met_factory = 0
        self.cry_factory = 0
        self.deit_factory = 0
        self.solar_station = 0
        self.nuclear_station = 0
        self.robotics_factory = 0
        self.nanites_factory = 0
        self.shipyard = 0
        self.met_silo = 0
        self.cry_silo = 0
        self.deit_silo = 0
        self.lab = 0
        self.terraformer = 0
        self.alliance_silo = 0
        self.rocket_silo = 0
        self.lunar_base = 0
        self.lunar_phalanx = 0
        self.gates = 0


class XNDefenseBundle:
    """
    holds all info about planet's defenses count
    """
    def __init__(self):
        self.rocket = 0
        self.light_laser = 0
        self.heavy_laser = 0
        self.gauss = 0
        self.ion = 0
        self.plasma = 0
        self.small_dome = 0
        self.big_dome = 0
        self.defender_rocket = 0
        self.attack_rocket = 0


class XNPlanetProductionPowers:
    """
    Acts like a sctructure to hold values for individual
    production power settings (levels)
    """
    def __init__(self):
        self.met = 0
        self.cry = 0
        self.deit = 0
        self.solar_station = 0
        self.nuclear_station = 0
        self.satellites = 0


class XNPlanetEnergyInfo:
    """
    Acts like a structure to hold information
    about planet's energy situation
    """
    def __init__(self):
        self.energy_left = 0
        self.energy_total = 0
        self.charge_percent = 0


class XNDebrisField:
    """ planet debris field, contains only metal and crystal """
    def __init__(self, m=0, c=0):
        self.met = m
        self.cry = c

    def __len__(self):
        return self.met + self.cry

    def __str__(self):
        return 'Debris field (Metal: {0}, Crystal: {1})'.format(self.met, self.cry)


class XNPlanet:
    """
    Main planet model, holding all information
    """
    def __init__(self, name=None, coords=None, planet_id=0):
        self.planet_id = planet_id
        self.name = name if name is not None else ''
        self.pic_url = ''
        self.coords = coords if isinstance(coords, XNCoords) else XNCoords()
        self.fields_busy = 0
        self.fields_total = 0
        self.res_current = XNResourceBundle(0, 0, 0)
        self.res_prod_per_hour = XNResourceBundle(0, 0, 0)
        self.energy = XNPlanetEnergyInfo()
        self.prod_powers = XNPlanetProductionPowers()
        self.ships = XNShipsBundle()
        self.buildings = XNBuildingsBundle()
        self.defense = XNDefenseBundle()
        self.moon = None  # planet may have moon
        self.is_moon = False  # or may be a moon itself
        # planet may have debris_field
        self.debris_field = XNDebrisField(0, 0)

    def __str__(self):
        if self.coords.target_name == '':
            self.coords.target_name = self.name
        return str(self.coords)

