import itertools
import re
import requests
import threading

from html.parser import HTMLParser

ROOT_URL = "https://www.wordproject.org/"

RE_TRANSLATION_URL = re.compile('bibles/([a-z_]+)/index.htm')
assert RE_TRANSLATION_URL.match('bibles/no/index.htm')

RE_BOOK_URL = re.compile('^[0-9]+/[0-9]+.htm')

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
        # print('success')

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
        if RE_TRANSLATION_URL.match(url):
            full_url = self.root_url + url
            # print("Encountered link:", full_url)
            self.result.append(full_url)


class BookParser(Accumulator):
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == 'a' and 'href' in d:
            self.handle_url(d['href'])

    def handle_url(self, url):
        if RE_BOOK_URL.match(url):
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
        # print("Encountered chapter link:", full_url)
        self.result.append(full_url)


class VerseParser(Accumulator):
    def __init__(self, root_url, callback_fn):
        Accumulator.__init__(self, root_url)
        self.capture = False
        self.callback_fn = callback_fn

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if d.get('class') in ('textBody', 'textHeader'):
            self.capture = True
        elif tag == 'div' or d.get('class') == 'chap':
            self.capture = False

    def handle_data(self, data):
        if RE_WHITESPACE_ONLY.match(data):
            return
        if self.capture:
            self.callback_fn(data)


class MyThread(threading.Thread):
    def __init__(self, task_fn):
        threading.Thread.__init__(self)
        self.task_fn = task_fn
        self.result = None

    def run(self):
        self.result = self.task_fn()

class ThreadBundle():
    def __init__(self):
        self.threads = []

    def AddTask(self, task_fn):
        t = MyThread(task_fn)
        self.threads.append(t)
        t.start()

    def AddMany(self, xs, task_fn):
        for x in xs:
            self.AddTask(lambda: task_fn(x))

    def Join(self):
        results = []
        for t in self.threads:
            t.join()
            results.append(t.result)
        return results


def download_chapter(chapter_url):
    result = []
    VerseParser(chapter_url, lambda x: result.append(x)).run()
    return result


def download_book(book_url):
    # Chapter 1
    chapter_urls = [book_url]
    # Fetch the other chapters:
    chapter_urls += ChapterParser(book_url).run()

    bundle = ThreadBundle()
    bundle.AddMany(chapter_urls, download_chapter)
    return bundle.Join()


def download_translation(translation_url):
    m = RE_TRANSLATION_URL.search(translation_url)
    if not m:
        print('ERROR: no match for ', translation_url)
        return False
    translation = m.group(1)

    book_urls = BookParser(translation_url).run()
    if not book_urls:
        print('ERROR: no books found for', translation_url)
        return False

    found = False
    with open(f'data/{translation}.txt', 'w', encoding='utf-8') as out:
        for book_url in book_urls:
            ls = download_book(book_url)
            if not ls:
                print('ERROR: no data found for', book_url)
                return False

            content = ''.join(itertools.chain.from_iterable(ls))
            out.write(content)
            found = True
    return found


def download_all():
    for translation in RootParser(ROOT_URL).run():
        found = download_translation(translation)
        if found:
            return # TODO get all books

def main():
    download_all()

    # bundle = ThreadBundle()
    # bundle.AddMany([1,2,3,4,5,6,7], lambda x: x**2)
    # print(bundle.Join())

main()
