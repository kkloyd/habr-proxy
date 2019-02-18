import html
import re
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, NavigableString


# count punctuation in string/word (Ex: 'blog,.' has 2 punc )
def count_punc(s, punc):
    return sum([1 for x in s if x in punc])


# adding TRADE SYMBOL for 6 length word(without punctuation)
def modify_words(array):
    for i, word in enumerate(array):
        word = word.strip()
        c = count_punc(word, set(string.punctuation))
        if len(word) - c == 6:
            array[i] = word + html.unescape('&#8482;')

    return ''.join(array)


# changes strings of all descendants(all children inside tag)
def change_in_tag(root):
    for desc in list(root.descendants):
        if isinstance(desc, NavigableString):
            if desc.strip() != '':
                arr = re.split(r'(\s+)', desc)  # re.split saves whitespaces as original
                newchild = modify_words(arr)
                desc.replace_with(newchild)


def get_soup_from_request(url, self):
    r = requests.get(url)

    if r.status_code == 200 and ("text/html" in r.headers["content-type"]):

        soup = BeautifulSoup(r.text, 'html.parser')

        # replace all habr links with localhost
        for link in soup.find_all('a', attrs={'href': re.compile("habrahabr.ru|habr.com")}):
            scheme, netloc, path, params, query, fragment = urlparse(link['href'])
            new_url = urlunparse(('http', 'localhost:3000', path, params, query, fragment))
            link['href'] = new_url

        # for habr post list
        posts_lists = soup.find('div', attrs={'class': 'posts_lists'})
        if posts_lists:
            change_in_tag(posts_lists)

        # for habr full post view
        post_body = soup.find('article')
        if post_body:
            change_in_tag(post_body)

        self.wfile.write(bytes(str(soup), "utf-8"))

    elif r.status_code == 404:
        print("Error 404")


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    # GET method in python's http server
    def do_GET(self):
        self.set_headers()
        if self.path == '/':
            get_soup_from_request("https://habr.com", self)

        if self.path != '/':
            real_url = "https://habr.com" + self.path
            print(self.path)
            get_soup_from_request(real_url, self)


def run():
    port = 3000
    httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
    print("Running localhost: " + str(port))
    httpd.serve_forever()


if __name__ == "__main__":
    run()
