from PyQt5.QtCore import QObject, QThread

# from PyQt5.QtCore import Qt
# ^^ for Qt.QueuedConnection

from . import xn_logger
from .xn_data import XNCoords, XNovaAccountInfo, XNovaAccountScores
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload

logger = xn_logger.get(__name__, debug=True)


class XNovaWorld_impl(QThread):
    def __init__(self, parent=None):
        super(XNovaWorld_impl, self).__init__(parent)
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

    def world_tick(self):
        # logger.debug('world_tick() called')
        pass

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

    def run(self):
        logger.debug('XNovaWorld thread: entering event loop, cur thread: {0}'.format(self._gettid()))
        ret = self.exec()
        logger.debug('XNovaWorld thread: event loop ended with code {0}'.format(ret))
        # cannot return result


singleton_XNovaWorld = None


# Serves as singleton entry-point to get world class instance
def XNovaWorld():
    global singleton_XNovaWorld
    if not singleton_XNovaWorld:
        singleton_XNovaWorld = XNovaWorld_impl()
    return singleton_XNovaWorld
