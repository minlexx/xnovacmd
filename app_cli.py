import argparse
import re

from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_page_dnl import XNovaPageDownload
from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class NetError(Exception):
    def __init__(self, desc=None):
        super(NetError, self).__init__()
        self.desc = desc if desc is not None else ''


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('login', help='your login')
    parser.add_argument('password', help='your password')
    return parser.parse_args()


def main():
    args = parse_args()
    page_cache = XNovaPageCache()
    page_dnl = XNovaPageDownload()
    # 
    # 1. download main root page
    content = page_dnl.download_url_path('')
    if content is None:
        raise NetError('Network download page error: ' + page_dnl.error_str)
    logger.info('Login form downloaded OK')
    #
    # 2. post login form
    postdata = {'emails': args.login, 'password': args.password, 'rememberme': 'on'}
    referer = 'http://{0}/'.format(page_dnl.xnova_url)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    url = 'http://{0}/?set=login&xd&popup&ajax'.format(page_dnl.xnova_url)
    if page_dnl.sess is not None:
        if page_dnl.sess.headers is not None:
            page_dnl.sess.headers.update(headers)
    content = page_dnl.post(url, postdata, referer=referer)
    if content is None:
        raise NetError('Network download page error: ' + page_dnl.error_str)
    #
    # 3. parse login response
    match = re.search('^<script', content)
    if match is None:
        raise NetError('Login error! Name or password is invalid!')
    logger.info('Login OK!')
    #
    # 4. init page cache, load all cached pages
    page_cache.load_from_disk_cache()


if __name__ == '__main__':
    try:
        main()
    except NetError as e:
        logger.exception('NetError: {0}'.format(e.desc))
    logger.info('Exiting.')
