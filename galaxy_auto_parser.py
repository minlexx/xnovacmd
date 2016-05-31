#!/usr/bin/python3
import sys
import time
import sqlite3
import json
import argparse
import re
# 3rd party, not used right here, but used by sub-modules anyway
try:
    import requests
except ImportError:
    print('python-requests is not installed? try "pip install requests" or something')
    print('  or apt-get install python3-requests :)')
    sys.exit(1)
try:
    import execjs
except ImportError:
    print('PyExecJS is not installed? try "pip install PyExecJS" or something')
    print('   before that you need pip, apt-get install python3-pip')
    print('   then pip-3 install pyexecjs')
    sys.exit(1)

from ui.xnova import xn_logger
from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_page_dnl import XNovaPageDownload
from ui.xnova.xn_parser_galaxy import GalaxyParser

###############################################
# configure some parameters
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) \
Chrome/45.0.2454.85 Safari/537.36'
delay_between_requests_secs = 5
# galaxy_range = (5, 5)  # debug, originally (1, 5)
# system_range = (75, 75)  # debug, originally (1, 499)
galaxy_range = (1, 5)
system_range = (1, 499)
max_cache_secs = 10 * 3600  # cache galaxy pages for 10 hours
status_filename = 'galaxy_auto_parser.json'


###############################################
# internal state vars, do not touch
logger = xn_logger.get('GAP', debug=True)
g_page_cache = XNovaPageCache()
g_page_dnl = XNovaPageDownload()
g_parser = GalaxyParser()
g_db = sqlite3.connect('galaxy.db')
g_got_from_cache = False


def int_(val):
    if val is None:
        return None
    try:
        r = int(val)
    except ValueError:
        r = 0
    return r


def str_(val):
    if val is None:
        return None
    return str(val)


def parse_range(val: str) -> tuple:
    ret = tuple()
    if val is None:
        return ret
    m = re.match(r'(\d+),(\d+)', val)
    if m:
        start = int_(m.group(1))
        end = int_(m.group(2))
        ret = (start, end)
    return ret


class GalaxyRow:
    def __init__(self):
        self.galaxy = 0
        self.system = 0
        self.position = 0  # position of planet in solar system
        # planet info
        self.planet_id = 0
        self.planet_name = ''
        self.planet_type = 0  # 1-planet, 5-base
        self.planet_metal = 0
        self.planet_crystal = 0
        self.planet_destroyed = 0
        self.planet_image = ''  # unused
        # luna info
        self.luna_id = 0
        self.luna_name = ''
        self.luna_diameter = 0
        self.luna_destroyed = 0
        self.luna_temp = 0  # unused
        self.luna_parent_planet = 0  # unused
        # user info
        self.user_id = 0
        self.user_name = ''
        self.user_rank = 0
        self.user_totalpoints = 0
        self.user_authlevel = 0  # 0-normal, 3-admin
        self.user_onlinetime = 0  # 0-active, 1-i, 2-Ii
        self.user_banned = 0
        self.user_ro = 0  # user vacation mode
        self.user_race = 0  # 1 - confederation, 2 - bionic, 3 - cylon, 4 - ancients
        self.user_image = ''  # unused
        # ally info
        self.ally_id = 0
        self.ally_name = ''
        self.ally_tag = ''
        self.ally_members = 0  # member count
        self.ally_web = ''  # unused, WTF is this? website URL?
        # activity
        self.last_active = 0  # unused

    def from_row(self, gal, sys_, row):
        if row is None:
            return
        self.galaxy = int_(gal)
        self.system = int_(sys_)
        self.position = int_(row['planet'])
        # planet info
        self.planet_id = int_(row['id_planet'])
        self.planet_name = str_(row['name'])
        self.planet_type = int_(row['planet_type'])
        self.planet_metal = int_(row['metal'])
        self.planet_crystal = int_(row['crystal'])
        self.planet_destroyed = int_(row['destruyed'])
        self.planet_image = str_(row['image'])
        # luna info
        self.luna_id = int_(row['luna_id'])
        self.luna_name = str_(row['luna_name'])
        self.luna_diameter = int_(row['luna_diameter'])
        self.luna_destroyed = int_(row['luna_destruyed'])
        self.luna_temp = int_(row['luna_temp'])
        self.luna_parent_planet = int_(row['parent_planet'])
        # user info
        self.user_id = int_(row['user_id'])
        self.user_name = str_(row['username'])
        self.user_rank = int_(row['total_rank'])
        self.user_totalpoints = int_(row['total_points'])
        self.user_authlevel = int_(row['authlevel'])
        self.user_onlinetime = int_(row['onlinetime'])
        self.user_banned = int_(row['banaday'])
        self.user_ro = int_(row['urlaubs_modus_time'])
        self.user_race = int_(row['race'])
        self.user_image = str_(row['user_image'])
        # ally info
        self.ally_id = int_(row['ally_id'])
        self.ally_name = str_(row['ally_name'])
        self.ally_tag = str_(row['ally_tag'])
        self.ally_members = int_(row['ally_members'])
        self.ally_web = str_(row['ally_web'])
        # activity
        self.last_active = int_(row['last_active'])


def check_database_tables():
    cur = g_db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    rows = cur.fetchall()
    existing_tables = list()
    for row in rows:
        existing_tables.append(row[0])
    if 'planets' not in existing_tables:
        logger.info('DB: Creating planets table...')
        q = "CREATE TABLE planets( \
            g INT, \
            s INT, \
            p INT, \
            planet_id INT PRIMARY KEY, \
            planet_name TEXT, \
            planet_type INT, \
            planet_metal INT, \
            planet_crystal INT, \
            planet_destroyed INT, \
            luna_id INT, \
            luna_name TEXT, \
            luna_diameter INT, \
            luna_destroyed INT, \
            user_id INT, \
            user_name TEXT, \
            user_rank INT, \
            user_totalpoints INT, \
            user_authlevel INT, \
            user_onlinetime INT, \
            user_banned INT, \
            user_ro INT, \
            user_race INT, \
            ally_id INT, \
            ally_name TEXT, \
            ally_tag TEXT, \
            ally_members INT \
            )"
        cur.execute(q)
        g_db.commit()
        cur.close()
    logger.info('DB init complete')


def db_set_galaxy_row(r: GalaxyRow):
    # gal, sys_, position,
    # planet
    # planet_id, planet_name, planet_type,
    # planet_metal, planet_crystal, planet_destroyed,
    # luna
    # luna_id, luna_name, luna_diameter, luna_destroyed,
    # user
    # user_id, user_name, user_rank, user_totalpoints,
    # user_authlevel, user_onlinetime, user_banned, user_ro, user_race,
    # ally
    # ally_id, ally_name, ally_tag, ally_members
    # check if planet is already in DB
    exists = True
    cur = g_db.cursor()
    cur.execute('SELECT planet_id FROM planets WHERE g=? AND s=? and p=?', (r.galaxy, r.system, r.position))
    rows = cur.fetchall()
    if len(rows) == 0:
        exists = False
    if exists:
        q = 'UPDATE planets SET \
            planet_id=?, planet_name=?, planet_type=?, planet_metal=?, planet_crystal=?, planet_destroyed=?, \
            luna_id=?,  luna_name=?,  luna_diameter=?, luna_destroyed=?, \
            user_id=?,  user_name=?,  user_rank=?, user_totalpoints=?, user_authlevel=?, user_onlinetime=?, user_banned=?, user_ro=?, user_race=?, \
            ally_id=?,  ally_name=?, ally_tag=?, ally_members=? \
            WHERE (g=? AND s=? AND p=?)'
        cur.execute(
            q, (r.planet_id, r.planet_name, r.planet_type, r.planet_metal, r.planet_crystal, r.planet_destroyed,
            r.luna_id, r.luna_name, r.luna_diameter, r.luna_destroyed,
            r.user_id, r.user_name, r.user_rank, r.user_totalpoints, r.user_authlevel, r.user_onlinetime, r.user_banned, r.user_ro, r.user_race,
            r.ally_id, r.ally_name, r.ally_tag, r.ally_members,
            r.galaxy, r.system, r.position))
    else:
        q = 'INSERT INTO planets VALUES (?,?,?, ?,?,?,?,?,?, ?,?,?,?, ?,?,?,?,?,?,?,?,?, ?,?,?,?)'
        cur.execute(
            q, (r.galaxy, r.system, r.position,
            r.planet_id, r.planet_name, r.planet_type, r.planet_metal, r.planet_crystal, r.planet_destroyed,
            r.luna_id, r.luna_name, r.luna_diameter, r.luna_destroyed,
            r.user_id, r.user_name, r.user_rank, r.user_totalpoints, r.user_authlevel, r.user_onlinetime, r.user_banned, r.user_ro, r.user_race,
            r.ally_id, r.ally_name, r.ally_tag, r.ally_members))
    g_db.commit()
    cur.close()


def xnova_authorize(xn_login, xn_password):
    postdata = {
        'emails': xn_login,
        'password': xn_password,
        'rememberme': 'on'
    }
    r = requests.post('http://uni4.xnova.su/?set=login&xd',
                      data=postdata,
                      allow_redirects=False)
    # print(r.content)  # empty
    # print(r.text)     # also empty
    cookies_dict = {}
    for single_cookie in r.cookies.iteritems():
        cookies_dict[single_cookie[0]] = single_cookie[1]
    # print(cookies_dict)
    if ('x_id' not in cookies_dict) and ('x_secret' not in cookies_dict) \
        and ('x_uni' not in cookies_dict):
        return None
    return cookies_dict


def go_galaxy_system(gal, sys_):
    # try lo get page from cache
    global g_got_from_cache
    page_name = 'galaxy_{0}_{1}'.format(gal, sys_)
    content = g_page_cache.get_page(page_name, max_cache_secs)
    if content is None:
        # not in cache, or invalid, try to download
        url_path = '?set=galaxy&r=3&galaxy={0}&system={1}'.format(gal, sys_)
        content = g_page_dnl.download_url_path(url_path)
        if content is None:
            return False
        g_page_cache.set_page(page_name, content)
        g_got_from_cache = False
    else:
        g_got_from_cache = True
    g_parser.clear()
    g_parser.parse_page_content(content)
    if g_parser.script_body != '':
        g_parser.unscramble_galaxy_script()
    rows = g_parser.galaxy_rows
    if len(rows) > 0:
        # logger.info('{0} planets in [{1}:{2}:]'.format(len(rows), gal, sys_))
        for row in rows:
            if row is None:
                continue
            galaxy_row = GalaxyRow()
            galaxy_row.from_row(gal, sys_, row)
            try:
                db_set_galaxy_row(galaxy_row)
            except OverflowError as ove:
                logger.error('Got overflow error while processing a row at [{0}:{1}:{2}]:'.format(
                    gal, sys_, galaxy_row.position))
                logger.error(str(row))
                logger.error('Saving to overflow_error.json')
                try:
                    row['coords'] = '[{0}:{1}:{2}]'.format(gal, sys_, galaxy_row.position)
                    with open('overflow_error.json', mode='at', encoding='UTF-8') as f:
                        json.dump(row, f, indent=4, sort_keys=True)
                except IOError:
                    pass
    else:
        logger.warn('no planets in [{0}:{1}:]'.format(gal, sys_))
        return True


def output_progress(ts_start, num, total, gal, sys_):
    ts_now = time.time()
    secs_passed = int(ts_now - ts_start)
    speed = 0
    if secs_passed > 0:
        speed = num / secs_passed
    requests_left = total - num
    secs_left = int(requests_left / speed)
    hrs_left = int(secs_left / 3600)
    secs_left -= (hrs_left * 3600)
    mins_left = int(secs_left / 60)
    secs_left -= (mins_left * 60)
    percent = 100.0 * num / total
    cached_str = ''
    global g_got_from_cache
    if g_got_from_cache:
        cached_str = ' [CACHED]'
    logger.info('[{0}/{1}]{2} [{3}:{4}] ({5:0.1f}%) done, {6}s passed, ~{7:02}h {8:02}m {9:02}s left.'.format(
        num, total, cached_str, gal, sys_, percent, secs_passed, hrs_left, mins_left, secs_left))
    try:
        status = dict()
        status['done'] = num
        status['total'] = total
        with open(status_filename, mode='wt', encoding='UTF-8') as f:
            json.dump(status, f, indent=4, sort_keys=True)
    except IOError:
        pass


def go():
    num_galaxies = int(galaxy_range[1]) - int(galaxy_range[0]) + 1
    num_systems = int(system_range[1]) - int(system_range[0]) + 1
    total_requests = num_galaxies * num_systems
    num_requests = 0
    logger.info('Starting scan gals {0}, systems {1}, total {2} requests'.format(
        galaxy_range, system_range, total_requests))
    global g_got_from_cache
    ts_start = time.time()
    for gal in range(int(galaxy_range[0]), int(galaxy_range[1]) + 1):
        for sys_ in range(int(system_range[0]), int(system_range[1]) + 1):
            go_galaxy_system(gal, sys_)
            num_requests += 1
            output_progress(ts_start, num_requests, total_requests, gal, sys_)
            if not g_got_from_cache:
                time.sleep(delay_between_requests_secs)


def list_js_runtimes():
    ajsr = execjs.available_runtimes()
    if len(ajsr) > 0:
        print('Detected {0} JavaScript runtimes:'.format(len(ajsr)))
        for js in ajsr:
            jsr = execjs.get(js)
            pref_str = ''
            if js == 'Node':
                pref_str = ' <== I prefer this one!'
            print('   {0}: {1}{2}'.format(js, jsr.name, pref_str))
    else:
        print('No JS runtimes detected! Install Node.js, spidermonkey or something!')
    sys.exit(0)


def main():
    # parse command line
    ap = argparse.ArgumentParser(description='XNova galaxy scanner/parser. All arguments '
                                             'are optional and have defaults. Default will scan all galaxy.')
    ap.add_argument('--version', action='version', version='%(prog)s 0.1')
    ap.add_argument('--delay', nargs='?', default='5', type=int, metavar='DELAY_SEC',
                    help='delay between requests, in seconds. Default: 5 sec.')
    ap.add_argument('--galaxy-range', nargs='?', default='1,5', type=parse_range, metavar='FROM,TO',
                    help='range of galaxies to scan, in form: "From,To". Default: 1,5')
    ap.add_argument('--system-range', nargs='?', default='1,499', type=parse_range, metavar='FROM,TO',
                    help='range of systems to scan, in form: "From,To". Default: 1,499')
    ap.add_argument('-1', '--one-shot', nargs='?', default='0,0', type=parse_range, metavar='G,S',
                    help='scan only one system, format: 2,129 will scan galaxy 2 system 129. Overrides \
--galaxy-range and --system-range options.')
    ap.add_argument('--cache-lifetime', nargs='?', default='36000', type=int, metavar='CACHE_LIFETIME_SEC',
                    help='cache expiration timeout, in seconds. Default is 10 hours (36000)')
    ap.add_argument('--db-filename', nargs='?', default='galaxy.db',
                    help='Name of sqlite3 db file to store galaxy data. Default is "galaxy.db"')
    ap.add_argument('--status-filename', nargs='?', default='galaxy_auto_parser.json',
                    help='File name where scan progress will be written in JSON format. Default \
is "galaxy_auto_parser.json". JSON output example is: {"done": 1, "total": 10}.')
    ap.add_argument('--cookies-filename', nargs='?', default='./cache/cookies.json',
                    help='Name of JSON file with cookies used to access site. \
Default is "./cache/cookies.json". Ignored if --login and --password are given and auth was OK')
    ap.add_argument('--list-js-runtimes', action='store_true',
                    help='List available detected JavaScript runtimes and exit.')
    # NEW: explicitly set login/password via command-line arguments
    ap.add_argument('--login', nargs='?', default='your@email.com',
                    help='Login to use to authorize in XNova game')
    ap.add_argument('--password', nargs='?', default='your_secret_password',
                    help='Password to use to authorize in XNova game')

    ns = ap.parse_args()

    global g_db, status_filename, galaxy_range, system_range, max_cache_secs, delay_between_requests_secs

    # apply parsed arguments
    g_db = sqlite3.connect(ns.db_filename)
    delay_between_requests_secs = ns.delay
    max_cache_secs = ns.cache_lifetime
    status_filename = ns.status_filename
    galaxy_range = ns.galaxy_range
    system_range = ns.system_range
    if (ns.one_shot[0] > 0) and (ns.one_shot[1] > 0):
        galaxy_range = (ns.one_shot[0], ns.one_shot[0])
        system_range = (ns.one_shot[1], ns.one_shot[1])
    cookies_filename = ns.cookies_filename
    if ns.list_js_runtimes:
        list_js_runtimes()

    have_login = False
    if (ns.login != 'your@email.com') and (ns.password != 'your_secret_password'):
        cookies_dict = xnova_authorize(ns.login, ns.password)
        if cookies_dict is None:
            logger.error('Failed to authorize in XNova!\n')
            sys.exit(1)
        have_login = True
        logger.info('Login to XNova OK!')
        # now we got those cookies, set it to
        g_page_dnl.set_cookies_from_dict(cookies_dict,
                                         do_save=True,
                                         json_filename=cookies_filename)

    # init globals
    g_page_cache.load_from_disk_cache(clean=True)
    g_page_dnl.set_useragent(user_agent)
    if not have_login:
        if not g_page_dnl.load_cookies_from_file(cookies_filename):
            logger.error('Page downloader failed to load cookies JSON!')
            logger.error('Please make sure that file "{0}" exists and contains cookies!'.format(cookies_filename))
            logger.error('(You can provide cookies with --cookies-filename option.)')
            sys.exit(1)
    logger.info('Helpers init complete')
    check_database_tables()
    go()
    g_db.close()
    logger.info('All job done, exiting')


if __name__ == '__main__':
    main()
