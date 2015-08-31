#!/usr/bin/python3
from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_userinfo import UserInfoParser
from ui.xnova.xn_parser_imperium import ImperiumParser


def main():
    # load file
    cacher = XNovaPageCache()
    cacher.load_from_disk_cache(clean=True)
    content = cacher.get_page('overview')
    # parse overview
    parser = OverviewParser()
    parser.parse_page_content(content)
    # parse user info
    content = cacher.get_page('self_user_info')
    p2 = UserInfoParser()
    p2.parse_page_content(content)
    # parse imperium
    p3 = ImperiumParser()
    content = cacher.get_page('imperium')
    p3.parse_page_content(content)

if __name__ == "__main__":
    main()
