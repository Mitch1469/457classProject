import sys
import socket
import selectors
import serverlib
import json
import time
import threading

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
        self.gamestate = None

    def start_game(self):
        self.logger.info("Starting game setup, asking for usernames.")
        self.request_username(self.conn1, "Enter your username (Player 1):")
        self.request_username(self.conn2, "Enter your username (Player 2):")

        self.conn1_name, self.conn2_name = self.wait_for_both(self.sel)
        self.logger.info(f"Player 1: {self.conn1_name}, Player 2: {self.conn2_name}")
        self.game_active = True
        json_message = json.dumps({"msg_type": "message", "data": f"Game starting! Player 1: {self.conn1_name}, Player 2: {self.conn2_name}"})

        self.broadcast(json_message)

        time.sleep(0.1)

        json_startmessage = json.dumps({"msg_type": "game_init", "data": "Place Your Pieces"})
        self.broadcast(json_startmessage)

        set1, set2 = self.wait_for_both(self.sel)

        self.turn_loop()

                



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

    def game_over(self, message):
        self.logger.info(f"Game Over: {message}")
        quit_message = json.dumps({"msg_type": "gameover", "data": message})
        self.game_active = False  

        def notify_and_close(conn, player):
            if conn:
                try:
                    conn.sendall(quit_message.encode('utf-8'))
                    self.logger.info(f"Sent game-over message to {player}")
                except Exception as e:
                    self.logger.error(f"Failed to send game-over message to {player}: {e}")
                finally:
                    try:
                        conn.shutdown(socket.SHUT_RDWR) 
                        conn.close()
                        self.logger.info(f"Closed connection for {player}")
                    except Exception as e:
                        self.logger.error(f"Failed to close connection for {player}: {e}")


        threads = []
        threads.append(threading.Thread(target=notify_and_close, args=(self.conn1, "Player 1")))
        threads.append(threading.Thread(target=notify_and_close, args=(self.conn2, "Player 2")))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.game_active = False
        self.game_manager.remove_game(self)
        self.logger.info("Game connections closed and game removed from manager.")


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

    def wait_for_both(self, sel):
        conn1_data = None
        conn2_data = None

        while not (conn1_data and conn2_data):
            events = sel.select(timeout=None)
            for key, mask in events:
                conn = key.fileobj
                if mask & selectors.EVENT_READ:
                    try:
                        data = conn.recv(1024)
                        if data:
                            message = json.loads(data.decode('utf-8'))
                            if message.get('msg_type') == 'join':
                                if conn == self.conn1 and not conn1_data:
                                    conn1_data = message.get('data')
                                    self.logger.info(f"Player 1 username: {conn1_data}")
                                elif conn == self.conn2 and not conn2_data:
                                    conn2_data = message.get('data')
                                    self.logger.info(f"Player 2 username: {conn2_data}")
                            if message.get('msg_type') == 'game_init':
                                if conn == self.conn1 and not conn1_data:
                                    conn1_data = message.get('data')
                                    self.logger.info(f"Player 1 set: {conn1_data}")
                                elif conn == self.conn2 and not conn2_data:
                                    conn2_data = message.get('data')
                                    self.logger.info(f"Player 2 set: {conn2_data}")
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error decoding message: {e}")
                    except ConnectionResetError as e:
                        self.logger.error(f"Connection reset by client: {e}")
                        self.close_game()

        return conn1_data, conn2_data
    

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
                            return message  
                    except Exception as e:
                        self.logger.error(f"Error receiving response: {e}")
                        return None
                    
    
    def turn_loop(self):
        turn, p_turn = self.conn1, self.conn1_name  
        not_turn, p_not_turn = self.conn2, self.conn2_name
        while True:
            self.logger.info(f"{turn}'s turn")
            move_message = json.dumps({"msg_type": "gameplay", "message": "Make your Move!", "data": "turn"})
            turn.sendall(move_message.encode('utf-8'))
            guess_unfiltered = self.wait_for_response(turn)
            guess_unfiltered = json.loads(guess_unfiltered)
            guess = guess_unfiltered.get('data')
            not_turn.sendall(json.dumps({"msg_type": "gameplay", "message": guess, "data": "guess"}).encode('utf-8'))
            answer_unfiltered = self.wait_for_response(not_turn)
            answer_unfiltered = json.loads(answer_unfiltered)
            if answer_unfiltered.get('gamestate'):
                over = f"{p_not_turn} has lost all their ships! {p_turn} has won!"
                self.game_over(over)
                break
            answer = answer_unfiltered.get('data')
            turn.sendall(json.dumps({"msg_type": "gameplay", "message": answer, "data": "answer", "guess": guess}).encode('utf-8'))
            turn, not_turn = not_turn, turn
            p_turn, p_not_turn = p_not_turn, p_turn

                                    