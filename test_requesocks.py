#!/usr/bin/python3
# requires:
#  - pysocks for socks5 proxy socket, required by requesocks
#  - certifi for HTTPS certificate validation, also used in depths of requesocks
#  - requesocks
import requesocks
import certifi


SOCKS5_PROXY = '127.0.0.1:9050'
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/45.0.2454.85 Safari/537.36'


def main():
    session = requesocks.session()
    session.proxies = {
        'http': 'socks5://{0}'.format(SOCKS5_PROXY),
        'https': 'socks5://{0}'.format(SOCKS5_PROXY)
    }
    session.headers.update({'user-agent': USER_AGENT})
    # url = 'http://yandex.ru/internet'
    # url = 'https://www.whatismyip.com/my-ip-information/'
    url = 'http://httpbin.org/ip'
    print('Using proxy: {0}'.format(SOCKS5_PROXY))
    print('Requesting URL: {0}'.format(url))
    r = session.get(url)
    if r.status_code == 200:
        text = r.text
        if text is None:
            if type(r.content) == bytes:
                text = r.content.decode('UTF-8')
        if text:
            print(text)
            with open('res.html', 'wt', encoding=r.encoding) as f:
                f.write(text)
    else:
        print('status code: {0}'.format(r.status_code))


if __name__ == '__main__':
    main()
