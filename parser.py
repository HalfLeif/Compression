import re
import requests

from html.parser import HTMLParser

ROOT_URL = "https://www.wordproject.org/"

RE_BOOK_URL = re.compile('^bibles/[a-z_]+/index.htm')
assert RE_BOOK_URL.match('bibles/no/index.htm')

RE_SUB_BOOK_URL = re.compile('^[0-9]+/[0-9]+.htm')

RE_WHITESPACE_ONLY = re.compile('^\\s+$')
assert RE_WHITESPACE_ONLY.match('\r\n  ')

class Accumulator(HTMLParser):
    def __init__(self, root_url):
        HTMLParser.__init__(self)
        self.root_url = root_url
        self.result = []

    def run(self):
        print(f'downloading {self.root_url}')
        web_root = requests.get(self.root_url)
        print('success')

        # Note: web_root.encoding says ISO-8859-1, but that's wrong.
        s = web_root.content.decode('utf-8')
        self.feed(s)
        return self.result

    # Methods to override from HTMLParser:
    #   def handle_starttag(self, tag, attrs):
    #   def handle_endtag(self, tag):
    #   def handle_data(self, data):


class RootParser(Accumulator):
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'href' in d:
            self.handle_url(d['href'])

    def handle_url(self, url):
        if RE_BOOK_URL.match(url):
            full_url = self.root_url + url
            # print("Encountered link:", full_url)
            self.result.append(full_url)


class BookParser(Accumulator):
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'href' in d:
            self.handle_url(d['href'])

    def handle_url(self, url):
        if RE_SUB_BOOK_URL.match(url):
            full_url = self.root_url.replace('index.htm', url)
            # print("Encountered sub book link:", full_url)
            self.result.append(full_url)


class ChapterParser(Accumulator):
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'href' in d and d.get('class') == 'chap':
            self.handle_url(d['href'])

    def handle_url(self, url):
        full_url = self.root_url.replace('1.htm', url)
        print("Encountered chapter link:", full_url)
        self.result.append(full_url)


class VerseParser(Accumulator):
    def __init__(self, root_url):
        Accumulator.__init__(self, root_url)
        self.capture = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get('class') == 'dimver':
            self.capture = True
        elif tag == 'div':
            self.capture = False

    def handle_data(self, data):
        if RE_WHITESPACE_ONLY.match(data):
            return
        if self.capture:
            print(data)


def download():
    # root = RootParser(ROOT_URL)
    # links = root.run()

    # book = BookParser('https://www.wordproject.org/bibles/de/index.htm')
    # sub_books = book.run()

    # chapter = ChapterParser('https://www.wordproject.org/bibles/de/24/1.htm')
    # chapter.run()

    verse = VerseParser('https://www.wordproject.org/bibles/de/24/43.htm#0')
    verse.run()

    # data = b'Nimm gro\\xc3\\x9fe Steine und vergrabe sie in dem Boden am Eingang des Hauses des Pharao in Tachpanches, so da\\xc3\\x9f die M\\xc3\\xa4nner aus Juda es sehen, \\r\\n'
    # # print(data)
    # print(data.decode('utf-8', 'strict'))


def main():
    download()

main()
