import html
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, NavigableString

# modified version of string punctuation
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~«»"""


# adding TRADE SYMBOL for 6 length word(without punctuation)
def modify_words(array):
    remove_punc = str.maketrans(punctuation, ' ' * len(punctuation))
    for i, word in enumerate(array):
        without_punc = word.translate(remove_punc)
        myarr = re.split(r'(\s+)', without_punc)
        for j, part in enumerate(myarr):
            if len(part) == 6:
                word = word.replace(part, part + html.unescape('&#8482;'))

        array[i] = word

    return ''.join(array)


# changes strings of all descendants(all children inside tag)
def change_in_tag(root):
    for desc in list(root.descendants):
        if isinstance(desc, NavigableString):
            arr = re.split(r'(\s+)', desc)  # re.split saves whitespaces as original
            newchild = modify_words(arr)
            desc.replace_with(newchild)


def modify_content_from_url(url, self):
    r = requests.get(url)

    if r.status_code == 200 and ("text/html" in r.headers["content-type"]):

        soup = BeautifulSoup(html.unescape(r.text), 'html.parser')

        # replace all habr links with localhost domain
        for link in soup.find_all('a', attrs={'href': re.compile("habrahabr.ru|habr.com")}):
            scheme, netloc, path, params, query, fragment = urlparse(link['href'])
            new_url = urlunparse(('http', 'localhost:3000', path, params, query, fragment))
            link['href'] = new_url
        with open("/home/zhasulan/Downloads/sometxt.txt", 'w') as f:
            f.write(html.unescape(r.text))

        layout = soup.find('div', attrs={'class': 'layout'})
        if layout:
            change_in_tag(layout)

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
            modify_content_from_url("https://habr.com", self)

        if self.path != '/':
            real_url = "https://habr.com" + self.path
            modify_content_from_url(real_url, self)


def run():
    port = 3000
    httpd = HTTPServer(('', port), SimpleHTTPRequestHandler)
    print("Running localhost: " + str(port))
    httpd.serve_forever()


if __name__ == "__main__":
    run()
