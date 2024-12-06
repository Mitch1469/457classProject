import socket
import selectors
import json

"""Contains the methods for sending and receiving information. This is initilized as an object with Gamesetup. 
    They refrence each other"""

class ServerLib:
    # Doubled on the variables for connection related tasks. Could be condensed into serverlib or gamesetup
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


    # Setters for placing variables in object
    def set_names(self):
        self.conn1_name = self.game.conn1_name
        self.conn2_name = self.game.conn2_name

    def set_sel(self, sel):
        self.sel = sel

    def set_game(self, game):
        self.game = game


    # Main entry port for information coming into the game
    def exchange_data(self):
        # Game initilization moved to exchange data to ensure the game loop doesnt move prematurely
        conn1_name = None # Variables to track the name of the players and wait till both names are submitted
        conn2_name = None
        conn1_set = None # variable that waits for the players to inform the server that they have set their boards and the main game loop can start
        conn2_set = None
        setup_phase = "waiting_for_names" # flag that determines what stage in setup the loop is at 

        while self.game.game_active: # Loop will continue while the game is listed as active
            print(self.game.conn1_name)
            events = self.sel.select(timeout=None) # No timeout as some setup actions can take a large amount of time
            # Generel purpose listener
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data != None: # Prints the screen any non empty data messages 
                            print(data)
                        if not data: # Catches unexpected disconnects 
                            self.logger.warning(f"Connection closed by client {conn.getpeername()}")
                            self.game.game_over("A player disconnected.")
                            return

                        message = json.loads(data.decode('utf-8')) # Loads any data recieved into json                      
                        msg_type = message.get('msg_type')

                        if setup_phase == "waiting_for_names": # 1st phase of setup, waits for both names
                            if msg_type == "join":
                                if conn == self.conn1 and not conn1_name: # determines which socket sent the name and assigns it to a variable
                                    self.game.conn1_name = message.get('data')
                                    self.logger.info(f"Player 1 username: {conn1_name}")
                                elif conn == self.conn2 and not conn2_name:
                                    self.game.conn2_name = message.get('data')
                                    self.logger.info(f"Player 2 username: {conn2_name}")
                            else: # Catches any non game initilization messages, such as quit messages
                                self.process_message(conn, message) 

                            if self.game.conn1_name and self.game.conn2_name: # Determines if the setup phase can advance
                                self.logger.info(f"Both players joined: {conn1_name}, {conn2_name}")
                                setup_phase = "waiting_for_pieces"
                                start_message = json.dumps({ # Message to tell the clients to move onto the next phase
                                "msg_type": "game_init",
                                "data": "Place Your Pieces",
                                "players": {
                                    "player1": self.game.conn1_name, # Assigns names to future use
                                    "player2": self.game.conn2_name
                                }
                            })
                                self.broadcast(start_message) # Sends setup advancement and player names to clients                       

                        if setup_phase == "waiting_for_pieces": # Next phase of the setup, waits for clients to confirm that their pieces have been set. Similar to previous stage
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
                                self.process_message(conn, message) # Catches non game setup
                        else:
                            self.process_message(conn, message) # Used for gameplay after the setup has completed

                    except ConnectionResetError as e:
                        self.logger.error(f"Connection reset by client {conn.getpeername()}: {e}")
                        self.game_over("A player disconnected.")
                        return
                    except Exception as e:
                        self.logger.error(f"Unexpected error: {e}")
                        self.game_over("An error occurred.")
                        return


    def broadcast(self, message): # Sends to both players
        self.conn1.sendall(message.encode('utf-8'))
        self.conn2.sendall(message.encode('utf-8'))

    def send_one(self, conn, message): # Sends to one client
        conn.sendall(message.encode('utf-8'))

    def process_message(self, conn, message): # Determines non-gamesetup and non-gameplay messages
        print(message) # Debugging and primitive logging of received messages
        msg_type = message.get('msg_type') # Gets the header of the json message
        if msg_type == "command": 
            if message.get('data') == "quit": # Recived when a player quits prematurely 
                self.logger.info(f"Player {conn.getpeername()} quit. Closing game.")
                quit_message = "Your opponent has left the game."
                self.game.game_over(quit_message) # Sends the message to the quit function for the specific quit reason


            if message.get('data') == "current_games": # Proccesses message requesting all current active games
                current_games = self.game.game_manager.current_games() # Method that retrieves the information
                current_games = json.dumps({"msg_type": "message", "data": current_games})
                conn.sendall(current_games.encode('utf-8')) # Sends to the requesting client
                self.logger.info(f"Player {conn.getpeername()} getting current games.")
            if message.get('data') == "partner_connections": # Proccess the clients specific game information. Names, addresses, etc.
                partner_connections = f"{self.conn1_name} ({self.conn1.getpeername()}) and {self.conn2_name} ({self.conn2.getpeername()})"
                partner_connections = json.dumps({"msg_type": "message", "data": partner_connections}).encode('utf-8')
                conn.sendall(partner_connections)
            else: # Ignores anything not explicitly defined 
                return

    def wait_for_response(self, conn): # Function that waits for a response from the clients
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

def start_server(host, port, sel): # starts the server, specifically the listener for new connections
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((host, port))
    server_sock.listen()
    server_sock.setblocking(False)
    sel.register(server_sock, selectors.EVENT_READ, data=None)
    print(f"Server started on {host}:{port}")

def accept_connection(sock): # Function that accepts a connection from a client. 
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    return conn, addr

