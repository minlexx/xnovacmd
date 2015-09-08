import datetime

from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QThread, QMutex

from .xn_data import XNAccountInfo
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload
from .xn_data import XNCoords, XNFlight, XNPlanet
from .xn_parser_overview import OverviewParser
from .xn_parser_userinfo import UserInfoParser
from .xn_parser_curplanet import CurPlanetParser
from .xn_parser_imperium import ImperiumParser
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# created by main window to keep info about world updated
class XNovaWorld(QThread):
    SIGNAL_QUIT = 0
    SIGNAL_RELOAD_PAGE = 1

    # signal to be emitted when initial world loading is complete
    world_load_complete = pyqtSignal()
    # emitted when fleet has arrived at its destination
    flight_arrived = pyqtSignal(XNFlight)

    def __init__(self, parent=None):
        super(XNovaWorld, self).__init__(parent)
        # helpers
        self._page_dnl_times = dict()
        self._page_cache = XNovaPageCache()
        self._page_downloader = XNovaPageDownload()
        # parsers
        self._parser_overview = OverviewParser()
        self._parser_userinfo = UserInfoParser()
        self._parser_curplanet = CurPlanetParser()
        self._parser_imperium = ImperiumParser()
        # world/user info
        self._server_time = datetime.datetime.today()  # server time at last overview update
        # all we need to calc server time is actually time diff with our time:
        self._diff_with_server_time_secs = 0  # calculated as: our_time - server_time
        self._account = XNAccountInfo()
        self._flights = []
        self._cur_planet_id = 0
        self._cur_planet_name = ''
        self._cur_planet_coords = XNCoords(0, 0, 0)
        self._planets = []
        # internal need
        self._net_errors_count = 0
        self._mutex = QMutex(QMutex.Recursive)
        self._signal_kwargs = dict()
        # thread identifiers, collected here mainly for debugging purposes
        # those are actually:
        # - DWORD GetCurrentThreadId() in Windows
        # - pthread_t pthread_current() in Linux
        self._maintid = 0
        self._worldtid = 0
        # settings
        self._overview_update_interval = 60  # seconds

    def initialize(self, cookies_dict: dict):
        """
        Called from main window just before thread starts
        :param cookies_dict: dictionary with cookies for networking
        :return: None
        """
        # load cached pages
        self._page_cache.load_from_disk_cache(clean=True)
        # init network session with cookies for authorization
        self._page_downloader.set_cookies_from_dict(cookies_dict)
        # misc
        self._maintid = self._gettid()
        logger.debug('initialized from tid={0}'.format(self._maintid))

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
        self.lock()
        self.quit()
        self.unlock()

    def signal(self, signal_code=0, **kwargs):
        # logger.debug('signal: kwargs = {0}'.format(str(kwargs)))
        # ^^: args = (), kwargs = {'page': 'overview'}
        self.lock()
        if kwargs is not None:
            self._signal_kwargs = kwargs
        self.exit(signal_code)  # QEventLoop.exit(code) makes thread's event loop to exit with code
        self.unlock()

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
        self.lock()
        ret = self._flights
        self.unlock()
        return ret

    def get_flight_remaining_time_secs(self, fl: XNFlight) -> int:
        """
        Calculates flight remaining time, adjusting time by difference
        between our time and server
        :param fl: flight
        :return: remaining time in seconds, or None on error
        """
        self.lock()
        secs_left = fl.remaining_time_secs(self._diff_with_server_time_secs)
        self.unlock()
        if secs_left is None:
            return None
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
        self.lock()
        ret = self._planets
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
        self._maybe_refresh_overview()
        self.unlock()

    def _world_tick_flights(self):
        # logger.debug('tick: server time diff: {0}'.format(self._diff_with_server_time_secs))  # 0:00:16.390197
        # iterate
        finished_flights_count = 0
        for fl in self._flights:
            secs_left = self.get_flight_remaining_time_secs(fl)
            if secs_left is None:
                raise ValueError('Flight seconds left is None: {0}'.format(str(fl)))
            if secs_left <= 0:
                logger.debug('==== Flight considered complete, seconds left: {0}'.format(secs_left))
                logger.debug('==== Flight: {0}'.format(str(fl)))
                logger.debug('==== additional debug info:')
                logger.debug('====  - diff with server time: {0}'.format(self._diff_with_server_time_secs))
                logger.debug('====  - current time: {0}'.format(datetime.datetime.today()))
                logger.debug('====  - current server time: {0}'.format(self.get_current_server_time()))
                finished_flights_count += 1
        if finished_flights_count > 0:
            logger.debug('==== Removing total {0} arrived flights'.format(finished_flights_count))
            for irow in range(finished_flights_count):
                try:
                    # finished_flight = self._flights[irow]
                    # item-to-delete from python list will always have index 0?
                    # because we need to delete the first item every time
                    finished_flight = self._flights[0]
                    del self._flights[0]
                    # emit signal
                    self.flight_arrived.emit(finished_flight)
                except IndexError:
                    # should never happen
                    logger.error('IndexError while clearing finished flights: ')
                    logger.error(' deleting index {0}, while total list len: {1}'.format(
                        0, len(self._flights)))
        # end world_tick_flights()

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
        logger.debug('on_page_downloaded({0}) tid={1}'.format(page_name, self._gettid()))
        # cache has the page inside before the signal was emitted!
        # we can get page content from cache
        page_content = self._page_cache.get_page(page_name)
        if not page_content:
            raise ValueError('This should not ever happen!')
        # get current date/time
        dt_now = datetime.datetime.today()
        self._page_dnl_times[page_name] = dt_now  # save last download time for page
        # dispatch parser and merge data
        if page_name == 'overview':
            self._parser_overview.parse_page_content(page_content)
            self._account = self._parser_overview.account
            self._flights = self._parser_overview.flights
            # get server time also calculate time diff
            self._server_time = self._parser_overview.server_time
            dt_diff = dt_now - self._server_time
            self._diff_with_server_time_secs = int(dt_diff.total_seconds())
            # run also cur planet parser on the same content
            self._parser_curplanet.parse_page_content(page_content)
            self._cur_planet_id = self._parser_curplanet.cur_planet_id
            self._cur_planet_name = self._parser_curplanet.cur_planet_name
            self._cur_planet_coords = self._parser_curplanet.cur_planet_coords
            self._update_current_planet()  # it may have changed
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
            self._parser_imperium.parse_page_content(page_content)
            self._planets = self._parser_imperium.planets
            # since we've overwritten the whole planets array, we need to
            # write current planet into it again
            self._update_current_planet()

    def on_reload_page(self):
        # logger.debug('on_reload_page(), signal args = {0}'.format(str(self._signal_kwargs)))
        if 'page_name' in self._signal_kwargs:
            page_name = self._signal_kwargs['page_name']
            logger.debug('on_reload_page(): reloading {0}'.format(page_name))
            self._get_page(page_name, max_cache_lifetime=1, force_download=True)

    def _update_current_planet(self):
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

    # internal helper, converts page identifier to url path
    def _page_name_to_url_path(self, page_name: str):
        urls_dict = dict()
        urls_dict['overview'] = '?set=overview'
        urls_dict['imperium'] = '?set=imperium'
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

    # for internal needs, get page from server
    # first try to get from cache
    # if there is no page there, or it is expired, download from net
    def _get_page(self, page_name, max_cache_lifetime=None, force_download=False):
        page = None
        page_path = self._page_name_to_url_path(page_name)
        if not page_path:
            return None
        if not force_download:
            # try to get cached page
            page = self._page_cache.get_page(page_name, max_cache_lifetime)
        if page is None:
            # try to download
            page = self._page_downloader.download_url_path(page_path)
            if page:
                self._page_cache.set_page(page_name, page)  # save in cache
                self.on_page_downloaded(page_name)  # process downloaded page
            else:
                # page download error
                self._net_errors_count += 1
                logger.debug('net error happened, total count: {0}'.format(self._net_errors_count))
                if self._net_errors_count > 10:
                    raise RuntimeError('Too many network errors: {0}!'.format(self._net_errors_count))
        return None

    def _download_image(self, img_path: str):
        img_bytes = self._page_downloader.download_url_path(img_path, return_binary=True)
        if img_bytes is None:
            logger.error('image dnl failed: [{0}]'.format(img_path))
            return
        self._page_cache.save_image(img_path, img_bytes)

    # internal, called from thread on first load
    def _full_refresh(self):
        logger.info('thread: starting full world update')
        self.lock()
        # load all pages that contain useful information
        pages_list = ['overview', 'imperium']
        # pages' expiration time in cache
        pages_maxtime = [300, 300]
        for i in range(0, len(pages_list)):
            page_name = pages_list[i]
            page_time = pages_maxtime[i]
            self._get_page(page_name, max_cache_lifetime=page_time, force_download=True)
            QThread.msleep(500)  # 500ms delay before requesting next page
        # additionally request user info page, constructed as:
        #  http://uni4.xnova.su/?set=players&id=71995
        #  This need overview parser to parse and fetch account id
        self._get_page('self_user_info', 300, force_download=True)
        # also download all planets pics
        for pl in self._planets:
            self._download_image(pl.pic_url)
        QThread.msleep(500)
        self.unlock()  # unlock before emitting any signal, just for a case...
        # signal wain window that we fifnished initial loading
        self.world_load_complete.emit()

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

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
                self.on_reload_page()
        logger.debug('thread: exiting.')


# only one instance of XNovaWorld should be!
# well, there may be others, but for coordination it should be one
singleton_XNovaWorld = None


# Factory
# Serves as singleton entry-point to get world class instance
def XNovaWorld_instance():
    global singleton_XNovaWorld
    if not singleton_XNovaWorld:
        singleton_XNovaWorld = XNovaWorld()
    return singleton_XNovaWorld
