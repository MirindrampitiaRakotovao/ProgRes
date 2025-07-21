import socket
import threading
import select
from filter import is_blocked

BUFFER_SIZE = 4096
LISTEN_PORT = 8888
LOG_FILE = "logs.txt"

def log_event(text):
    print(text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def tunnel(client, remote):
    sockets = [client, remote]
    while True:
        ready, _, _ = select.select(sockets, [], [])
        for sock in ready:
            other = remote if sock is client else client
            try:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    client.close()
                    remote.close()
                    return
                other.send(data)
            except Exception:
                client.close()
                remote.close()
                return

def handle_client(client_socket, addr):
    try:
        request = client_socket.recv(BUFFER_SIZE)
        if not request:
            client_socket.close()
            return

        request_line = request.split(b'\r\n')[0].decode()
        method, url, protocol = request_line.split()
        host = ""
        port = 80

        log_event(f"[📡] Connexion de {addr} - {method} {url}")

        if method == 'CONNECT':
            host_port = url.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 443

            if is_blocked(host, ''):
                log_event(f"[✋ HTTPS] Bloqué : {host}")
                client_socket.send("HTTP/1.1 403 Forbidden\r\n\r\nSite bloqué par le proxy".encode('utf-8'))
                client_socket.close()
                return

            try:
                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_socket.connect((host, port))
                client_socket.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
                tunnel(client_socket, remote_socket)
            except Exception as e:
                log_event(f"[Erreur HTTPS] {e}")
            return

        else:
            # HTTP simple
            if "://" in url:
                host = url.split('/')[2]
            else:
                host = url.split('/')[0]

            if ':' in host:
                host, port = host.split(':')
                port = int(port)

            if is_blocked(host, url):
                log_event(f"[✋ HTTP] Bloqué : {host} - {url}")
                response = "HTTP/1.1 403 Forbidden\r\n\r\nSite bloqué par le proxy".encode('utf-8')
                client_socket.close()
                return

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((host, port))
            remote_socket.sendall(request)

            while True:
                data = remote_socket.recv(BUFFER_SIZE)
                if not data:
                    break
                client_socket.send(data)

            remote_socket.close()
            client_socket.close()

    except Exception as e:
        log_event(f"[Erreur générique] {e}")
        client_socket.close()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", LISTEN_PORT))
    server.listen(100)
    log_event(f"[🛡️] Proxy démarré sur le port {LISTEN_PORT}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    start_proxy()
