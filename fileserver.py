#!/usr/bin/env python3

from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler
from hash_zip import hash_zip
import argparse, yaml, re, ssl, os, sys, json
from functools import partial

class HTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, routes, providers_subpath, *args, **kwargs):
        self.routes = routes
        self.providers_subpath = providers_subpath
        super(HTTPHandler, self).__init__(*args, **kwargs)

    def translate_path(self, path, base_dir=False):
        if path.startswith(self.providers_subpath):
            path = path.split(self.providers_subpath, 1)[1]
        for route in self.routes:
            if path.startswith(route):
                subpath = ''
                if not base_dir:
                    subpath = path[len(route):]
                path = self.routes[route] + subpath
                break
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath

    def set200(self, response=""):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(response.encode('UTF-8')))

    def set404(self):
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes('{}'.encode('UTF-8')))

    def set500(self):
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes('{}'.encode('UTF-8')))

    # Terraform uses index.json to get available versions for selected provider (https://<hostname>/<providers>/registry.terraform.io/hashicorp/aci/index.json).
    # The next query selects specific version of  terraform provider (https://<hostname>/<providers>/registry.terraform.io/hashicorp/aci/2.0.1.json) which
    # returns available archives to download (platform specific) and calculated hashes of their contents.
    # After that it gets the provider's archive.
    # --
    # If the path doesn't contain providers_subpath, do_GET serves like in a regular HTTP file server.
    def do_GET(self):
        if self.path.startswith(self.providers_subpath):
            target = self.path.rsplit('/', 1)[1]
            if target == 'index.json':
                versions = {}
                try:
                    for version in os.listdir(self.translate_path(self.path, True)):
                        versions[version] = {}
                except FileNotFoundError:
                    self.set404()
                    return
                except Exception as e:
                    print(str(e))
                    self.set500()
                    return
                response = {}
                response['versions'] = versions
                self.set200(str(json.dumps(response)))
                return
            elif re.match('.*\.json', target):
                target_version = target.rsplit('.', 1)[0]
                if target_version in os.listdir(self.translate_path(self.path, True)):
                    response = {}
                    archives = {}
                    dir = self.translate_path(self.path, True) + '/' + target_version + '/'

                    try:
                        for file in os.listdir(dir):
                            if re.match('.*\.zip', file):
                                platform = file.rsplit('.zip', 1)[0]
                                platform = platform.rsplit('_', 2)[1] + '_' + platform.rsplit('_', 1)[1]
                                archives[platform] = {}
                                archives[platform]['hashes'] = [hash_zip(dir + file)]
                                archives[platform]['url'] = target_version + '/' + file
                    except FileNotFoundError:
                        self.set404()
                        return
                    except Exception as e:
                        print(str(e))
                        self.set500()
                        return

                    response['archives'] = archives
                    self.set200(str(json.dumps(response)))
                    return
            elif re.match('.*\.zip', target):
                SimpleHTTPRequestHandler.do_GET(self)
                return

            self.set404()
            return
        else:
            return SimpleHTTPRequestHandler.do_GET(self)


class HTTPServer(BaseHTTPServer):
    def __init__(self, base_path, server_address, RequestHandlerClass):
        self.base_path = base_path
        BaseHTTPServer.__init__(self, server_address, RequestHandlerClass)


def get_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', type=str, default='config.yaml')
    parser.add_argument('-d', '--directory', type=str, default='files')
    parser.add_argument('-H', '--host', type=str, default='localhost')
    parser.add_argument('-p', '--port', type=int, default=80)
    parser.add_argument('--providers-subpath', type=str, default='/providers/')
    parser.add_argument('--ssl-enabled', type=bool, default=False)
    parser.add_argument('--ssl-check-hostname', type=bool, default=False)
    parser.add_argument('--ssl-server-cert', type=str, default='server-cert.pem')
    parser.add_argument('--ssl-server-cert-key', type=str, default='server-key.pem')

    return vars(parser.parse_args())


if __name__ == '__main__':

    c = get_args(sys.argv[1:])

    c["routes"] = {}
    with open(c["config_file"], 'r') as f:
        conf = yaml.safe_load(f)
        for key in ['routes', 'host', 'port', 'directory', 'providers_subpath',
                    'ssl_enabled', 'ssl_check_hostname', 'ssl_server_cert', 'ssl_server_cert_key']:
            try:
                c[key] = conf[key]
            except KeyError:
                pass

    web_dir = os.path.join(os.path.dirname(__file__), c["directory"])
    httpd = HTTPServer(web_dir, (c["host"], c["port"]), partial(HTTPHandler, c["routes"], c["providers_subpath"]))
    if c["ssl_enabled"]:
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = c["ssl_check_hostname"]
        ssl_context.load_cert_chain(certfile=c['ssl_server_cert'], keyfile=c['ssl_server_cert_key'])
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()
