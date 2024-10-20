import sys
import socket
import selectors
import serverlib
import json
import time

class GameManager:
    def __init__(self):
        self.games = []

    def add_game(self, game):
        self.games.append(game)

    def remove_game(self, game):
        if game in self.games:
            self.games.remove(game)

    def find_game_by_connection(self, conn):
        for game in self.games:
            if game.conn1 == conn or game.conn2 == conn:
                return game
        return None

    def current_games(self):
        if not self.games:
            return "No active games at the moment."
        
        current_games_list = []
        for game in self.games:
            game_info = f"Game between {game.conn1_name} and {game.conn2_name}"
            current_games_list.append(game_info)

        total_games = len(current_games_list)
        current_games_string = "\n".join(current_games_list)
        return f"There are {total_games} active game(s):\n{current_games_string}"


class GameSetup:
    def __init__(self, connPair, sel, logger, game_manager):
        self.conn1 = connPair.conn1
        self.conn2 = connPair.conn2
        self.conn1_name = None
        self.conn2_name = None
        self.logger = logger
        self.game_active = False
        self.sel = sel
        self.game_manager = game_manager
        self.game_manager.add_game(self)

    def start_game(self):
        self.logger.info("Starting game setup, asking for usernames.")
        self.request_username(self.conn1, "Enter your username (Player 1):")
        self.request_username(self.conn2, "Enter your username (Player 2):")

        self.conn1_name, self.conn2_name = self.wait_for_both_usernames(self.sel)
        self.logger.info(f"Player 1: {self.conn1_name}, Player 2: {self.conn2_name}")
        self.game_active = True
        json_message = json.dumps({"msg_type": "message", "data": f"Game starting! Player 1: {self.conn1_name}, Player 2: {self.conn2_name}"})

        self.broadcast(json_message)

        time.sleep(0.1)

        json_startmessage = json.dumps({"msg_type": "game_init", "data": "Place Your Pieces"})
        self.broadcast(json_startmessage)



    def request_username(self, conn, message):
        conn.sendall(json.dumps({"msg_type": "request", "data": message}).encode('utf-8'))

    def process_message(self, conn, message):
        try:
            message_json = json.loads(message)
            msg_type = message_json.get('msg_type')

            if msg_type == "chat":
                other_conn = self.conn2 if conn == self.conn1 else self.conn1
                other_conn.sendall(json.dumps({"msg_type": "chat", "data": message_json['data']}).encode('utf-8'))

            elif msg_type == "command":
                if message_json.get('data') == "quit":
                    self.logger.info(f"Player {conn.getpeername()} quit. Closing game.")
                    self.close_game()
                if message_json.get('data') == "current_games":
                    current_games = self.game_manager.current_games()
                    current_games = json.dumps({"msg_type": "message", "data": current_games}).encode('utf-8')
                    conn.sendall(current_games)
                    self.logger.info(f"Player {conn.getpeername()} getting current games.")
                if message_json.get('data') == "partner_connections":
                    partner_connections = f"{self.conn1_name} ({self.conn1.getpeername()}) and {self.conn2_name} ({self.conn2.getpeername()})"
                    partner_connections = json.dumps({"msg_type": "message", "data": partner_connections}).encode('utf-8')
                    conn.sendall(partner_connections)

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def broadcast(self, message):
        self.conn1.sendall(message.encode('utf-8'))
        self.conn2.sendall(message.encode('utf-8'))
        self.logger.info(f"Broadcasting " + " " + message)

 

    def close_game(self):
        self.logger.info("Closing game connections.")
        quit_message = json.dumps({"msg_type": "quit", "data": "The other player has left the game."})
        try:
            if self.conn1:
                self.conn1.sendall(quit_message.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Failed to send quit message to Player 1: {e}")

        try:
            if self.conn2:
                self.conn2.sendall(quit_message.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Failed to send quit message to Player 2: {e}")
        time.sleep(0.1)
        try:
            self.conn1.close()
        except Exception as e:
            self.logger.error(f"Failed to close Player 1 connection: {e}")

        try:
            self.conn2.close()
        except Exception as e:
            self.logger.error(f"Failed to close Player 2 connection: {e}")

        self.game_active = False
        self.game_manager.remove_game(self)

    def wait_for_both_usernames(self, sel):
        conn1_name = None
        conn2_name = None

        while not (conn1_name and conn2_name):
            events = sel.select(timeout=None)
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            if message.get('msg_type') == 'join':
                                if conn == self.conn1 and not conn1_name:
                                    conn1_name = message.get('data')
                                    self.logger.info(f"Player 1 username: {conn1_name}")
                                elif conn == self.conn2 and not conn2_name:
                                    conn2_name = message.get('data')
                                    self.logger.info(f"Player 2 username: {conn2_name}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error decoding message: {e}")
                    except ConnectionResetError as e:
                        self.logger.error(f"Connection reset by client: {e}")
                        self.close_game()

        return conn1_name, conn2_name

    def exchange_data(self):
        while self.game_active:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data:
                            self.process_message(conn, data.decode('utf-8'))
                        else:
                            self.close_game()
                    except Exception as e:
                        self.logger.error(f"Error in data exchange: {e}")
                        self.close_game()
