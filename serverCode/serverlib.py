import socket
import selectors
import json

"""Contains the methods for sending and receiving information accross the """

class ServerLib:
    def __init__(self, conn1, addr1, conn2, addr2, logger):
        self.conn1 = conn1
        self.addr1 = addr1
        self.conn2 = conn2
        self.addr2 = addr2
        self.logger = logger
        self.game = None
        self.sel = None
        self.conn1_name = None
        self.conn2_name = None

    def set_names(self):
        self.conn1_name = self.game.conn1_name
        self.conn2_name = self.game.conn2_name

    def set_sel(self, sel):
        self.sel = sel

    def set_game(self, game):
        self.game = game

    def exchange_data(self):
        conn1_name = None
        conn2_name = None
        conn1_set = None
        conn2_set = None
        setup_phase = "waiting_for_names"  

        while self.game.game_active:
            print(self.game.conn1_name)
            events = self.sel.select(timeout=None)
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data != None:
                            print(data)
                        if not data:
                            self.logger.warning(f"Connection closed by client {conn.getpeername()}")
                            self.game.game_over("A player disconnected.")
                            return

                        message = json.loads(data.decode('utf-8'))                      
                        msg_type = message.get('msg_type')

                        if setup_phase == "waiting_for_names":
                            if msg_type == "join":
                                if conn == self.conn1 and not conn1_name:
                                    self.game.conn1_name = message.get('data')
                                    self.logger.info(f"Player 1 username: {conn1_name}")
                                elif conn == self.conn2 and not conn2_name:
                                    self.game.conn2_name = message.get('data')
                                    self.logger.info(f"Player 2 username: {conn2_name}")
                            else:
                                self.process_message(conn, message)

                            if self.game.conn1_name and self.game.conn2_name:
                                self.logger.info(f"Both players joined: {conn1_name}, {conn2_name}")
                                setup_phase = "waiting_for_pieces"
                                start_message = json.dumps({
                                "msg_type": "game_init",
                                "data": "Place Your Pieces",
                                "players": {
                                    "player1": self.game.conn1_name,
                                    "player2": self.game.conn2_name
                                }
                            })
                                self.set_names()
                                self.broadcast(start_message)                        

                        if setup_phase == "waiting_for_pieces":
                            if msg_type == "game_init":
                                if conn == self.conn1 and not conn1_set:
                                    conn1_set = message.get('data')
                                    self.logger.info(f"Player 1 set: {conn1_set}")
                                elif conn == self.conn2 and not conn2_set:
                                    conn2_set = message.get('data')
                                    self.logger.info(f"Player 2 set: {conn2_set}")

                            if conn1_set and conn2_set:
                                self.logger.info("Both players placed their pieces. Starting the game.")
                                self.game.turn_loop()

                            else:
                                self.process_message(conn, message)
                        else:
                            self.process_message(conn, message)

                    except ConnectionResetError as e:
                        self.logger.error(f"Connection reset by client {conn.getpeername()}: {e}")
                        self.game_over("A player disconnected.")
                        return
                    except Exception as e:
                        self.logger.error(f"Unexpected error: {e}")
                        self.game_over("An error occurred.")
                        return


    def broadcast(self, message):
        self.conn1.sendall(message.encode('utf-8'))
        self.conn2.sendall(message.encode('utf-8'))

    def send_one(self, conn, message):
        conn.sendall(message.encode('utf-8'))

    def process_message(self, conn, message):
        print(message)
        msg_type = message.get('msg_type')
        if msg_type == "chat":
            other_conn = self.conn2 if conn == self.conn1 else self.conn1
            other_conn.sendall(json.dumps({"msg_type": "chat", "data": message['data']}).encode('utf-8'))

        if msg_type == "command":
            if message.get('data') == "quit":
                self.logger.info(f"Player {conn.getpeername()} quit. Closing game.")
                quit_message = "Your opponent has left the game."
                self.game.game_over(quit_message)


            if message.get('data') == "current_games":
                current_games = self.game.game_manager.current_games()
                current_games = json.dumps({"msg_type": "message", "data": current_games})
                conn.sendall(current_games.encode('utf-8'))
                self.logger.info(f"Player {conn.getpeername()} getting current games.")
            if message.get('data') == "partner_connections":
                partner_connections = f"{self.conn1_name} ({self.conn1.getpeername()}) and {self.conn2_name} ({self.conn2.getpeername()})"
                partner_connections = json.dumps({"msg_type": "message", "data": partner_connections}).encode('utf-8')
                conn.sendall(partner_connections)
            else:
                return

    def wait_for_response(self, conn):
        while True:
            events = self.sel.select(timeout=None)  
            for key, mask in events:
                if key.fileobj == conn and mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024) 
                        if data:
                            message = data.decode('utf-8')
                            print(message)
                            self.process_message(conn, json.loads(message))
                            return message  
                    except ConnectionResetError as e:
                        self.logger.error(f"Connection reset by client {conn.getpeername()}: {e}")
                        self.close_game()
                        return None, None
                    except Exception as e: 
                        self.logger.error(f"Unexpected error in wait_for_both: {e}")
                        self.close_game()
                        return None, None

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

