#!/usr/bin/python3
from ui.xnova.xn_page_cache import XNovaPageCache
from ui.xnova.xn_parser_overview import OverviewParser
from ui.xnova.xn_parser_userinfo import UserInfoParser


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

if __name__ == "__main__":
    main()
