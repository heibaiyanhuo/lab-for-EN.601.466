import re
import sys
import time

from queue import PriorityQueue
from urllib import parse, request

from helper import RegType
from bs4 import BeautifulSoup

def get_links(base_url, html):
    soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8')
    for link in soup.find_all('a'):
        href = link.get('href')
        if href:
            text = link.string or ''
            text = re.sub('\s+', ' ', text).strip()
            yield parse.urljoin(base_url, href), text

def extract_information(url, content, writer=sys.stdout):
    for phone_info in RegType.PHONE.findall(content):
        info = '({}; PHONE; {})\n'.format(url, phone_info.strip())
        writer.write(info)

    for email_info in RegType.EMAIL.findall(content):
        info = '({}; EMAIL; {})\n'.format(url, email_info.strip())
        writer.write(info)

    for address_info in RegType.ADDRESS.findall(content):
        info = '({}; CITY; {})\n'.format(url, re.sub('\s+', ' ', address_info).strip())
        writer.write(info)


class LinkRover:

    def __init__(self, root_url, extract_information=lambda u, c, w: None):
        self.root_url = root_url
        self.extract_information = extract_information

        self._log_writer = open('traversal.log', 'w')
        self._content_writer = open('content.txt', 'w')

    def should_visit(self, url):
        return 'cs.jhu.edu' in parse.urlparse(url).netloc

    def is_non_local(self, to_url, from_url):
        return parse.urlparse(to_url).path != parse.urlparse(from_url).path

    def get_content_operation(self, content_type):
        if 'pdf' in content_type:
            return '__PRINT__'
        if 'text/html' in content_type:
            return '__TRAVERSAL__'
        return '__SKIP__'

    def start(self):
        visited = set()
        queue = PriorityQueue()

        queue.put((1, self.root_url))
        visited.add(self.root_url)

        while not queue.empty():
            priority, curr_url = queue.get()

            # if priority > 2: break

            try:
                response = request.urlopen(curr_url, timeout=5)
                if response.status == 200:
                    url_operation = self.get_content_operation(response.getheader('Content-Type'))
                    if url_operation == '__SKIP__':
                        continue
                    self._log_writer.write(curr_url + '\n')
                    self._log_writer.flush()
                    if url_operation == '__PRINT__':
                        print(curr_url)
                    elif url_operation == '__TRAVERSAL__':
                        html = response.read()
                        self.extract_information(curr_url, html.decode('utf-8'), self._content_writer)
                        self._content_writer.flush()
                        for url, text in get_links(curr_url, html):
                            if self.should_visit(url) and self.is_non_local(url, curr_url) and url not in visited:
                                next_priority = priority + 1
                                queue.put((next_priority, url))
                                visited.add(url)
            except Exception as e:
                print(e, curr_url)
            time.sleep(0.1)
        self.close()

    def close(self):
        self._log_writer.close()
        self._content_writer.close()

if __name__ == '__main__':
    root_url = sys.argv[1]
    rover = LinkRover(root_url, extract_information)

    # response = request.urlopen(root_url)
    # for l in get_links(root_url, response.read()):
    #     print(l)
    # extract_information(url, response.read().decode('utf-8'))

    rover.start()