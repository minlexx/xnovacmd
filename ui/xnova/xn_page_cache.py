import os
import pathlib
import locale
import time

from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# Incapsulates downloaded pages storage
# keeps all downloaded files in ./cache
# the file first requested from this cache,
# and only if get() returns None, it will be
# downloaded over network
class XNovaPageCache:
    def __init__(self):
        self._pages = {}
        self._mtimes = {}
        self._page_cache_dir = './cache/page'
        self._img_cache_dir = './cache/img'
        self.save_load_encoding = locale.getpreferredencoding()

    # scan ./cache directory and load all files into memory
    def load_from_disk_cache(self, clean=True):
        if clean:
            self._pages = {}
            self._mtimes = {}
        cache_dir = pathlib.Path(self._page_cache_dir)
        if not cache_dir.exists():
            try:
                cache_dir.mkdir(parents=True)
            except OSError as ose:
                pass
            return
        num_loaded = 0
        for subitem in cache_dir.iterdir():
            if subitem.is_file():
                try:
                    # get file last modification time
                    stt = subitem.stat()
                    mtime = int(stt.st_mtime)
                    if subitem.name != 'login.dat':
                        # skip login.dat
                        with subitem.open(mode='rt', encoding=self.save_load_encoding) as f:
                            fname = subitem.name
                            contents = f.read()
                            self._pages[fname] = contents  # save file contents
                            self._mtimes[fname] = mtime  # save also modification time
                            num_loaded += 1
                except IOError as ioe:
                    pass
                except UnicodeDecodeError as ude:
                    logger.error('Encoding error in [{0}], skipped: {1}'.format(subitem.name, str(ude)))
        logger.info('Loaded {0} cached pages.'.format(num_loaded))
        # ensure that image cache dir also exists
        cache_dir = pathlib.Path(self._img_cache_dir)
        if not cache_dir.exists():
            try:
                cache_dir.mkdir(parents=True)
            except OSError as ose:
                pass
            return

    # save page into cache
    def set_page(self, page_name, contents):
        self._pages[page_name] = contents
        self._mtimes[page_name] = int(time.time())  # also update modified time!
        try:
            fn = os.path.join(self._page_cache_dir, page_name)
            f = open(fn, mode='wt', encoding=self.save_load_encoding)
            # f = open(fn, mode='wt')
            f.write(contents)
            f.close()
        except IOError as ioe:
            logger.error('set_page("{0}", ...): IOError: {1}'.format(page_name, str(ioe)))

    def save_image(self, img_path: str, img_bytes: bytes):
        img_path_plain = img_path.replace('/', '_')
        filename = os.path.join(self._img_cache_dir, img_path_plain)
        try:
            with open(filename, mode='wb') as f:
                f.write(img_bytes)
        except IOError as ioe:
            logger.error('image [{0}] save failed: [{1}]'.format(filename, str(ioe)))

    # get page from cache
    # the file first requested from this cache,
    # and only if get() returns None, it will be
    # downloaded over network
    def get_page(self, page_name, max_cache_secs=None):
        if len(page_name) < 1:
            return None
        if page_name in self._pages:
            # should we check file cache time?
            if max_cache_secs is None:
                # do not check cache time, just return
                return self._pages[page_name]
            # get current time
            tm_now = int(time.time())
            tm_cache = self._mtimes[page_name]
            tm_diff = tm_now - tm_cache
            if tm_diff <= max_cache_secs:
                return self._pages[page_name]
            logger.debug('cache considered invalid for [{0}]: {1}s > {2}s'.format(page_name, tm_diff, max_cache_secs))
        return None
