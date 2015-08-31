import configparser

import requests
import requests.exceptions
import requests.cookies

from . import xn_logger

logger = xn_logger.get(__name__, debug=True)


# Incapsulates network layer:
# all operations for getting data from server
class XNovaPageDownload:
    def __init__(self, cookies_dict: dict=None):
        self.xnova_url = 'uni4.xnova.su'
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.error_str = None
        # load user-agent from config/net.ini
        cfg = configparser.ConfigParser()
        cfg.read('config/net.ini', encoding='utf-8')
        if 'net' in cfg:
            self.user_agent = cfg['net']['user_agent']
            self.xnova_url = cfg['net']['xnova_url']
        # construct requests HTTP session
        self.sess = requests.Session()
        self.sess.headers.update({'user-agent': self.user_agent})
        self.sess.headers.update({'referer': 'http://{0}/'.format(self.xnova_url)})
        if cookies_dict:
            self.set_cookies_from_dict(cookies_dict)

    def set_cookies_from_dict(self, cookies_dict: dict):
        self.sess.cookies = requests.cookies.cookiejar_from_dict(cookies_dict)

    # error handler
    def _set_error(self, errstr):
        self.error_str = errstr

    # real downloader function
    # returns None on failure
    def download_url_path(self, url_path: str):
        self.error_str = None  # clear error
        # construct url to download
        url = 'http://{0}/{1}'.format(self.xnova_url, url_path)
        logger.debug('internal: downloading [{0}]...'.format(url))
        text = None
        try:
            r = self.sess.get(url)
            if r.status_code == requests.codes.ok:
                text = r.text
                logger.debug('internal: download [{0}] OK'.format(url))
                # on successful request, update referer header for the next request
                self.sess.headers.update({'referer': url})
            else:
                logger.debug('Unexpected response code: HTTP {0}'.format(r.status_code))
                self._set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.debug('Exception {0}'.format(type(e)))
            self._set_error(str(e))
        return text
