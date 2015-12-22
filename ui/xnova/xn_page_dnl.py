import configparser
import json

import requests
import requests.exceptions
import requests.cookies

import requesocks
import requesocks.exceptions

from . import xn_logger

logger = xn_logger.get(__name__, debug=False)


# Incapsulates network layer:
# all operations for getting data from server
class XNovaPageDownload:
    def __init__(self, cookies_dict: dict=None):
        self.xnova_url = 'uni4.xnova.su'
        self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.error_str = None
        self.proxy = None
        self.sess = None
        # load config
        self.read_config()
        # construct requests HTTP session
        self.construct_session()
        # setup cookies
        if cookies_dict:
            self.set_cookies_from_dict(cookies_dict)

    def read_config(self):
        cfg = configparser.ConfigParser()
        cfg.read('config/net.ini', encoding='utf-8')
        if 'net' in cfg:
            self.user_agent = cfg['net']['user_agent']
            self.xnova_url = cfg['net']['xnova_url']
            self.proxy = cfg['net']['proxy']
            if self.proxy == '':
                self.proxy = None

    def construct_session(self):
        if self.proxy is not None:
            if self.proxy.startswith('socks5://'):
                # for SOCKS5 proxy create requesocks session
                self.sess = requesocks.session()
                logger.info('Using SOCKS5 proxy session (requesocks)')
        else:
            self.sess = requests.Session()  # else normal session
            logger.info('Using normal session (requests)')
        if self.proxy is not None:
            self.sess.proxies = {'http': self.proxy, 'https': self.proxy}
            logger.info('Set HTTP/HTTPS proxy to: {0}'.format(self.proxy))
        self.sess.headers.update({'user-agent': self.user_agent})
        self.sess.headers.update({'referer': 'http://{0}/'.format(self.xnova_url)})

    def set_useragent(self, ua_str):
        self.user_agent = ua_str
        self.sess.headers.update({'user-agent': self.user_agent})

    def set_cookies_from_dict(self, cookies_dict: dict, do_save=False, json_filename=None):
        self.sess.cookies = requests.cookies.cookiejar_from_dict(cookies_dict)
        if do_save:
            # Save cookies to file
            # Note: cache dir should exist at this point, because
            #   XNovaPageCache.load_from_disk_cache() is called right before
            #   this function from XNovaWorld.initialize(), which creates cache dirs
            #   if they do not exist.
            try:
                filename = './cache/cookies.json'
                if json_filename is not None:
                    filename = json_filename
                with open(filename, mode='wt', encoding='UTF-8') as f:
                    f.write(json.dumps(cookies_dict, sort_keys=True, indent=4))
            except IOError:
                pass

    def load_cookies_from_file(self, filename: str):
        result = True
        try:
            s = ''
            with open(filename, mode='rt', encoding='UTF-8') as f:
                s = f.read()
            cookies_dict = json.loads(s)
            if type(cookies_dict) == dict:
                self.set_cookies_from_dict(cookies_dict, do_save=False)
        except IOError:
            result = False
        return result

    # error handler
    def _set_error(self, errstr):
        self.error_str = errstr

    # real downloader function
    # returns None on failure, string or binary data on success
    def download_url_path(self, url_path: str, return_binary=False):
        self.error_str = None  # clear error
        # construct url to download
        url = 'http://{0}/{1}'.format(self.xnova_url, url_path)
        logger.debug('GET [{0}]...'.format(url))
        ret = None
        try:
            r = self.sess.get(url)
            if r.status_code == requests.codes.ok:
                if not return_binary:
                    ret = r.text
                else:
                    ret = r.content
                logger.debug('GET [{0}] OK'.format(url))
                # on successful request, update referer header for the next request
                self.sess.headers.update({'referer': url})
            else:
                logger.error('Unexpected response code: HTTP {0}'.format(r.status_code))
                self._set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.error('Exception {0}'.format(type(e)))
            self._set_error(str(e))
        except requesocks.exceptions.RequestException as e:
            logger.error('Requesocks exception {0}'.format(type(e)))
            self._set_error(str(e))
        return ret

    def post(self, url_path: str, post_data: dict = None, return_binary=False, referer=None):
        ret = None
        url = 'http://{0}/{1}'.format(self.xnova_url, url_path)
        logger.debug('POST [{0}]...'.format(url))
        try:
            if referer is not None:
                self.sess.headers.update({'referer': referer})
            r = self.sess.post(url, data=post_data)
            if r.status_code == requests.codes.ok:
                if not return_binary:
                    ret = r.text
                else:
                    ret = r.content
                logger.debug('POST [{0}] OK'.format(url))
            else:
                logger.error('Unexpected response code: HTTP {0}'.format(r.status_code))
                self._set_error('HTTP {0}'.format(r.status_code))
        except requests.exceptions.RequestException as e:
            logger.error('Exception {0}'.format(type(e)))
            self._set_error(str(e))
        except requesocks.exceptions.RequestException as e:
            logger.error('Requesocks exception {0}'.format(type(e)))
            self._set_error(str(e))
        return ret
