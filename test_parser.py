from ui.xn_page_cache import XNovaPageCache
from ui.xn_parser import OverviewParser


def main():
    # load file
    cacher = XNovaPageCache()
    cacher.load_from_disk_cache(clean=True)
    content = cacher.get_page('overview')
    # parse
    parser = OverviewParser()
    parser.parse_page_content(content)

if __name__ == "__main__":
    main()
