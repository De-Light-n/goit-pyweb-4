import urllib.parse as urlprs
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
from pathlib import Path
import mimetypes
import json
from datetime import datetime
import logging
from threading import Thread

BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000

class Framework(BaseHTTPRequestHandler):
    
    def do_GET(self):
        pr_url = urlprs.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)
                    
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
            
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()
    
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())
        
        
        
def run_http_serv(host, port):
    address = (host, port)
    http_server = HTTPServer(address, Framework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()
        
def run_socket_serv(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket received {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()
        
def save_data_from_form(data):
    parse_data = urlprs.unquote_plus(data.decode())
    try:
        data_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        
        file_path = Path("storage/data.json")
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        else:
            data = {}
        data[current_time] = data_dict
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)
        
        
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server = Thread(target=run_http_serv, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_serv, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()