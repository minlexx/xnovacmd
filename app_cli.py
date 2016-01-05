import argparse
import configparser
import re

from ui.xnova.xn_page_dnl import XNovaPageDownload
from ui.xnova import xn_logger

logger = xn_logger.get(__name__, debug=True)


class NetError(Exception):
    def __init__(self, desc=None):
        super(NetError, self).__init__()
        self.desc = desc if desc is not None else ''


def parse_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('login', help='your login')
    parser.add_argument('password', help='your password')
    return parser.parse_args()


def main():
    args = parse_args()
    #logger.debug('login={}, password={}'.format(args.login, args.password))
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
    # logger.debug('Going to post login form to {}'.format(url))
    # logger.debug('Postdata: {}'.format(postdata))
    content = page_dnl.post(url, postdata, referer=referer)
    if content is None:
        raise NetError('Network download page error: ' + page_dnl.error_str)
    # logger.debug('login form response = {0}'.format(content))
    # parse login response
    match = re.search('^<script', content)
    if match is None:
        raise NetError('Login error! Name or password is invalid!')
    logger.info('Login OK!')


if __name__ == '__main__':
    try:
        main()
    except NetError as e:
        logger.exception('NetError: {0}'.format(e.desc))
    logger.info('Exiting.')
