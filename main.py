import html
import re
import string
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import argv
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


# count punctuation in string/word (Ex: 'blog,.' has 2 punc )
def count_punc(s, punc):
    return sum([1 for x in s if x in punc])


# adding TRADE SYMBOL for 6 length word(without punctuation)
def modify_words(array):
    for i, word in enumerate(array):
        c = count_punc(word, set(string.punctuation))
        if len(word) - c == 6:
            array[i] = word + html.unescape('&#8482;')

    return ' '.join(array)


# replace text and child tag's text
def replace_tag(root):
    mytext = ''
    for child in root.children:
        if isinstance(child, NavigableString) and len(root.contents) == 1:
            arr = child.split()
            newchild = modify_words(arr)
            root.string.replace_with(newchild)
            mytext += " " + str(root)
        elif isinstance(child, NavigableString):
            arr = child.split()
            newchild = modify_words(arr)
            mytext += " " + newchild
        elif isinstance(child, Tag):
            if len(child) == 0:
                mytext += str(child)
            else:
                mytext += " " + replace_tag(child)

    return mytext


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, url, *args, **kwargs):
        self.url = url
        super().__init__(*args, **kwargs)

    def set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def no_cache(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    # GET method in python's http server
    def do_GET(self):

        if self.path == '/' and self.url:
            url_parse_result = urlparse(self.url)

            if url_parse_result.scheme == 'https' or url_parse_result.scheme == 'http':

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.no_cache()
                self.send_header('Location', url_parse_result.path)
                self.end_headers()
            else:
                print('Invalid URL')

        if self.path != '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.no_cache()
            self.end_headers()

            real_url = "https://habr.com" + self.path

            r = requests.get(real_url)

            if r.status_code == 200 and ("text/html" in r.headers["content-type"]):
                soup = BeautifulSoup(r.text, 'html.parser')
                for script in soup(["script", "style"]):
                    script.decompose()  # rip it out

                # replace all habr links with localhost
                for link in soup.find_all('a', attrs={'href': re.compile("habrahabr.ru|habr.com")}):
                    scheme, netloc, path, params, query, fragment = urlparse(link['href'])
                    new_url = urlunparse(('http', 'localhost:3000', path, params, query, fragment))
                    link['href'] = new_url

                title = soup.find('span', {'class': 'post__title-text'})
                title_arr = title.text.split()
                title.string.replace_with(modify_words(title_arr))

                post_body = soup.find('div', {'class': 'post__text post__text-html js-mediator-article'})

                new_post_body = "<div class='post__text post__text-html js-mediator-article'>" + str(
                    BeautifulSoup(replace_tag(post_body), 'html.parser')) + "</div>"

                post_body.replace_with(BeautifulSoup(new_post_body, 'html.parser'))

                self.wfile.write(bytes(str(soup), "utf-8"))
            elif r.status_code == 404:
                print("Error 404")


def run(url):
    port = 3000
    handler = partial(SimpleHTTPRequestHandler, url)
    httpd = HTTPServer(('', port), handler)
    print("Running localhost: " + str(port))
    httpd.serve_forever()


if __name__ == "__main__":
    print(argv)
    if len(argv) == 2:
        run(str(argv[1]))
    else:
        url = 'http://habr.com/ru/company/yandex/blog/258673/'  # default url
        run(url)
