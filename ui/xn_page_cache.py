import os
import pathlib
import locale
import time

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class XNovaPageCache:
    def __init__(self):
        self._pages = {}
        self._mtimes = {}
        self.save_load_encoding = locale.getpreferredencoding()

    def load_from_disk_cache(self, clean=True):
        if clean:
            self._pages = {}
            self._mtimes = {}
        cache_dir = pathlib.Path('./cache')
        num_loaded = 0
        for subitem in cache_dir.iterdir():
            if subitem.is_file():
                try:
                    # get file last modification time
                    stt = subitem.stat()
                    mtime = int(stt.st_mtime)
                    with subitem.open(mode='rt', encoding=self.save_load_encoding) as f:
                        fname = subitem.name
                        contents = f.read()
                        self._pages[fname] = contents  # save file contents
                        self._mtimes[fname] = mtime  # save also modification time
                        num_loaded += 1
                except IOError as ioe:
                    pass
        logger.info('Loaded {0} cached pages.'.format(num_loaded))

    def set_page(self, page_name, contents):
        self._pages[page_name] = contents
        try:
            fn = os.path.join('./cache', page_name)
            f = open(fn, mode='wt', encoding=self.save_load_encoding)
            # f = open(fn, mode='wt')
            f.write(contents)
            f.close()
        except IOError as ioe:
            logger.error('set_page("{0}", ...): IOError: {1}'.format(page_name, str(ioe)))

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
