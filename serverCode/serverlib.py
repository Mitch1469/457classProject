import socket
import selectors
import json
import queue

class ServerLib:
    def __init__(self, conn1, addr1, conn2, addr2, logger):
        self.conn1 = conn1
        self.addr1 = addr1
        self.conn2 = conn2
        self.addr2 = addr2
        self.logger = logger
        self.game = None
        self.message_queues = {
            conn1: queue.Queue(),
            conn2: queue.Queue()
        }

    def set_game(self, game):
        self.game = game

    def store_message(self, conn, message):
        if conn in self.message_queues:
            self.message_queues[conn].put(message)

    def retrieve_message(self, conn):
        if conn in self.message_queues and not self.message_queues[conn].empty():
            return self.message_queues[conn].get()
        return None

    def exchange_data(self, sel):
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data:
                            print(data)
                            message = data.decode('utf-8')
                            self.store_message(conn, message)
                            if self.game:
                                self.game.process_message(conn, message)
                        else:
                            self.close(sel)
                            return
                    except ConnectionResetError:
                        self.close(sel)

    def close(self, sel):
        print("Closing connections")
        try:
            sel.unregister(self.conn1)
            self.conn1.close()
        except Exception as e:
            self.logger.error(f"Failed to close conn1: {e}")

        try:
            sel.unregister(self.conn2)
            self.conn2.close()
        except Exception as e:
            self.logger.error(f"Failed to close conn2: {e}")

        self.logger.info(f"Connections to {self.addr1} and {self.addr2} closed.")

def send_all(conn1, conn2, message):
    if isinstance(message, str):
        message = {"msg_type": "message", "data": message}
    json_message = json.dumps(message)
    try:
        conn1.sendall(json_message.encode('utf-8'))
        conn2.sendall(json_message.encode('utf-8'))
    except Exception as e:
        print(f"Error sending message: {e}")

def start_server(host, port, sel):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    server_sock.setblocking(False)
    sel.register(server_sock, selectors.EVENT_READ, data=None)
    print(f"Server started on {host}:{port}")

def accept_connection(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    return conn, addr
