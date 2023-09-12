import configparser
import datetime
import json
import mimetypes
import pathlib
import socket
import urllib
import urllib.parse

from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

config = configparser.ConfigParser()
config.read("data/config.ini")

http_host = config.get("HTTP", "host")
http_port = int(config.get("HTTP", "port"))
udp_host = config.get("UDP", "host")
udp_port = int(config.get("UDP", "port"))

BASE_DIR = pathlib.Path()
ASSETS_DIR = BASE_DIR / "assets"
STORAGE = BASE_DIR / "storage" / "data.json"

class HTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if url.path == '/':
            self.send_static("index.html")
        elif url.path == "/message":
            self.send_static("message.html")
        else:
            self.send_static(url.path[1:])

    def do_POST(self):
        # self.send_response(302)
        # self.send_header('Location', '/')
        # self.end_headers()
        self.send_response(302)
        self.send_header('Location', self.path)
        self.end_headers()

        data = self.rfile.read(int(self.headers['Content-Length']))
        # print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        # print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        # print(data_dict)
        data = json.dumps(data_dict)
        message = data.encode()
        client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # client_socket.connect((udp_host, udp_port))
        client_socket.sendto(message, (udp_host, udp_port))
        # client_socket.close()

    def send_static(self, name, status=200):
        filename = ASSETS_DIR / name
        if filename.exists():
            self.send_response(status)
            mt = mimetypes.guess_type(filename)
            if mt:
                self.send_header("Content-type", mt[0])
            else:
                self.send_header("Content-type", "text/plain")
            self.end_headers()
            with open(filename, "rb") as fd:
                self.wfile.write(fd.read())
        else:
            self.send_static(ASSETS_DIR / "error.html", 404)

class StorageServer(Thread):

    def __init__(self, address):
        super().__init__()
        self.address = address

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(self.address)
        # sock.listen(1)
        # conn, address = sock.accept()
        while True:
            data, address = sock.recvfrom(1024)
            timestamp = datetime.datetime.now()
            decoded = data.decode()
            data_dict = json.loads(decoded)
            data = {}
            data[str(timestamp)] = data_dict
            sdata = json.dumps(data)
            with open(STORAGE, "a") as fd:
                fd.writelines(sdata)
                fd.write('\n')
            # continue
            # print(f'Received data: {data.decode()} from: {address}')
            # sock.sendto(data, address)
            # print(f'Send data: {data.decode()} to: {address}')

def main():
    # try:
    http = HTTPServer((http_host, http_port), HTTPHandler)
    httpd = Thread(target=http.serve_forever)
    httpd.start()

    nassd = StorageServer((udp_host, udp_port))
    nassd.start()

    httpd.join()
    nassd.join()

    # except KeyboardInterrupt:
    #     print(f'Destroy server')
    # finally:
    #     sock.close()
if __name__ == "__main__":
    main()
