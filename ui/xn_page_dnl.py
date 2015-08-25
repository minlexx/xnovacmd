import configparser
import requests
import requests.exceptions
import requests.cookies

from . import xn_logger
logger = xn_logger.get(__name__, debug=True)


class XNovaPageDownload:
    def __init__(self, cookies_dict: dict=None):
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        # load user-agent from config/net.ini
        cfg = configparser.ConfigParser()
        cfg.read('config/net.ini', encoding='utf-8')
        if 'net' in cfg:
            self.user_agent = cfg['net']['user_agent']
        # construct requests HTTP session
        self.sess = requests.Session()
        self.sess.headers.update({'user-agent': self.user_agent})
        if cookies_dict:
            self.set_cookies_from_dict(cookies_dict)

    def set_cookies_from_dict(self, cookies_dict: dict):
        self.sess.cookies = requests.cookies.cookiejar_from_dict(cookies_dict)

    def internal_download_url(self, url: str):
        logger.debug('internal: downloading [{0}]...'.format(url))
        text = ''
        try:
            r = self.sess.get(url)
            if r.status_code == requests.codes.ok:
                text = r.text
            else:
                logger.debug('Unexpected response code: HTTP {0}'.format(r.status_code))
                self.set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.debug('Exception {0}'.format(type(e)))
            self.set_error(str(e))