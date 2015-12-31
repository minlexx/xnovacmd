# -*- coding: utf-8 -*-
import datetime
import re

from PyQt5.QtCore import pyqtSignal, QThread, QMutex

from .xn_data import XNAccountInfo
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload
from .xn_data import XNCoords, XNFlight, XNPlanet, XNPlanetBuildingItem
from .xn_techtree import XNTechTree_instance
from .xn_parser_overview import OverviewParser
from .xn_parser_userinfo import UserInfoParser
from .xn_parser_curplanet import CurPlanetParser
from .xn_parser_imperium import ImperiumParser
from .xn_parser_galaxy import GalaxyParser
from .xn_parser_planet_buildings import PlanetBuildingsAvailParser, PlanetBuildingsProgressParser
from .xn_parser_planet_energy import PlanetEnergyResParser
from .xn_parser_shipyard import ShipyardShipsAvailParser, ShipyardBuildsInProgressParser
from .xn_parser_research import ResearchAvailParser
from .xn_parser_techtree import TechtreeParser
from .xn_parser_fleet import FleetsMaxParser
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# created by main window to keep info about world updated
class XNovaWorld(QThread):
    SIGNAL_QUIT = 0
    SIGNAL_RELOAD_PAGE = 1      # args: page_name
    SIGNAL_RENAME_PLANET = 2    # args: planet_id, new_name
    SIGNAL_RELOAD_PLANET = 3    # args: planet_id
    SIGNAL_BUILD_ITEM = 4       # args: bitem: XNPlanetBuildingItem, quantity, planet_id
    SIGNAL_BUILD_CANCEL = 5     # args: bitem: XNPlanetBuildingItem, planet_id
    SIGNAL_BUILD_DISMANTLE = 6  # args: bitem: XNPlanetBuildingItem, planet_id
    # testing signals ... ?
    SIGNAL_TEST_PARSE_GALAXY = 100   # args: galaxy, system

    # signal is emitted to report full world refresh progress
    # str is a comment what is loading now, int is a progress percent [0..100]
    world_load_progress = pyqtSignal(str, int)
    # signal to be emitted when initial world loading is complete
    world_load_complete = pyqtSignal()
    # emitted when fleet has arrived at its destination
    flight_arrived = pyqtSignal(XNFlight)
    # emitted when building has completed on planet
    build_complete = pyqtSignal(XNPlanet, XNPlanetBuildingItem)
    # emitted when overview was reloaded (but not during world refresh)
    loaded_overview = pyqtSignal()
    # emitted when imperium was reloaded (but not during world refresh)
    loaded_imperium = pyqtSignal()
    # emitted when full planet was refreshed (but not during world refresh)
    loaded_planet = pyqtSignal(int)   # planet_id
    # emitted when any network request has started (but not during world refresh)
    net_request_started = pyqtSignal()
    # emitted when network request has finished (but not during world refresh)
    net_request_finished = pyqtSignal()

    def __init__(self, parent=None):
        super(XNovaWorld, self).__init__(parent)
        self._world_is_loading = False  # true is _full_refresh() is running (world is loading)
        # helpers
        self._page_dnl_times = dict()   # last time when a page was downloaded
        self._page_cache = XNovaPageCache()
        self._page_cache.save_load_encoding = 'UTF-8'
        self._page_downloader = XNovaPageDownload()
        # parsers
        self._parser_overview = OverviewParser()
        self._parser_userinfo = UserInfoParser()
        self._parser_curplanet = CurPlanetParser()
        self._parser_imperium = ImperiumParser()
        self._parser_planet_buildings_avail = PlanetBuildingsAvailParser()
        self._parser_planet_buildings_progress = PlanetBuildingsProgressParser()
        self._parser_planet_energy = PlanetEnergyResParser()
        self._parser_shipyard_ships_avail = ShipyardShipsAvailParser()
        self._parser_shipyard_progress = ShipyardBuildsInProgressParser()
        self._parser_researches_avail = ResearchAvailParser()
        self._parser_techtree = TechtreeParser()
        self._parser_fleetmax = FleetsMaxParser()
        # world/user info
        self._server_time = datetime.datetime.today()  # server time at last overview update
        # all we need to calc server time is actually time diff with our time:
        self._diff_with_server_time_secs = 0  # calculated as: our_time - server_time
        self._vacation_mode = False
        self._account = XNAccountInfo()
        self._flights = []
        self._cur_planet_id = 0
        self._cur_planet_name = ''
        self._cur_planet_coords = XNCoords(0, 0, 0)
        self._planets = []  # list of XNPlanet
        self._techtree = XNTechTree_instance()
        self._new_messages_count = 0
        self._server_online_players = 0
        self._max_fleets_count = 0
        self._cur_fleets_count = 0
        # internal need
        self._net_errors_count = 0
        self._net_errors_list = []
        self._NET_ERRORS_MAX = 10
        self._mutex = QMutex(QMutex.Recursive)
        self._signal_kwargs = dict()
        # thread identifiers, collected here mainly for debugging purposes
        # those are actually:
        # - DWORD GetCurrentThreadId() in Windows
        # - pthread_t pthread_current() in Linux
        self._maintid = 0
        self._worldtid = 0
        # settings
        self._overview_update_interval = 120  # seconds
        self._galaxy_cache_lifetime = 60  # seconds
        self._planet_buildings_cache_lifetime = 60  # seconds
        self._planet_shipyard_cache_lifetime = 60  # seconds
        self._planet_research_cache_lifetime = 60  # seconds

    def initialize(self, cookies_dict: dict):
        """
        Called from main window just before thread starts
        :param cookies_dict: dictionary with cookies for networking
        :return: None
        """
        # load cached pages
        self._page_cache.load_from_disk_cache(clean=True)
        # init network session with cookies for authorization
        self._page_downloader.set_cookies_from_dict(cookies_dict, do_save=True)
        # misc
        self._maintid = self._gettid()
        logger.debug('initialized from tid={0}'.format(self._maintid))

    def reload_config(self):
        """
        Reloads network config in page downloader and if network settings
        change, creates a new HTTP session, resulting in fact in new connection!
        :return:
        """
        prev_proxy = self._page_downloader.proxy
        self._page_downloader.read_config()
        new_proxy = self._page_downloader.proxy
        # reconstruct session only if network settings were changed
        if new_proxy != prev_proxy:
            logger.debug('reload_config(): net proxy changed, recreating '
                         'HTTP session ({0} != {1})'.format(prev_proxy, new_proxy))
            self._page_downloader.construct_session()
        self._page_downloader.apply_useragent()

    def lock(self, timeout_ms=None, raise_on_timeout=False):
        """
        Locks thread mutex to protect thread state vars
        :param timeout_ms: timeout ms to wait, default infinite
        :param raise_on_timeout: if true, OSError/TimeoutError will be thrown on timeout
        :return: True if all OK, False if not locked
        """
        if timeout_ms is None:
            self._mutex.lock()
            return True
        ret = self._mutex.tryLock(timeout_ms)
        if ret:
            return True
        else:
            if raise_on_timeout:
                # python >= 3.3 has TimeoutError, others only have OSError
                # raise TimeoutError('XNovaWorld: failed to get mutex lock, timeout was {0} ms.'.format(timeout_ms))
                raise OSError('XNovaWorld: failed to get mutex lock, timeout was {0} ms.'.format(timeout_ms))
            return False

    def unlock(self):
        self._mutex.unlock()

    def signal_quit(self):
        self.quit()

    def signal(self, signal_code=0, **kwargs):
        # logger.debug('signal: kwargs = {0}'.format(str(kwargs)))
        # ^^: args = (), kwargs = {'page': 'overview'}
        self.lock()
        if kwargs is not None:
            self._signal_kwargs = kwargs
        self.unlock()
        self.exit(signal_code)  # QEventLoop.exit(code) makes thread's event loop to exit with code

    ###################################
    # Getters
    ###################################

    def get_account_info(self) -> XNAccountInfo:
        self.lock()
        ret = self._account
        self.unlock()
        return ret

    def set_login_email(self, email: str):
        self.lock()
        self._account.email = email
        self.unlock()

    def get_flights(self) -> list:
        ret = []
        # try to lock with 0ms wait, if fails, return empty list
        if self.lock(0):
            ret = self._flights
            self.unlock()
        return ret

    def get_flight_remaining_time_secs(self, fl: XNFlight) -> int:
        """
        Calculates flight remaining time, adjusting time by difference
        between our time and server
        :param fl: flight
        :return: remaining time in seconds, or -1 on error
        """
        self.lock()
        dsts = self._diff_with_server_time_secs
        self.unlock()
        #
        secs_left = -1
        if fl.seconds_left != -1:
            secs_left = fl.seconds_left + dsts
        #
        return secs_left

    def get_current_server_time(self) -> datetime.datetime:
        """
        Calculates current server time (at this moment), using
        previously calculated time diff (checked at last update)
        :return:
        """
        self.lock()
        dt_now = datetime.datetime.today()
        dt_delta = datetime.timedelta(seconds=self._diff_with_server_time_secs)
        dt_server = dt_now - dt_delta
        self.unlock()
        return dt_server

    def get_planets(self) -> list:
        ret = []
        # try to lock with 0ms wait, if fails, return empty list
        if self.lock(0):
            ret = self._planets
            self.unlock()
        return ret

    def get_planet(self, planet_id) -> XNPlanet:
        pls = self.get_planets()
        for pl in pls:
            if pl.planet_id == planet_id:
                return pl
        logger.warn('Could not find planet with id: {0}'.format(planet_id))
        return None

    def get_new_messages_count(self) -> int:
        self.lock()
        ret = self._new_messages_count
        self.unlock()
        return ret

    def get_online_players(self):
        self.lock()
        ret = self._server_online_players
        self.unlock()
        return ret

    def get_fleets_count(self) -> list:
        """
        Get current/maximum fleets count
        :return: list[0] = cur, list[1] = max
        """
        ret = [0, 0]
        self.lock()
        ret[0] = self._cur_fleets_count
        ret[1] = self._max_fleets_count
        self.unlock()
        return ret

    ################################################################################
    # this should re-calculate all user's object statuses
    # like fleets in flight, buildings in construction,
    # reserches in progress, etc, ...
    def world_tick(self):
        # This is called from GUI thread =(
        self.lock()
        self._world_tick_flights()
        self._world_tick_planets()
        self._maybe_refresh_overview()
        self.unlock()

    # just counts remaining time for flights,
    # removes finished flights and emits signal
    # 'flight_arrived' for every finished flight
    def _world_tick_flights(self):
        # logger.debug('tick: server time diff: {0}'.format(self._diff_with_server_time_secs))  # 0:00:16.390197
        # iterate
        finished_flights_count = 0
        for fl in self._flights:
            if fl.seconds_left == -1:
                raise ValueError('Flight seconds left is None: {0}'.format(str(fl)))
            fl.seconds_left -= 1
            if fl.seconds_left <= 0:
                fl.seconds_left = 0
                logger.debug('==== Flight considered complete: {0}'.format(str(fl)))
                # logger.debug('==== additional debug info:')
                # logger.debug('====  - diff with server time: {0}'.format(self._diff_with_server_time_secs))
                # logger.debug('====  - current time: {0}'.format(datetime.datetime.today()))
                # logger.debug('====  - current server time: {0}'.format(self.get_current_server_time()))
                finished_flights_count += 1
        if finished_flights_count > 0:
            # logger.debug('==== Removing total {0} arrived flights'.format(finished_flights_count))
            for irow in range(finished_flights_count):
                try:
                    # finished_flight = self._flights[irow]
                    # item-to-delete from python list will always have index 0?
                    # because we need to delete the first item every time
                    finished_flight = self._flights[0]
                    # del self._flights[0]
                    self._flights.remove(finished_flight)
                    # emit signal
                    self.flight_arrived.emit(finished_flight)
                except IndexError:
                    # should never happen
                    logger.error('IndexError while clearing finished flights: ')
                    logger.error(' deleting index {0}, while total list len: {1}'.format(
                        0, len(self._flights)))
        # end _world_tick_flights()

    def _world_tick_planets(self):
        """
        This should do the following:
        - increase planet resources every second
        - move planet buildings progress
        :return: None
        """
        for planet in self._planets:
            # tick resources
            # calc resource speed per second
            mps = planet.res_per_hour.met / 3600
            cps = planet.res_per_hour.cry / 3600
            dps = planet.res_per_hour.deit / 3600
            # add resource per second
            planet.res_current.met += mps
            planet.res_current.cry += cps
            planet.res_current.deit += dps
            # tick buildings in progress
            num_completed = 0
            for bitem in planet.buildings_items:
                if bitem.is_in_progress():
                    bitem.seconds_left -= 1
                    if bitem.seconds_left <= 0:
                        bitem.seconds_left = -1
                        bitem.dt_end = None  # mark as stopped
                        bitem.level += 1  # level increased
                        num_completed += 1
                        self.build_complete.emit(planet, bitem)
            # tick shipyard builds in progress
            todel_list = []
            for bitem in planet.shipyard_progress_items:
                bitem.seconds_left -= 1
                if bitem.seconds_left <= 0:
                    todel_list.append(bitem)
                break  # only one (first) item is IN PROGRESS, others WAIT !!!
            if len(todel_list) > 0:
                for bitem in todel_list:
                    planet.shipyard_progress_items.remove(bitem)
                    self.build_complete.emit(planet, bitem)
            # tick planet researches
            num_completed = 0
            for bitem in planet.research_items:
                if bitem.is_in_progress():
                    bitem.seconds_left -= 1
                    if bitem.seconds_left <= 0:
                        bitem.seconds_left = -1
                        bitem.dt_end = None  # mark as stopped
                        bitem.level += 1
                        num_completed += 1
                        self.build_complete.emit(planet, bitem)
            # tick planet research_fleet
            num_completed = 0
            for bitem in planet.researchfleet_items:
                if bitem.is_in_progress():
                    bitem.seconds_left -= 1
                    if bitem.seconds_left <= 0:
                        bitem.seconds_left = -1
                        bitem.dt_end = None  # mark as stopped
                        bitem.level += 1
                        num_completed += 1
                        self.build_complete.emit(planet, bitem)
        # end _world_tick_planets()

    # can trigger signal to refresh overview page every
    # 'self._overview_update_interval' seconds
    def _maybe_refresh_overview(self):
        if 'overview' in self._page_dnl_times:
            dt_last = self._page_dnl_times['overview']
            dt_now = datetime.datetime.today()
            dt_diff = dt_now - dt_last
            secs_ago = int(dt_diff.total_seconds())
            if secs_ago >= self._overview_update_interval:
                logger.debug('_maybe_refresh_overview() trigger update: {0} secs ago.'.format(secs_ago))
                self.signal(self.SIGNAL_RELOAD_PAGE, page_name='overview')

    ################################################################################

    def on_page_downloaded(self, page_name: str):
        logger.debug('on_page_downloaded( "{0}" ) tid={1}'.format(page_name, self._gettid_s()))
        # cache has the page inside before the signal was emitted!
        # we can get page content from cache
        page_content = self._page_cache.get_page(page_name)
        if page_content is None:
            raise ValueError('This should not ever happen!')
        # get current date/time
        dt_now = datetime.datetime.today()
        self._page_dnl_times[page_name] = dt_now  # save last download time for page
        # dispatch parser and merge data
        if page_name == 'overview':
            self._parser_overview.clear()
            self._parser_overview.account = self._account  # store previous info
            self._parser_overview.parse_page_content(page_content)
            self._account = self._parser_overview.account  # get new info
            self._flights = self._parser_overview.flights
            # get server time also calculate time diff
            self._server_time = self._parser_overview.server_time
            dt_diff = dt_now - self._server_time
            self._diff_with_server_time_secs = int(dt_diff.total_seconds())
            self._new_messages_count = self._parser_overview.new_messages_count
            self._vacation_mode = self._parser_overview.in_RO
            self._server_online_players = self._parser_overview.online_players
            # run also cur planet parser on the same content
            self._parser_curplanet.parse_page_content(page_content)
            self._cur_planet_id = self._parser_curplanet.cur_planet_id
            self._cur_planet_name = self._parser_curplanet.cur_planet_name
            self._cur_planet_coords = self._parser_curplanet.cur_planet_coords
            self._internal_set_current_planet()  # it may have changed
            # emit signal that we've loaded overview, but not during world update
            if not self._world_is_loading:
                self.loaded_overview.emit()
        elif page_name == 'self_user_info':
            self._parser_userinfo.parse_page_content(page_content)
            self._account.scores.buildings = self._parser_userinfo.buildings
            self._account.scores.buildings_rank = self._parser_userinfo.buildings_rank
            self._account.scores.fleet = self._parser_userinfo.fleet
            self._account.scores.fleet_rank = self._parser_userinfo.fleet_rank
            self._account.scores.defense = self._parser_userinfo.defense
            self._account.scores.defense_rank = self._parser_userinfo.defense_rank
            self._account.scores.science = self._parser_userinfo.science
            self._account.scores.science_rank = self._parser_userinfo.science_rank
            self._account.scores.total = self._parser_userinfo.total
            self._account.scores.rank = self._parser_userinfo.rank
            self._account.main_planet_name = self._parser_userinfo.main_planet_name
            self._account.main_planet_coords = self._parser_userinfo.main_planet_coords
            self._account.alliance_name = self._parser_userinfo.alliance_name
        elif page_name == 'imperium':
            self._parser_imperium.clear()
            self._parser_imperium.parse_page_content(page_content)
            self._planets = self._parser_imperium.planets
            # since we've overwritten the whole planets array, we need to
            # write current planet into it again
            self._internal_set_current_planet()
            # emit signal that we've loaded overview, but not during world update
            if not self._world_is_loading:
                self.loaded_imperium.emit()
        elif page_name == 'techtree':
            self._parser_techtree.clear()
            self._parser_techtree.parse_page_content(page_content)
            # store techtree, if there is successful parse of anything
            if len(self._parser_techtree.techtree) > 0:
                self._techtree.init_techtree(self._parser_techtree.techtree)
        elif page_name == 'fleet':
            self._parser_fleetmax.clear()
            self._parser_fleetmax.parse_page_content(page_content)
            self._cur_fleets_count = self._parser_fleetmax.fleets_cur
            self._max_fleets_count = self._parser_fleetmax.fleets_max
        elif page_name.startswith('buildings_'):
            try:
                m = re.match(r'buildings_(\d+)', page_name)
                planet_id = int(m.group(1))
                planet = self.get_planet(planet_id)
                # get available buildings to build
                self._parser_planet_buildings_avail.clear()
                self._parser_planet_buildings_avail.parse_page_content(page_content)
                # get buildings in progress on the same page
                self._parser_planet_buildings_progress.clear()
                self._parser_planet_buildings_progress.parse_page_content(page_content)
                # get planet energy info, res cur/max/prod
                self._parser_planet_energy.clear()
                self._parser_planet_energy.parse_page_content(page_content)
                if planet is not None:
                    planet.buildings_items = self._parser_planet_buildings_avail.builds_avail
                    num_added = len(self._parser_planet_buildings_progress.builds_in_progress)
                    if num_added > 0:
                        for bip in self._parser_planet_buildings_progress.builds_in_progress:
                            planet.add_build_in_progress(bip)
                        logger.debug('Buildings queue for planet {0}: added {1}'.format(planet.name, num_added))
                    # save planet energy info, do not overwite with zeros
                    if self._parser_planet_energy.energy_left > 0:
                        planet.energy.energy_left = self._parser_planet_energy.energy_left
                    if self._parser_planet_energy.energy_total > 0:
                        planet.energy.energy_total = self._parser_planet_energy.energy_total
                    # save planet resource info
                    if len(self._parser_planet_energy.res_current) > 0:
                        planet.res_current = self._parser_planet_energy.res_current
                    if len(self._parser_planet_energy.res_max_silos) > 0:
                        planet.res_max_silos = self._parser_planet_energy.res_max_silos
                    if len(self._parser_planet_energy.res_per_hour) > 0:
                        planet.res_per_hour = self._parser_planet_energy.res_per_hour
            except ValueError:  # failed to convert to int
                logger.exception('Failed to convert planet_id to int, page_name=[{0}]'.format(page_name))
            except AttributeError:  # no match
                logger.exception('Invalid format for page_name=[{0}], expected buildings_123456'.format(page_name))
        elif page_name.startswith('shipyard_'):
            try:
                m = re.match(r'shipyard_(\d+)', page_name)
                planet_id = int(m.group(1))
                planet = self.get_planet(planet_id)
                # go parse
                self._parser_shipyard_ships_avail.clear()
                self._parser_shipyard_ships_avail.parse_page_content(page_content)
                self._parser_shipyard_progress.clear()
                self._parser_shipyard_progress.server_time = self._server_time
                self._parser_shipyard_progress.parse_page_content(page_content)
                # get planet energy info
                self._parser_planet_energy.clear()
                self._parser_planet_energy.parse_page_content(page_content)
                if planet is not None:
                    planet.shipyard_tems = self._parser_shipyard_ships_avail.ships_avail
                    planet.shipyard_progress_items = self._parser_shipyard_progress.shipyard_progress_items
                    if len(self._parser_shipyard_progress.shipyard_progress_items) > 0:
                        logger.debug('planet [{0}] has {0} items in shipyard queue'.format(
                            planet.name, len(self._parser_shipyard_progress.shipyard_progress_items)))
                    # save planet energy info, but do not overwrite with zeros
                    # if there is no shipyard @ planet, no energy info will be on the page =(
                    if self._parser_planet_energy.energy_left > 0:
                        planet.energy.energy_left = self._parser_planet_energy.energy_left
                    if self._parser_planet_energy.energy_total > 0:
                        planet.energy.energy_total = self._parser_planet_energy.energy_total
                    # save planet resource info
                    if len(self._parser_planet_energy.res_current) > 0:
                        planet.res_current = self._parser_planet_energy.res_current
                    if len(self._parser_planet_energy.res_max_silos) > 0:
                        planet.res_max_silos = self._parser_planet_energy.res_max_silos
                    if len(self._parser_planet_energy.res_per_hour) > 0:
                        planet.res_per_hour = self._parser_planet_energy.res_per_hour
            except AttributeError:  # no match
                logger.exception('Invalid format for page_name=[{0}], expected shipyard_123456'.format(page_name))
            except ValueError:  # failed to convert to int
                logger.exception('Failed to convert planet_id to int, page_name=[{0}]'.format(page_name))
        elif page_name.startswith('defense_'):
            try:
                m = re.match(r'defense_(\d+)', page_name)
                planet_id = int(m.group(1))
                planet = self.get_planet(planet_id)
                # go parse
                self._parser_shipyard_ships_avail.clear()
                self._parser_shipyard_ships_avail.parse_page_content(page_content)
                self._parser_shipyard_progress.clear()
                self._parser_shipyard_progress.server_time = self._server_time
                self._parser_shipyard_progress.parse_page_content(page_content)
                # get planet energy info
                self._parser_planet_energy.clear()
                self._parser_planet_energy.parse_page_content(page_content)
                if planet is not None:
                    # shipyard parser ships_avail can also parse planet defenses avail
                    planet.defense_items = self._parser_shipyard_ships_avail.ships_avail
                    # even in defense page, ships build queue is the same as in shipyard page
                    planet.shipyard_progress_items = self._parser_shipyard_progress.shipyard_progress_items
                    if len(self._parser_shipyard_progress.shipyard_progress_items) > 0:
                        logger.debug('planet [{0}] has {0} items in shipyard queue'.format(
                            planet.name, len(self._parser_shipyard_progress.shipyard_progress_items)))
                    # save planet energy info, but do not overwrite with zeros
                    # if there is no shipyard @ planet, no energy info will be on the page =(
                    if self._parser_planet_energy.energy_left > 0:
                        planet.energy.energy_left = self._parser_planet_energy.energy_left
                    if self._parser_planet_energy.energy_total > 0:
                        planet.energy.energy_total = self._parser_planet_energy.energy_total
                    # save planet resource info
                    if len(self._parser_planet_energy.res_current) > 0:
                        planet.res_current = self._parser_planet_energy.res_current
                    if len(self._parser_planet_energy.res_max_silos) > 0:
                        planet.res_max_silos = self._parser_planet_energy.res_max_silos
                    if len(self._parser_planet_energy.res_per_hour) > 0:
                        planet.res_per_hour = self._parser_planet_energy.res_per_hour
            except AttributeError:  # no match
                logger.exception('Invalid format for page_name=[{0}], expected defense_123456'.format(page_name))
            except ValueError:  # failed to convert to int
                logger.exception('Failed to convert planet_id to int, page_name=[{0}]'.format(page_name))
        elif page_name.startswith('research_'):
            try:
                m = re.match(r'research_(\d+)', page_name)
                planet_id = int(m.group(1))
                planet = self.get_planet(planet_id)
                # go parse
                self._parser_researches_avail.clear()
                self._parser_researches_avail.server_time = self._server_time
                self._parser_researches_avail.set_parsing_research_fleet(False)
                self._parser_researches_avail.parse_page_content(page_content)
                # get planet energy info
                self._parser_planet_energy.clear()
                self._parser_planet_energy.parse_page_content(page_content)
                if planet is not None:
                    planet.research_items = self._parser_researches_avail.researches_avail
                    if len(self._parser_researches_avail.researches_avail) > 0:
                        logger.info('Planet {0} has {1} researches avail'.format(
                            planet.name, len(self._parser_researches_avail.researches_avail)))
                    # save planet energy info, but do not overwrite with zeros
                    # if there is no lab @ planet, no energy info will be on the page =(
                    if self._parser_planet_energy.energy_left > 0:
                        planet.energy.energy_left = self._parser_planet_energy.energy_left
                    if self._parser_planet_energy.energy_total > 0:
                        planet.energy.energy_total = self._parser_planet_energy.energy_total
                    # save planet resource info
                    if len(self._parser_planet_energy.res_current) > 0:
                        planet.res_current = self._parser_planet_energy.res_current
                    if len(self._parser_planet_energy.res_max_silos) > 0:
                        planet.res_max_silos = self._parser_planet_energy.res_max_silos
                    if len(self._parser_planet_energy.res_per_hour) > 0:
                        planet.res_per_hour = self._parser_planet_energy.res_per_hour
            except AttributeError:  # no match
                logger.exception('Invalid format for page_name=[{0}], '
                                 'expected research_123456'.format(page_name))
            except ValueError:  # failed to convert to int
                logger.exception('Failed to convert planet_id to int, '
                                 'page_name=[{0}]'.format(page_name))
        elif page_name.startswith('researchfleet_'):
            try:
                m = re.match(r'researchfleet_(\d+)', page_name)
                planet_id = int(m.group(1))
                planet = self.get_planet(planet_id)
                # go parse
                self._parser_researches_avail.clear()
                self._parser_researches_avail.server_time = self._server_time
                self._parser_researches_avail.set_parsing_research_fleet(True)
                self._parser_researches_avail.parse_page_content(page_content)
                # get planet energy info
                self._parser_planet_energy.clear()
                self._parser_planet_energy.parse_page_content(page_content)
                if planet is not None:
                    planet.researchfleet_items = self._parser_researches_avail.researches_avail
                    if len(self._parser_researches_avail.researches_avail) > 0:
                        logger.info('Planet {0} has {1} fleet researches avail'.format(
                            planet.name, len(self._parser_researches_avail.researches_avail)))
                    # save planet energy info, but do not overwrite with zeros
                    # if there is no lab @ planet, no energy info will be on the page =(
                    if self._parser_planet_energy.energy_left > 0:
                        planet.energy.energy_left = self._parser_planet_energy.energy_left
                    if self._parser_planet_energy.energy_total > 0:
                        planet.energy.energy_total = self._parser_planet_energy.energy_total
                    # save planet resource info
                    if len(self._parser_planet_energy.res_current) > 0:
                        planet.res_current = self._parser_planet_energy.res_current
                    if len(self._parser_planet_energy.res_max_silos) > 0:
                        planet.res_max_silos = self._parser_planet_energy.res_max_silos
                    if len(self._parser_planet_energy.res_per_hour) > 0:
                        planet.res_per_hour = self._parser_planet_energy.res_per_hour
            except AttributeError:  # no match
                logger.exception('Invalid format for page_name=[{0}], '
                                 'expected researchfleet_123456'.format(page_name))
            except ValueError:  # failed to convert to int
                logger.exception('Failed to convert planet_id to int, '
                                 'page_name=[{0}]'.format(page_name))
        else:
            logger.warn('on_page_downloaded(): Unhandled page name [{0}]. '
                        'This may be not a problem, but...'.format(page_name))

    def on_signal_reload_page(self):
        if 'page_name' in self._signal_kwargs:
            page_name = self._signal_kwargs['page_name']
            logger.debug('on_reload_page(): reloading {0}'.format(page_name))
            self.lock()
            self._get_page(page_name, max_cache_lifetime=1, force_download=True)
            self.unlock()

    def on_signal_rename_planet(self):
        if ('planet_id' in self._signal_kwargs) and ('new_name' in self._signal_kwargs):
            planet_id = int(self._signal_kwargs['planet_id'])
            new_name = self._signal_kwargs['new_name']
            # go go go
            logger.debug('renaming planet #{0} to [{1}]'.format(planet_id, new_name))
            self.lock()
            self._request_rename_planet(planet_id, new_name)
            # force imperium update to read new planet name
            self._get_page('imperium', 1, force_download=True)
            self.unlock()

    def on_signal_reload_planet(self):
        if 'planet_id' in self._signal_kwargs:
            planet_id = int(self._signal_kwargs['planet_id'])
            logger.debug('reloading planet #{0}'.format(planet_id))
            self.lock()
            self._download_planet(planet_id, delays_msec=250, force_download=True)
            self.unlock()
            logger.debug('reload planet #{0} done'.format(planet_id))

    def on_signal_test_parse_galaxy(self):
        if ('galaxy' in self._signal_kwargs) and ('system' in self._signal_kwargs):
            gal_no = self._signal_kwargs['galaxy']
            sys_no = self._signal_kwargs['system']
            logger.debug('downloading galaxy page {0},{1}'.format(gal_no, sys_no))
            page_content = self._download_galaxy_page(gal_no, sys_no, force_download=True)
            if page_content is not None:
                gp = GalaxyParser()
                gp.clear()
                gp.parse_page_content(page_content)
                if gp.script_body != '':
                    gp.unscramble_galaxy_script()
                    logger.debug(gp.galaxy_rows)

    def on_signal_build_item(self):
        if ('bitem' in self._signal_kwargs) and ('planet_id' in self._signal_kwargs) \
                and ('quantity' in self._signal_kwargs):
            bitem = self._signal_kwargs['bitem']
            planet_id = int(self._signal_kwargs['planet_id'])
            quantity = int(self._signal_kwargs['quantity'])
            self.lock()
            self._request_build_item(planet_id, bitem, quantity)
            self.unlock()

    def on_signal_build_cancel(self):
        if ('bitem' in self._signal_kwargs) and ('planet_id' in self._signal_kwargs):
            bitem = self._signal_kwargs['bitem']
            planet_id = int(self._signal_kwargs['planet_id'])
            self.lock()
            self._request_build_cancel(planet_id, bitem)
            self.unlock()

    def on_signal_build_dismantle(self):
        if ('bitem' in self._signal_kwargs) and ('planet_id' in self._signal_kwargs):
            bitem = self._signal_kwargs['bitem']
            planet_id = int(self._signal_kwargs['planet_id'])
            self.lock()
            self._request_build_dismantle(planet_id, bitem)
            self.unlock()

    def _internal_set_current_planet(self):
        """
        Just updates internal planets array with information
        about which of them is current one
        :return: None
        """
        for pl in self._planets:
            if pl.planet_id == self._cur_planet_id:
                pl.is_current = True
            else:
                pl.is_current = False

    def _inc_network_errors(self):
        """
        Error handler, called when network error has occured,
        when page could not be downloaded. Raises RuntimeError when
        too many errors happened.
        :return:
        """
        # increase errors count
        self._net_errors_count += 1
        # store error text
        if self._page_downloader.error_str != '':
            self._net_errors_list.append(self._page_downloader.error_str)
        logger.error('net error happened: [{0}], total errors count: {1}'.format(
                self._page_downloader.error_str, self._net_errors_count))
        if self._net_errors_count > self._NET_ERRORS_MAX:
            raise RuntimeError('Too many network errors: {0}!'.format(self._net_errors_count))

    # internal helper, converts page identifier to url path
    def _page_name_to_url_path(self, page_name: str):
        urls_dict = dict()
        urls_dict['overview'] = '?set=overview'
        urls_dict['imperium'] = '?set=imperium'
        urls_dict['techtree'] = '?set=techtree'
        urls_dict['fleet'] = '?set=fleet'
        sub_url = None
        if page_name in urls_dict:
            return urls_dict[page_name]
        elif page_name == 'self_user_info':
            # special page case, dynamic URL, depends on user id
            #  http://uni4.xnova.su/?set=players&id=71995
            if self._account.id == 0:
                logger.warn('requested account info page, but account id is 0!')
                return None
            sub_url = '?set=players&id={0}'.format(self._account.id)
        else:
            logger.warn('unknown page name requested: {0}'.format(page_name))
        return sub_url

    def _get_page(self, page_name, max_cache_lifetime=None, force_download=False):
        """
        Gets page from cache or from server only by page name.
        Converts page_name to page URL, using _page_name_to_url_path().
        First tries to get cached page from cache using page_name as key.
        If there is no cached page there, or it is expired, downloads from network.
        Then calls self.on_page_downloaded() to automatically parse requested page.
        :param page_name: 'name' used as key in pages cache
        :param max_cache_lifetime: cache timeout
        :param force_download:
        :return: page contents as str, or None on error
        """
        page_url = self._page_name_to_url_path(page_name)
        if not page_url:
            logger.error('Failed to convert page_name=[{0}] to url!'.format(page_name))
            return None
        return self._get_page_url(page_name, page_url, max_cache_lifetime, force_download)

    def _get_page_url(self, page_name, page_url,
                      max_cache_lifetime=None,
                      force_download=False,
                      referer=None):
        """
        For internal needs, downloads url from server using HTTP GET.
        First tries to get cached page from cache using page_name as key.
        If there is no cached page there, or it is expired, downloads from network.
        Then calls self.on_page_downloaded() to automatically parse requested page.
        If force_download is True, max_cache_lifetime is ignored.
        (This method's return value is ignored for now)
        :param page_name: 'name' of page to use as key when stored to cache
        :param page_url: URL to download in HTTP GET request
        :param max_cache_lifetime:
        :param force_download:
        :param referer: set this to str value to force Referer header before request
        :return: page contents (str) or None on error
        """
        page_content = None
        if not force_download:
            # try to get cached page (default)
            page_content = self._page_cache.get_page(page_name, max_cache_lifetime)
            if page_content is not None:
                logger.debug('... got page "{0}" from cache! (lifetime < {1})'.format(
                        page_name, max_cache_lifetime))
        if page_content is None:
            # signal that we are starting network request
            if not self._world_is_loading:
                self.net_request_started.emit()
            # set referer, if set
            if referer is not None:
                self._page_downloader.set_referer(referer)
            # try to download, it not in cache
            page_content = self._page_downloader.download_url_path(page_url)
            # signal that we have finished network request
            if not self._world_is_loading:
                self.net_request_finished.emit()
            if page_content is not None:
                self._page_cache.set_page(page_name, page_content)  # save in cache
            else:  # download error
                self._inc_network_errors()
        # parse page content independently if it was read from cache or by network from server
        if (page_content is not None) and (page_name is not None):
            self.on_page_downloaded(page_name)  # process downloaded page
        return page_content

    def _post_page_url(self, page_url: str, post_data: dict=None, referer: str=None):
        """
        For internal needs, sends a POST request, and handles possible error returns
        :param page_url: URL to send HTTP POST to
        :param post_data: dict with post data key-value pairs
        :param referer: if set, use this as value for HTTP Referer header
        :return: response content, or None on error
        """
        # signal that we are starting network request
        if not self._world_is_loading:
            self.net_request_started.emit()
        page_content = self._page_downloader.post(page_url, post_data=post_data, referer=referer)
        # signal that we have finished network request
        if not self._world_is_loading:
            self.net_request_finished.emit()
        # handle errors
        if page_content is None:
            self._inc_network_errors()
        return page_content

    def _download_galaxy_page(self, galaxy_no, sys_no, force_download=False):
        # 'http://uni4.xnova.su/?set=galaxy&r=3&galaxy=3&system=130'
        page_url = '?set=galaxy&r=3&galaxy={0}&system={1}'.format(galaxy_no, sys_no)
        page_name = 'galaxy_{0}_{1}'.format(galaxy_no, sys_no)
        # if force_download is True, cache_lifetime is ignored
        return self._get_page_url(page_name, page_url,
                                  self._galaxy_cache_lifetime, force_download)

    def _download_image(self, img_path: str):
        img_bytes = self._page_downloader.download_url_path(img_path, return_binary=True)
        if img_bytes is None:
            logger.error('image dnl failed: [{0}]'.format(img_path))
            self._inc_network_errors()
            return
        self._page_cache.save_image(img_path, img_bytes)

    def _download_planet_overview(self, planet_id: int, force_download=False):
        # url to change current planet is:
        #    http://uni4.xnova.su/?set=overview&cp=60668&re=0
        page_url = '?set=overview&cp={0}&re=0'.format(planet_id)
        page_name = 'overview'
        return self._get_page_url(page_name, page_url, 1, force_download)

    def _download_planet_buildings(self, planet_id: int, force_download=False):
        page_url = '?set=buildings&cp={0}&re=0'.format(planet_id)
        page_name = 'buildings_{0}'.format(planet_id)
        return self._get_page_url(page_name, page_url,
                                  self._planet_buildings_cache_lifetime, force_download)

    def _download_planet_shipyard(self, planet_id: int, force_download=False):
        # url to change current planet is:
        #    http://uni4.xnova.su/?set=buildings&mode=fleet&cp=60668&re=0
        page_url = '?set=buildings&mode=fleet&cp={0}&re=0'.format(planet_id)
        page_name = 'shipyard_{0}'.format(planet_id)
        return self._get_page_url(page_name, page_url,
                                  self._planet_shipyard_cache_lifetime, force_download)

    def _download_planet_defense(self, planet_id: int, force_download=False):
        # url to change current planet is:
        #    http://uni4.xnova.su/?set=buildings&mode=defense&cp=60668&re=0
        page_url = '?set=buildings&mode=defense&cp={0}&re=0'.format(planet_id)
        page_name = 'defense_{0}'.format(planet_id)
        return self._get_page_url(page_name, page_url,
                                  self._planet_shipyard_cache_lifetime, force_download)

    def _download_planet_researches(self, planet_id: int, force_download=False):
        # url: http://uni4.xnova.su/?set=buildings&mode=research&cp=57064&re=0
        page_url = '?set=buildings&mode=research&cp={0}&re=0'.format(planet_id)
        page_name = 'research_{0}'.format(planet_id)
        return self._get_page_url(page_name, page_url,
                                  self._planet_research_cache_lifetime, force_download)

    def _download_planet_researches_fleet(self, planet_id: int, force_download=False):
        # url: http://uni4.xnova.su/?set=buildings&mode=research_fleet&cp=57064&re=0
        page_url = '?set=buildings&mode=research_fleet&cp={0}&re=0'.format(planet_id)
        page_name = 'researchfleet_{0}'.format(planet_id)
        return self._get_page_url(page_name, page_url,
                                  self._planet_research_cache_lifetime, force_download)

    def _download_planet(self, planet_id: int, delays_msec: int=None, force_download: bool=False):
        # planet buildings in progress
        self._download_planet_buildings(planet_id, force_download)
        if delays_msec is not None:
            self.msleep(delays_msec)
        # planet researches and in progress
        self._download_planet_researches(planet_id, force_download)
        if delays_msec is not None:
            self.msleep(delays_msec)
        # planet factory researches and in progress
        self._download_planet_researches_fleet(planet_id, force_download)
        if delays_msec is not None:
            self.msleep(delays_msec)
        # planet shipyard/defense builds in progress
        self._download_planet_shipyard(planet_id, force_download)
        if delays_msec is not None:
            self.msleep(delays_msec)
        self._download_planet_defense(planet_id, force_download)
        if delays_msec is not None:
            self.msleep(delays_msec)
        if not self._world_is_loading:
            self.loaded_planet.emit(planet_id)

    def _request_rename_planet(self, planet_id: int, new_name: str):
        post_url = '?set=overview&mode=renameplanet&pl={0}'.format(planet_id)
        post_data = dict()
        post_data['action'] = 'Сменить название'
        post_data['newname'] = new_name
        referer = 'http://{0}/?set=overview&mode=renameplanet'.format(self._page_downloader.xnova_url)
        self._post_page_url(post_url, post_data, referer)
        logger.debug('Rename planet to [{0}] complete'.format(new_name))

    def _request_build_item(self, planet_id: int, bitem: XNPlanetBuildingItem, quantity: int):
        logger.debug('Request to build: {0} lv {1} x {2} on planet {3}, build_link = [{4}]'.format(
                bitem.name, bitem.level+1, quantity, planet_id, bitem.build_link))
        if bitem.is_building_item or bitem.is_research_item or bitem.is_researchfleet_item:
            if bitem.build_link is None or (bitem.build_link == ''):
                logger.warn('bitem build_link is empty, cannot build!')
                return
            # construct page name and referer
            # successful request to build item redirects to buildings page
            page_name = None
            referer = ''
            if bitem.is_building_item:
                page_name = 'buildings_{0}'.format(planet_id)
                referer = '?set=buildings'
            elif bitem.is_research_item:
                page_name = 'research_{0}'.format(planet_id)
                referer = '?set=buildings&mode=research'
            elif bitem.is_researchfleet_item:
                referer = '?set=buildings&mode=research_fleet'
                page_name = 'researchfleet_{0}'.format(planet_id)
            # send request
            self._get_page_url(page_name, bitem.build_link,
                               max_cache_lifetime=0, force_download=True,
                               referer=referer)
        elif bitem.is_shipyard_item:
            # TODO: support building ships/defense!
            logger.warn('Cannot build shipyard items for now!')

    def _request_build_cancel(self, planet_id: int, bitem: XNPlanetBuildingItem):
        logger.debug('Request to cancel build: {0} on planet {1}, remove_link = [{2}]'.format(
                bitem.name, planet_id, bitem.remove_link))
        if bitem.is_building_item or bitem.is_research_item or bitem.is_researchfleet_item:
            if bitem.remove_link is None or (bitem.remove_link == ''):
                logger.warn('bitem remove_link is empty, cannot cancel build!')
                return
            # construct page name and referer
            # successful request to cancel build item redirects to buildings page
            page_name = None
            referer = ''
            if bitem.is_building_item:
                page_name = 'buildings_{0}'.format(planet_id)
                referer = '?set=buildings'
            elif bitem.is_research_item:
                page_name = 'research_{0}'.format(planet_id)
                referer = '?set=buildings&mode=research'
            elif bitem.is_researchfleet_item:
                page_name = 'researchfleet_{0}'.format(planet_id)
                referer = '?set=buildings&mode=research_fleet'
            # send request
            self._get_page_url(page_name, bitem.remove_link,
                               max_cache_lifetime=0, force_download=True,
                               referer=referer)
        else:
            logger.warn('Cannot cancel shipyard item: {0}'.format(bitem))

    def _request_build_dismantle(self, planet_id: int, bitem: XNPlanetBuildingItem):
        logger.debug('Request to downgrade building: {0} on planet {1}, dismantle_link = [{2}]'.format(
                bitem.name, planet_id, bitem.dismantle_link))
        if bitem.is_building_item:
            if bitem.dismantle_link is None or (bitem.dismantle_link == ''):
                logger.warn('bitem dismantle_link is empty, cannot dismantle build!')
                return
            # construct page name and referer
            # successful request to cancel build item redirects to buildings page
            page_name = 'buildings_{0}'.format(planet_id)
            referer = '?set=buildings'
            # send request
            self._get_page_url(page_name, bitem.dismantle_link,
                               max_cache_lifetime=0, force_download=True,
                               referer=referer)
        else:
            logger.warn('Can only dismantle buildings items! bitem={0}'.format(bitem))

    # internal, called from thread on first load
    def _full_refresh(self):
        logger.info('thread: starting full world update')
        # full refresh always downloads all pages, ignoring cache
        self.lock()
        self._world_is_loading = True
        # load all pages that contain useful information
        load_progress_percent = 0
        load_progress_step = 5
        pages_list = ['techtree', 'overview', 'imperium', 'fleet']
        pages_maxtime = [3600, 60, 60, 60]  # pages' expiration time in cache
        for i in range(0, len(pages_list)):
            page_name = pages_list[i]
            page_time = pages_maxtime[i]
            self.world_load_progress.emit(page_name, load_progress_percent)
            self._get_page(page_name, max_cache_lifetime=page_time, force_download=False)
            self.msleep(100)  # delay before requesting next page
            load_progress_percent += load_progress_step
        #
        # additionally request user info page, constructed as:
        #  http://uni4.xnova.su/?set=players&id=71995
        #  This need overview parser to parse and fetch account id
        self.world_load_progress.emit('self_user_info', load_progress_percent)
        self._get_page('self_user_info', max_cache_lifetime=60, force_download=False)
        load_progress_percent += load_progress_step
        #
        # download all planets info
        load_progress_left = 100 - load_progress_percent
        load_progress_step = load_progress_left // len(self._planets)
        for pl in self._planets:
            self.world_load_progress.emit(self.tr('Planet') + ' ' + pl.name, load_progress_percent)
            load_progress_percent += load_progress_step
            # planet image
            self._download_image(pl.pic_url)
            self.msleep(100)  # wait 100 ms
            # all other planet items
            self._download_planet(pl.planet_id, delays_msec=100, force_download=True)
        self.msleep(100)
        # restore original current planet that was before full world refresh
        # because world refresh changes it by loading every planet
        logger.info('Restoring current planet to #{0} ({1})'.format(self._cur_planet_id, self._cur_planet_name))
        self._download_planet_overview(self._cur_planet_id, force_download=True)
        self._world_is_loading = False
        self.unlock()  # unlock before emitting any signal, just for a case...
        #
        # signal wain window that we fifnished initial loading
        self.world_load_complete.emit()

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

    def _gettid_s(self):
        """
        Get thread ID as descriptive string
        :return: 'gui' if called from main GUI thread, 'network' if from net bg thread
        """
        tid = self._gettid()
        if tid == self._maintid:
            return 'gui'
        if tid == self._worldtid:
            return 'network'
        return 'unknown_' + str(tid)

    def run(self):
        """
        Main thread function, lives in Qt event loop to receive/send Qt events
        :return: cannot return any value, including None
        """
        self._worldtid = self._gettid()
        # start new life from full downloading of current server state
        self._full_refresh()
        ret = -1
        while ret != self.SIGNAL_QUIT:
            # logger.debug('thread: entering Qt event loop, tid={0}'.format(self._worldtid))
            ret = self.exec()  # enter Qt event loop to receive events
            # logger.debug('thread: Qt event loop ended with code {0}'.format(ret))
            # parse event loop's return value
            if ret == self.SIGNAL_QUIT:
                break
            if ret == self.SIGNAL_RELOAD_PAGE:
                self.on_signal_reload_page()
            elif ret == self.SIGNAL_RENAME_PLANET:
                self.on_signal_rename_planet()
            elif ret == self.SIGNAL_RELOAD_PLANET:
                self.on_signal_reload_planet()
            elif ret == self.SIGNAL_BUILD_ITEM:
                self.on_signal_build_item()
            elif ret == self.SIGNAL_BUILD_CANCEL:
                self.on_signal_build_cancel()
            elif ret == self.SIGNAL_BUILD_DISMANTLE:
                self.on_signal_build_dismantle()
            elif ret == self.SIGNAL_TEST_PARSE_GALAXY:
                self.on_signal_test_parse_galaxy()
            #
            # clear signal arguments after handler
            self._signal_kwargs = dict()
        logger.debug('thread: exiting.')


# only one instance of XNovaWorld should be!
# well, there may be others, but for coordination it should be one
_singleton_XNovaWorld = None


# Factory
# Serves as singleton entry-point to get world class instance
def XNovaWorld_instance() -> XNovaWorld:
    global _singleton_XNovaWorld
    if not _singleton_XNovaWorld:
        _singleton_XNovaWorld = XNovaWorld()
    return _singleton_XNovaWorld
