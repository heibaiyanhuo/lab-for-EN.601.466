import sys
import urllib.request
import urllib.parse
from html.parser import HTMLParser

class ImgParser(HTMLParser):

    def __init__(self, base_url):
        super(ImgParser, self).__init__()
        self.base_url = base_url
        self.path = urllib.parse.urlparse(base_url).path

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for attr, val in attrs:
                if attr == 'src':
                    abs_url = urllib.parse.urljoin(self.base_url, val)
                    if urllib.parse.urlparse(abs_url).path != self.path:
                        print(abs_url)
                    break


if __name__ == '__main__':
    url = sys.argv[1]
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')

    lwp_parser = ImgParser(url)
    lwp_parser.feed(html)