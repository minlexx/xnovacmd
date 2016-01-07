import argparse
import datetime
import re

from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_page_dnl import XNovaPageDownload
from ui.xnova.xn_data import XNAccountInfo, XNCoords, XNFlight, XNPlanet, XNPlanetBuildingItem
from ui.xnova.xn_techtree import XNTechTree_instance
from ui.xnova.xn_parser import XNParserBase
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_curplanet import CurPlanetParser
from ui.xnova.xn_parser_imperium import ImperiumParser
from ui.xnova.xn_parser_fleet import FleetsMaxParser
from ui.xnova.xn_parser_techtree import TechtreeParser
# from ui.xnova.xn_parser_galaxy import GalaxyParser
# from ui.xnova.xn_parser_planet_buildings import PlanetBuildingsAvailParser, PlanetBuildingsProgressParser
# from ui.xnova.xn_parser_planet_energy import PlanetEnergyResParser
# from ui.xnova.xn_parser_shipyard import ShipyardShipsAvailParser, ShipyardBuildsInProgressParser
# from ui.xnova.xn_parser_research import ResearchAvailParser
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


class World:
    def __init__(self, login_email: str, password: str):
        self._login_email = login_email
        self._password = password
        self._page_cache = XNovaPageCache()
        self._page_dnl = XNovaPageDownload()
        self._parsers = dict()
        # world info
        self._techtree = XNTechTree_instance()
        self._account = XNAccountInfo()
        self._flights = []
        self._planets = []
        self._server_time = datetime.datetime.now()
        self._new_messages_count = 0
        self._vacation_mode = False
        self._server_online_players = 0
        self._get_bonus_url = ''
        self._cur_planet_id = 0
        self._cur_planet_name = ''
        self._cur_planet_coords = XNCoords()

    def get_planets(self) -> list:
        return self._planets

    def do_login(self) -> bool:
        # 1. download main root page
        content = self._page_dnl.download_url_path('')
        if content is None:
            raise NetError('Network download page error: ' + page_dnl.error_str)
        logger.info('Login form downloaded OK')
        #
        # 2. post login form
        postdata = {'emails': self._login_email,
            'password': self._password, 'rememberme': 'on'}
        referer = 'http://{0}/'.format(self._page_dnl.xnova_url)
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        url = 'http://{0}/?set=login&xd&popup&ajax'.format(self._page_dnl.xnova_url)
        if self._page_dnl.sess is not None:
            if self._page_dnl.sess.headers is not None:
                self._page_dnl.sess.headers.update(headers)
        content = self._page_dnl.post(url, postdata, referer=referer)
        if content is None:
            raise NetError('Network download page error: ' + self._page_dnl.error_str)
        #
        # 3. parse login response
        match = re.search('^<script', content)
        if match is None:
            raise NetError('Login error! Name or password is invalid!')
        logger.info('Login OK!')
        #
        # 4. post-login init procedure
        self._page_cache.save_load_encoding = 'UTF-8'  # force encoding
        self._page_cache.load_from_disk_cache(clean=True)
        self.init_parsers()
        return True

    def init_parsers(self):
        self._parsers['overview'] = [OverviewParser(), CurPlanetParser()]
        self._parsers['imperium'] = [ImperiumParser()]
        self._parsers['techtree'] = [TechtreeParser()]
        self._parsers['fleet'] = [FleetsMaxParser()]
        self._parsers['self_user_info'] = [UserInfoParser()]

    def run_parser(self, page_name: str, page_content: str):
        logger.debug('Running parsers for: {}'.format(page_name))
        if page_name in self._parsers:
            for parser in self._parsers[page_name]:
                try:
                    if isinstance(parser, XNParserBase):
                        parser.parse_page_content(page_content)
                        # save parser's results
                        if isinstance(parser, OverviewParser):
                            self._account = parser.account
                            self._flights = parser.flights
                            self._server_time = parser.server_time
                            self._new_messages_count = parser.new_messages_count
                            self._vacation_mode = parser.in_RO
                            self._server_online_players = parser.online_players
                            self._get_bonus_url = parser.bonus_url
                        if isinstance(parser, CurPlanetParser):
                            self._cur_planet_id = parser.cur_planet_id
                            self._cur_planet_name = parser.cur_planet_name
                            self._cur_planet_coords = parser.cur_planet_coords
                        if isinstance(parser, ImperiumParser):
                            self._planets = parser.planets
                        if isinstance(parser, TechtreeParser):
                            if len(parser.techtree) > 0:
                                self._techtree.init_techtree(parser.techtree)
                        if isinstance(parser, UserInfoParser):
                            self._account.scores.buildings = parser.buildings
                            self._account.scores.buildings_rank = parser.buildings_rank
                            self._account.scores.fleet = parser.fleet
                            self._account.scores.fleet_rank = parser.fleet_rank
                            self._account.scores.defense = parser.defense
                            self._account.scores.defense_rank = parser.defense_rank
                            self._account.scores.science = parser.science
                            self._account.scores.science_rank = parser.science_rank
                            self._account.scores.total = parser.total
                            self._account.scores.rank = parser.rank
                            self._account.main_planet_name = parser.main_planet_name
                            self._account.main_planet_coords = parser.main_planet_coords
                            self._account.alliance_name = parser.alliance_name
                except AttributeError as ae:
                    logger.error('Unexpected attribute error while running parsers ' \
                        'for page: {0}: {1}'.format(page_name, str(ae)))
        else:
            logger.warn('Cannot find parser for page: [{}]'.format(page_name))

    def _page_name_to_url_path(self, page_name: str):
        urls_dict = dict()
        urls_dict['overview'] = '?set=overview'
        urls_dict['imperium'] = '?set=imperium'
        urls_dict['techtree'] = '?set=techtree'
        urls_dict['fleet'] = '?set=fleet'
        sub_url = None
        if page_name in urls_dict:
            return urls_dict[page_name]
        elif page_name == 'self_user_info':
            # special page case, dynamic URL, depends on user id
            #  http://uni4.xnova.su/?set=players&id=71995
            if self._account.id == 0:
                logger.warn('requested account info page, but account id is 0!')
                return None
            sub_url = '?set=players&id={0}'.format(self._account.id)
        else:
            logger.warn('unknown page name requested: {0}'.format(page_name))
        return sub_url

    def _get_page(self, page_name, max_cache_lifetime=None, force_download=False):
        """
        Gets page from cache or from server only by page name.
        Converts page_name to page URL, using _page_name_to_url_path().
        First tries to get cached page from cache using page_name as key.
        If there is no cached page there, or it is expired, downloads from network.
        Then calls self.on_page_downloaded() to automatically parse requested page.
        :param page_name: 'name' used as key in pages cache
        :param max_cache_lifetime: cache timeout
        :param force_download:
        :return: page contents as str, or None on error
        """
        page_url = self._page_name_to_url_path(page_name)
        if not page_url:
            logger.error('Failed to convert page_name=[{0}] to url!'.format(page_name))
            return None
        return self._get_page_url(page_name, page_url, max_cache_lifetime, force_download)

    def _get_page_url(self, page_name, page_url,
                      max_cache_lifetime=None,
                      force_download=False,
                      referer=None):
        """
        For internal needs, downloads url from server using HTTP GET.
        First tries to get cached page from cache using page_name as key.
        If there is no cached page there, or it is expired, downloads from network.
        Then calls self.on_page_downloaded() to automatically parse requested page.
        If force_download is True, max_cache_lifetime is ignored.
        (This method's return value is ignored for now)
        :param page_name: 'name' of page to use as key when stored to cache, if None - cache disabled
        :param page_url: URL to download in HTTP GET request
        :param max_cache_lifetime:
        :param force_download:
        :param referer: set this to str value to force Referer header before request
        :return: page contents (str) or None on error
        """
        page_content = None
        if not force_download:
            # try to get cached page (default)
            page_content = self._page_cache.get_page(page_name, max_cache_lifetime)
            if page_content is not None:
                logger.debug('... got page "{0}" from cache! (lifetime < {1})'.format(
                        page_name, max_cache_lifetime))
        if page_content is None:
            # set referer, if set
            if referer is not None:
                self._page_dnl.set_referer(referer)
            # try to download
            page_content = self._page_dnl.download_url_path(page_url)
            # save in cache, only if content anf page_name is present
            if (page_content is not None) and (page_name is not None):
                self._page_cache.set_page(page_name, page_content)
            # check for download error
            if page_content is None:  # download error happened
                raise NetError(self._page_dnl.error_str)
        # parse page content independently if it was read from cache or by network from server
        if (page_content is not None) and (page_name is not None):
            self.run_parser(page_name, page_content)  # process downloaded page
        return page_content

    def _post_page_url(self, page_url: str, post_data: dict=None, referer: str=None):
        """
        For internal needs, sends a POST request, and handles possible error returns
        :param page_url: URL to send HTTP POST to
        :param post_data: dict with post data key-value pairs
        :param referer: if set, use this as value for HTTP Referer header
        :return: response content, or None on error
        """
        page_content = self._page_dnl.post(page_url, post_data=post_data, referer=referer)
        # handle errors
        if page_content is None:
            raise NetError(self._page_dnl.error_str)
        return page_content

    def download_galaxy_page(self, galaxy_no, sys_no, force_download=False):
        # 'http://uni4.xnova.su/?set=galaxy&r=3&galaxy=3&system=130'
        page_url = '?set=galaxy&r=3&galaxy={0}&system={1}'.format(
                galaxy_no, sys_no)
        page_name = 'galaxy_{0}_{1}'.format(galaxy_no, sys_no)
        # if force_download is True, cache_lifetime is ignored
        return self._get_page_url(page_name, page_url,
                force_download=force_download)

    def world_refresh(self):
        pages_list = ['techtree', 'overview', 'imperium', 'fleet']
        pages_maxtime = [3600, 60, 60, 60]  # pages' expiration time in cache
        for i in range(0, len(pages_list)):
            page_name = pages_list[i]
            page_time = pages_maxtime[i]
            self._get_page(page_name, max_cache_lifetime=page_time, force_download=False)
        self._get_page('self_user_info', max_cache_lifetime=60, force_download=False)


def main():
    global world
    args = parse_args()
    world = World(args.login, args.password)
    world.do_login()
    world.world_refresh()

    for planet in world.get_planets():
        logger.info('Planet {} {} id #{}'.format(
            planet.name, planet.coords.coords_str(), planet.planet_id))

    content = world._get_page_url('buildings_54450', '?set=buildings&cp=54450',
        None, True)

    content = world.download_galaxy_page(5, 62)


world = None


if __name__ == '__main__':
    try:
        main()
    except NetError as e:
        logger.exception('NetError: {0}'.format(e.desc))
    logger.info('Exiting.')
