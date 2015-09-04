import datetime

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread, Qt

from .xn_data import XNAccountInfo
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload
from .xn_data import XNCoords, XNPlanet
from .xn_parser_overview import OverviewParser
from .xn_parser_userinfo import UserInfoParser
from .xn_parser_curplanet import CurPlanetParser
from .xn_parser_imperium import ImperiumParser
from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# created by main window to keep info about world updated
class XNovaWorld(QThread):

    # signal to be emitted when page is just fetched from server and ready to process
    page_downloaded = pyqtSignal(str)  # (page_name)
    # signal to be emitted when initial loging is complete
    world_load_complete = pyqtSignal()

    def __init__(self, parent=None):
        super(XNovaWorld, self).__init__(parent)
        # helpers
        self.page_cache = XNovaPageCache()
        self.page_downloader = XNovaPageDownload()
        # parsers
        self.parser_overview = OverviewParser()
        self.parser_userinfo = UserInfoParser()
        self.parser_curplanet = CurPlanetParser()
        self.parser_imperium = ImperiumParser()
        # world/user info
        self.server_time = datetime.datetime.today()
        self.account = XNAccountInfo()
        self.flights = []
        self.cur_planet_id = 0
        self.cur_planet_name = ''
        self.cur_planet_coords = XNCoords(0, 0, 0)
        self.planets = []
        # misc
        self.net_errors_count = 0

    def initialize(self, cookies_dict: dict):
        # load cached pages
        self.page_cache.load_from_disk_cache(clean=True)
        # init network session with cookies for authorization
        self.page_downloader.set_cookies_from_dict(cookies_dict)
        # connections
        logger.debug('XNovaWorld: initialized from tid={0}'.format(self._gettid()))
        self.page_downloaded.connect(self.on_page_downloaded, Qt.QueuedConnection)

    def get_account_info(self) -> XNAccountInfo:
        return self.account

    def get_flights(self) -> list:
        # return data, making a copy of world flights for self
        # because caller may modify those (del items when fleet arrives)
        return self.flights.copy()

    def get_server_time(self) -> datetime.datetime:
        return self.server_time

    def get_planets(self) -> list:
        return self.planets.copy()

    # this should re-calculate all user's object statuses
    # like fleets in flight, buildings in construction,
    # reserches in progress, etc, ...
    def world_tick(self):
        # logger.debug('world_tick() called')
        pass

    ################################################################################

    @pyqtSlot(str)
    def on_page_downloaded(self, page_name: str):
        logger.debug('on_page_downloaded({0}) tid={1}'.format(page_name, self._gettid()))
        # cache has the page inside before the signal was emitted!
        # we can get page content from cache
        page_content = self.page_cache.get_page(page_name)
        if not page_content:
            raise ValueError('This should not ever happen!')
        # dispatch parser and merge data
        if page_name == 'overview':
            self.parser_overview.parse_page_content(page_content)
            self.account = self.parser_overview.account
            self.flights = self.parser_overview.flights
            self.server_time = self.parser_overview.server_time
            # run also cur planet parser on the same content
            self.parser_curplanet.parse_page_content(page_content)
            self.cur_planet_id = self.parser_curplanet.cur_planet_id
            self.cur_planet_name = self.parser_curplanet.cur_planet_name
            self.cur_planet_coords = self.parser_curplanet.cur_planet_coords
        elif page_name == 'self_user_info':
            self.parser_userinfo.parse_page_content(page_content)
            self.account.scores.buildings = self.parser_userinfo.buildings
            self.account.scores.buildings_rank = self.parser_userinfo.buildings_rank
            self.account.scores.fleet = self.parser_userinfo.fleet
            self.account.scores.fleet_rank = self.parser_userinfo.fleet_rank
            self.account.scores.defense = self.parser_userinfo.defense
            self.account.scores.defense_rank = self.parser_userinfo.defense_rank
            self.account.scores.science = self.parser_userinfo.science
            self.account.scores.science_rank = self.parser_userinfo.science_rank
            self.account.scores.total = self.parser_userinfo.total
            self.account.scores.rank = self.parser_userinfo.rank
            self.account.main_planet_name = self.parser_userinfo.main_planet_name
            self.account.main_planet_coords = self.parser_userinfo.main_planet_coords
            self.account.alliance_name = self.parser_userinfo.alliance_name
        elif page_name == 'imperium':
            self.parser_imperium.parse_page_content(page_content)
            self.planets = self.parser_imperium.planets

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
            if self.account.id == 0:
                logger.warn('XNovaWorld: requested account info page, but account id is 0!')
                return None
            sub_url = '?set=players&id={0}'.format(self.account.id)
        else:
            logger.warn('XNovaWorld: unknown page name requested: {0}'.format(page_name))
        return sub_url

    # for internal needs, get page from server
    # first try to get from cache
    # if there is no page there, or it is expired, download from net
    def _get_page(self, page_name, max_cache_lifetime=None, force_download=False, do_emit=False):
        page = None
        page_path = self._page_name_to_url_path(page_name)
        if not page_path:
            return None
        if not force_download:
            # try to get cached page
            page = self.page_cache.get_page(page_name, max_cache_lifetime)
        if page is None:
            # try to download
            page = self.page_downloader.download_url_path(page_path)
            if page:
                self.page_cache.set_page(page_name, page)
                # emit signal to process aynchronously, if set to
                if do_emit:
                    self.page_downloaded.emit(page_name)
                else:  # or process sync
                    self.on_page_downloaded(page_name)
            else:
                # page download error
                self.net_errors_count += 1
                logger.debug('XNovaWorld: net error happened, total count: {0}'.format(self.net_errors_count))
                if self.net_errors_count > 10:
                    raise RuntimeError('Too many network errors: {0}!'.format(self.net_errors_count))
        return None

    # internal, called from thread on first load
    def _full_refresh(self):
        logger.info('XNovaWorld thread: starting full world update')
        # load all pages that contain useful information
        pages_list = ['overview', 'imperium']
        # pages' expiration time in cache
        pages_maxtime = [300, 300]
        for i in range(0, len(pages_list)):
            page_name = pages_list[i]
            page_time = pages_maxtime[i]
            self._get_page(page_name, max_cache_lifetime=page_time, force_download=True, do_emit=False)
            QThread.msleep(500)  # 500ms delay before requesting next page
        # additionally request user info page, constructed as:
        #  http://uni4.xnova.su/?set=players&id=71995
        #  This need overview parser to parse and fetch account id
        self._get_page('self_user_info', 300, force_download=True, do_emit=False)
        QThread.msleep(500)
        # signal wain window that we fifnished initial loading
        self.world_load_complete.emit()

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

    # main thread function, lives in Qt event loop to receive/send Qt events
    def run(self):
        # start new life from full downloading of current server state
        self._full_refresh()
        logger.debug('XNovaWorld thread: entering Qt event loop, tid={0}'.format(self._gettid()))
        ret = self.exec()  # enter Qt event loop to receive events
        logger.debug('XNovaWorld thread: Qt event loop ended with code {0}'.format(ret))
        # cannot return result


# only one instance of XNovaWorld should be!
# well, there may be others, but for coordination...
singleton_XNovaWorld = None


# Factory
# Serves as singleton entry-point to get world class instance
def XNovaWorld_instance():
    global singleton_XNovaWorld
    if not singleton_XNovaWorld:
        singleton_XNovaWorld = XNovaWorld()
    return singleton_XNovaWorld
