from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread

# from PyQt5.QtCore import Qt
# ^^ for Qt.QueuedConnection

from .xn_data import XNCoords, XNovaAccountInfo, XNovaAccountScores
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


# created by main window to keep info about world updated
class XNovaWorld(QThread):

    # signal to be emitted when page is just fetched from server and ready to process
    page_downloaded = pyqtSignal(str)  # (page_name)

    def __init__(self, parent=None):
        super(XNovaWorld, self).__init__(parent)
        # helpers
        self.page_cache = XNovaPageCache()
        self.page_downloader = XNovaPageDownload()
        # world/user info
        self.account = XNovaAccountInfo()

    def initialize(self, cookies_dict: dict):
        # load cached pages
        self.page_cache.load_from_disk_cache(clean=True)
        # init network session with cookies for authorization
        self.page_downloader.set_cookies_from_dict(cookies_dict)

    # this should re-calculate all user's object statuses
    # like fleets in flight, buildings in construction,
    # reserches in progress, etc, ...
    def world_tick(self):
        # logger.debug('world_tick() called')
        pass

    # internal, converts page identifier to url path
    @staticmethod
    def _page_name_to_url_path(page_name: str):
        urls_dict = dict()
        urls_dict['overview'] = '?set=overview'
        urls_dict['imperium'] = '?set=imperium'
        sub_url = None
        if page_name in urls_dict:
            return urls_dict[page_name]
        else:
            logger.warn('XNovaWorld: unknown page name requested: {0}'.format(page_name))
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
            page = self.page_cache.get_page(page_name, max_cache_lifetime)
        if page is None:
            # try to download
            page = self.page_downloader.download_url_path(page_path)
            if page:
                self.page_cache.set_page(page_name, page)
                self.page_downloaded.emit(page_name)
            else:
                # page download error
                # TODO: write appropriate handler later
                pass
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
            self._get_page(page_name, page_time)
            QThread.msleep(500)  # 500ms delay before requesting next page

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

    # main thread function, lives in Qt event loop to receive/send Qt events
    def run(self):
        # start new life from full downloading of current server state
        self._full_refresh()
        logger.debug('XNovaWorld thread: entering event loop, cur thread: {0}'.format(self._gettid()))
        ret = self.exec()  # enter Qt event loop to receive events
        logger.debug('XNovaWorld thread: event loop ended with code {0}'.format(ret))
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
