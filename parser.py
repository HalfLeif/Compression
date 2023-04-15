import re
import requests

from html.parser import HTMLParser

ROOT_URL = "https://www.wordproject.org/"

RE_BOOK_URL = re.compile('^bibles/[a-z_]+/index.htm')
assert RE_BOOK_URL.match('bibles/no/index.htm')

RE_SUB_BOOK_URL = re.compile('^[0-9]+/[0-9]+.htm')


class Accumulator(HTMLParser):
    def __init__(self, root_url):
        HTMLParser.__init__(self)
        self.root_url = root_url
        self.result = []

    def run(self):
        print(f'downloading {self.root_url}')
        web_root = requests.get(self.root_url)
        print('success')
        self.feed(str(web_root.content))
        return self.result

    # def handle_starttag(self, tag, attrs):
    #     return

    # def handle_endtag(self, tag):
    #     print("Encountered an end tag :", tag)

    # def handle_data(self, data):
    #     print("Encountered some data  :", data)


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
    def handle_starttag(self, tag, attrs):
        pass


def download():
    # root = RootParser(ROOT_URL)
    # links = root.run()

    # book = BookParser('https://www.wordproject.org/bibles/de/index.htm')
    # sub_books = book.run()

    chapter = ChapterParser('https://www.wordproject.org/bibles/de/24/1.htm')
    chapter.run()


def main():
    download()

main()
