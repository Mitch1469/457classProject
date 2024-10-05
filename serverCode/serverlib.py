# serverlib.py
import socket
import selectors

class ServerLib:
    def __init__(self, conn1, addr1, conn2, addr2):
        self.conn1 = conn1
        self.addr1 = addr1
        self.conn2 = conn2
        self.addr2 = addr2
        self.responses = {conn1: None, conn2: None}
        self.conn1name = ""
        self.conn2name = ""
        print(f"Managing connections: {addr1} and {addr2}")
    
    def exchange_data(self):
        try:
            data1 = self.conn1.recv(1024)
            data2 = self.conn2.recv(1024)

            if data1:
                print(f"Received from {self.addr1}: {data1.decode()}")
                self.conn2.send(data1)  # Forward data from conn1 to conn2
            if data2:
                print(f"Received from {self.addr2}: {data2.decode()}")
                self.conn1.send(data2)  # Forward data from conn2 to conn1
        except Exception as e:
            print(f"Error: {e}")
            self.close()

    def close(self, sel, logger):
        print("Closing connections")
        sel.unregister(self.conn1)
        sel.unregister(self.conn2)
        self.conn1.close()
        self.conn2.close()
        logger.info(f"Closing connection to {self.conn1}")
        logger.info(f"Closing connection to {self.conn2}")

# Other functions that don't belong to the class
def start_server(host, port, sel):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    server_sock.setblocking(False)
    sel.register(server_sock, selectors.EVENT_READ, data=None)
    print(f"Server started on {host}:{port}")

def accept_connection(sock):
    conn, addr = sock.accept()  # Accept the new connection
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    return conn, addr

def wait_for_responses(connPair, sel):
    while None in connPair.responses.values():  
        events = sel.select()  
        for key, mask in events:
            conn = key.fileobj
            if mask & selectors.EVENT_READ:
                data = conn.recv(1024) 
                if data:
                    connPair.responses[conn] = data.decode('utf-8')
                    print(f"Received from {connPair.responses[conn]}")

def send_all(connPair, message):
    connPair.conn1.sendall(message.encode('utf-8'))
    connPair.conn2.sendall(message.encode('utf-8'))
