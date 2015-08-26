from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread

# from PyQt5.QtCore import Qt
# ^^ for Qt.QueuedConnection

from .xn_data import XNCoords, XNovaAccountInfo, XNovaAccountScores
from .xn_page_cache import XNovaPageCache
from .xn_page_dnl import XNovaPageDownload

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class XNovaWorld_impl(QThread):

    page_downloaded = pyqtSignal(str)  # (page_name)

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

    def _get_page(self, page_name, max_cache_lifetime=None, force_download=False):
        page = None
        if not force_download:
            # try to get cached page
            page = self.page_cache.get_page(page_name, max_cache_lifetime)
        if page is None:
            # try to download
            page = self.page_downloader.download(page_name)
            if page:
                self.page_cache.set_page(page_name, page)
                self.page_downloaded.emit(page_name)
            else:
                pass

    def initial_download(self):
        logger.info('XNovaWorld thread: starting initial download')
        pages_list = ['overview']
        pages_maxtime = [60]
        for i in range(0, len(pages_list)):
            page_name = pages_list[i]
            page_time = pages_maxtime[i]
            self._get_page(page_name, page_time)
            QThread.msleep(500)  # 500ms delay before requesting next page

    @staticmethod
    def _gettid():
        sip_voidptr = QThread.currentThreadId()
        return int(sip_voidptr)

    def run(self):
        self.initial_download()
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
