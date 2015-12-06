# -*- coding: utf-8 -*-
import datetime
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
            type_str = ' (field) '
        elif self.target_type == self.TYPE_MOON:
            type_str = ' (moon) '
        elif self.target_type == self.TYPE_WARBASE:
            type_str = ' (base) '
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
        # interplanetary rocket is also a ship, a fast one
        self.mpr = 0

    def __len__(self):
        """
        :return total ships count in bundle
        """
        total = self.mt + self.bt + self.li + self.ti + self.crus + self.link \
            + self.col + self.rab + self.spy + self.bomber + self.ss + self.unik \
            + self.zs + self.lk + self.warbase \
            + self.f_ceptor + self.f_corsair + self.f_corvett + self.f_dread \
            + self.mpr
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
        ret += sa(self.mpr, 'MPR')
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
                       'owndestroy', 'ownhold', 'ownbase',
                       # enemy/hostile missions
                       'attack', 'espionage', 'missile', 'destroy', 'federation']

    def __init__(self):
        self.ships = XNShipsBundle()
        self.res = XNResourceBundle()
        self.src = XNCoords()
        self.dst = XNCoords()
        self.mission = None
        self.direction = ''
        self.arrive_datetime = datetime.datetime(datetime.MINYEAR, month=1, day=1, hour=0,
                                                 minute=0, second=0, microsecond=0, tzinfo=None)

    @staticmethod
    def is_hostile_mission(mission_str):
        if mission_str in ['attack', 'espionage', 'missile', 'destroy', 'federation']:
            return True
        return False

    def __str__(self):
        s = '{0} {1} -> {2} ({3}) {4}'.format(
            self.mission, str(self.src), str(self.dst), str(self.ships), str(self.res))
        if self.direction == 'return':
            s += ' return'
        s += (' @ ' + str(self.arrive_datetime))
        return s

    def remaining_time_secs(self, diff_with_server_time_secs=0) -> int:
        """
        Calculates the time flight has until arrival, in seconds
        :param diff_with_server_time_secs difference between local time and server time,
               in seconds, added to resulting return value
        :return None on error (self.arrive_datetime is None), or remaining time in seconds
        """
        if self.arrive_datetime is None:
            return None
        our_time = datetime.datetime.today()
        td = self.arrive_datetime - our_time
        seconds_left = int(td.total_seconds())
        seconds_left += diff_with_server_time_secs
        return seconds_left


class XNFraction:
    def __init__(self, name=None, race_id=None):
        self.name = ''
        if name is not None:
            self.name = name
        self.race_id = 0
        if race_id is not None:
            self.race_id = race_id
        self.ico_name = 'race{0}.gif'.format(self.race_id)


def fraction_from_name(name: str) -> XNFraction:
    if name == 'Конфедерация':
        ret = XNFraction(name, 1)
        return ret
    elif name == 'Бионики':
        ret = XNFraction(name, 2)
        return ret
    elif name == 'Сайлоны':
        ret = XNFraction(name, 3)
        return ret
    elif name == 'Древние':
        ret = XNFraction(name, 4)
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

    def __str__(self):
        ret = ''
        if self.met_factory > 0:
            ret += 'MetF: {0} '.format(self.met_factory)
        if self.cry_factory > 0:
            ret += 'CryF: {0} '.format(self.cry_factory)
        if self.deit_factory > 0:
            ret += 'DeitF: {0} '.format(self.deit_factory)
        if self.solar_station > 0:
            ret += 'Solar: {0} '.format(self.solar_station)
        if self.nuclear_station > 0:
            ret += 'Nuclear: {0} '.format(self.nuclear_station)
        if self.robotics_factory > 0:
            ret += 'RF: {0} '.format(self.robotics_factory)
        if self.nanites_factory > 0:
            ret += 'Nanites: {0} '.format(self.nanites_factory)
        if self.shipyard > 0:
            ret += 'ShipY: {0} '.format(self.shipyard)
        if self.met_silo > 0:
            ret += 'MetS: {0} '.format(self.met_silo)
        if self.cry_silo > 0:
            ret += 'CryS: {0} '.format(self.cry_silo)
        if self.deit_silo > 0:
            ret += 'DeitS: {0} '.format(self.deit_silo)
        if self.lab > 0:
            ret += 'Lab: {0} '.format(self.lab)
        if self.terraformer > 0:
            ret += 'TerraF: {0} '.format(self.terraformer)
        if self.alliance_silo > 0:
            ret += 'AllianceS: {0} '.format(self.alliance_silo)
        if self.rocket_silo > 0:
            ret += 'RocketS: {0} '.format(self.rocket_silo)
        if self.lunar_base > 0:
            ret += 'Lunar Base: {0} '.format(self.lunar_base)
        if self.lunar_phalanx > 0:
            ret += 'Phalanx: {0} '.format(self.lunar_phalanx)
        if self.gates > 0:
            ret += 'Gates: {0} '.format(self.gates)
        return ret.strip()


class XNDefenseBundle:
    """
    holds all info about planet's defenses count
    """
    def __init__(self):
        self.ru = 0
        self.ll = 0
        self.tl = 0
        self.gauss = 0
        self.ion = 0
        self.plasma = 0
        self.small_dome = 0
        self.big_dome = 0
        self.defender_rocket = 0
        self.attack_rocket = 0

    def __str__(self):
        ret = ''
        if self.ru > 0:
            ret += 'RU: {0} '.format(self.ru)
        if self.ll > 0:
            ret += 'LL: {0} '.format(self.ll)
        if self.tl > 0:
            ret += 'TL: {0} '.format(self.tl)
        if self.gauss > 0:
            ret += 'GAUSS: {0} '.format(self.gauss)
        if self.ion > 0:
            ret += 'ION: {0} '.format(self.ion)
        if self.plasma > 0:
            ret += 'PLASMA: {0} '.format(self.plasma)
        if self.small_dome > 0:
            ret += 'MSK: {0} '.format(self.small_dome)
        if self.big_dome > 0:
            ret += 'BSK: {0} '.format(self.big_dome)
        if self.defender_rocket > 0:
            ret += 'Defender Rocket: {0} '.format(self.defender_rocket)
        if self.attack_rocket > 0:
            ret += 'MPR: {0} '.format(self.attack_rocket)
        return ret.strip()


class XNPlanetProductionPowers:
    """
    Acts like a sctructure to hold values for individual
    production power settings (levels)
    """
    def __init__(self):
        self.met = 0
        self.cry = 0
        self.deit = 0
        self.solar = 0
        self.nuclear = 0
        self.ss = 0


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


class XNPlanetBuildingItem:
    """
    Some building that can be built on the planet
    or is in progress of building on the planet
    """
    def __init__(self):
        self.position = 0  # position in a queue
        self.gid = 0  # building item type ID
        self.name = ''
        self.level = 0
        self.quantity = 0  # for shipyard building item
        self.seconds_for_item = 0  # for shipyard item
        self.dt_end = None  # completion datetime, will hold a datetime object
        self.seconds_left = -1  # seconds left for this building to complete
        self.seconds_total = -1  # total seconds to build this item (-1 if building is not available)
        self.remove_from_queue_link = None  # url to delete building from queue
        # building price (for 1 item)
        self.cost_met = 0
        self.cost_cry = 0
        self.cost_deit = 0
        self.cost_energy = 0
        # item flags
        self.is_shipyard_item = False
        self.is_research_item = False

    def __str__(self):
        end_str = 'None'
        if self.dt_end is not None:
            dt_end = self.dt_end
            end_str = '{0:02}.{1:02}.{2:04} {3:02}:{4:02}:{5:02}'.format(
                dt_end.day, dt_end.month, dt_end.year,
                dt_end.hour, dt_end.minute, dt_end.second)
        secs_str = ''
        if self.seconds_total >= 0:
            secs_str = ' ('
            if self.seconds_left >= 0:
                secs_str += '{0} left, '.format(self.seconds_left)
            secs_str += '{0} total secs)'.format(self.seconds_total)
        rl = ''
        if self.remove_from_queue_link is not None:
            rl = ', remove_link = [{0}]'.format(self.remove_from_queue_link)
        lv_str = ''
        if self.is_shipyard_item:
            lv_str = '{0} pcs.'.format(self.quantity)
        else:
            lv_str = 'lv.{0}'.format(self.level)
        price_str = ''
        if (self.cost_met > 0) or (self.cost_cry > 0) or (self.cost_deit > 0) or (self.cost_energy > 0):
            price_str = ' (Price:'
            if self.cost_met > 0:
                price_str += ' {0} met'.format(self.cost_met)
            if self.cost_cry > 0:
                price_str += ' {0} cry'.format(self.cost_cry)
            if self.cost_deit > 0:
                price_str += ' {0} deit'.format(self.cost_deit)
            if self.cost_energy > 0:
                price_str += ' {0} energy'.format(self.cost_energy)
            price_str += ')'
        s = '{0}: {1} {2}, end: {3}{4}{5}{6}'.format(self.position, self.name, lv_str,
                                                     end_str, secs_str, rl, price_str)
        return s

    def set_end_time(self, dt: datetime.datetime):
        self.dt_end = dt
        self.calc_seconds_left()

    def calc_seconds_left(self):
        if not isinstance(self.dt_end, datetime.datetime):
            self.seconds_left = -1
            return
        dt_now = datetime.datetime.now()
        td = self.dt_end - dt_now
        self.seconds_left = int(td.total_seconds())

    def is_in_progress(self):
        if (self.seconds_left > 0) and (self.dt_end is not None):
            return True
        return False


class XNPlanet:
    """
    Main planet model, holding all information
    """
    def __init__(self, name=None, coords=None, planet_id=0):
        self.planet_id = planet_id
        self.name = ''
        if name is not None:
            self.name = name
        self.pic_url = ''
        self.coords = XNCoords()
        if isinstance(coords, XNCoords):
            self.coords = coords
        self.fields_busy = 0
        self.fields_total = 0
        self.res_current = XNResourceBundle(0, 0, 0)
        self.res_per_hour = XNResourceBundle(0, 0, 0)
        self.energy = XNPlanetEnergyInfo()
        self.prod_powers = XNPlanetProductionPowers()
        self.ships = XNShipsBundle()
        self.buildings = XNBuildingsBundle()  # buildings levels, from Imperium
        self.buildings_items = []  # list of XNPlanetBuildingItem, buildings available to build and in progress
        self.shipyard_tems = []  # list of XNPlanetBuildingItem, ships available to build
        self.shipyard_progress_items = []  # list of XNPlanetBuildingItem, ships in progress
        self.research_items = []  # list of XNPlanetBuildingItem, researches available to build and in progress
        self.defense = XNDefenseBundle()
        self.moon = None  # planet may have moon
        self.is_moon = False  # or may be a moon itself
        self.is_base = False
        # planet may have debris_field
        self.debris_field = XNDebrisField(0, 0)
        self.is_current = False  # used by UI to highlight current planet, that's all
        self.has_build_in_progress = False

    def __str__(self):
        if self.coords.target_name == '':
            self.coords.target_name = self.name
        add_type = ''
        if self.is_moon:
            add_type = ' (moon)'
        if self.is_base:
            add_type = ' (base)'
        return str(self.coords) + add_type

    def detect_type_by_pic_url(self):
        self.is_base = False
        if self.pic_url is not None:
            m = re.search(r's_baseplanet01.jpg$', self.pic_url)
            if m is not None:
                self.is_base = True
                return
            m = re.search(r'mond.jpg$', self.pic_url)
            if m is not None:
                self.is_moon = True
                return

    def add_build_in_progress(self, ba: XNPlanetBuildingItem):
        if len(self.buildings_items) < 1:
            return False
        for bi in self.buildings_items:
            if bi.name == ba.name:
                bi.position = ba.position
                bi.dt_end = ba.dt_end
                bi.seconds_left = ba.seconds_left
                bi.remove_from_queue_link = ba.remove_from_queue_link
                self.has_build_in_progress = True
                return True
        return False

    def check_builds_in_progress(self):
        self.has_build_in_progress = False  # assume no builds in progress
        for bi in self.buildings_items:
            if bi.is_in_progress():
                self.has_build_in_progress = True
                return

    # TODO: change this from item_name to item_ID when we will load item IDs
    def is_build_in_progress(self, build_name: str):
        if len(self.buildings_items) < 1:
            return False
        for b in self.buildings_items:
            if (b.name == build_name) and (b.is_in_progress()):
                return True
        return False

    def lab_level(self):
        return self.buildings.lab
