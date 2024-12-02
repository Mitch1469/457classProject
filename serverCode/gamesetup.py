import sys
import socket
import selectors
import serverlib
import json
import time
import threading
from collections import deque

"""Contains GameManager and GameSetup"""


class GameManager:
    """Tracks active games and allows for removal/addtion of games. Allows for access to information about
        the games
        """
    def __init__(self):
        self.games = deque() # Tracks active games

    def add_game(self, game): # adds games
        self.games.append(game)

    def remove_game(self, game): # removes games
        if game in self.games:
            self.games.remove(game)

    def find_game_by_connection(self, conn): # returns the game assoicated with a connection from a connPair
        for game in self.games:
            if game.conn1 == conn or game.conn2 == conn:
                return game
        return None

    def current_games(self): # Returns total number of games and names of the players in each game
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
    """This is the main driver of the game
    """
    def __init__(self, connPair, logger, game_manager): # Sets import variable for the game
        self.connPair = connPair # Used for refrencing both clients
        self.conn1 = connPair.conn1 # refrencing individual clienet 1
        self.conn2 = connPair.conn2 # refrencing individual clienet 2
        self.conn1_name = None # refrencing individual clienet 1
        self.conn2_name = None # refrencing individual clienet 2
        self.logger = logger
        self.game_active = False # tracks when the game starts and ends
        self.sel = selectors.DefaultSelector() # new selector for the specific game
        self.game_manager = game_manager 
        self.gamestate = None

    def start_game(self):
        """Start point for the game, registers the sockets with the game selector and starts the game_init"""
        self.sel.register(self.conn1, selectors.EVENT_READ, data=self.conn1)
        self.sel.register(self.conn2, selectors.EVENT_READ, data=self.conn2)
        self.connPair.set_sel(self.sel)
        self.logger.info("Starting game setup. Requesting usernames from players.")
        # Sends a message to the clients for usernames
        self.request_username(self.conn1, "Enter your username (Player 1):") 
        self.request_username(self.conn2, "Enter your username (Player 2):")
        self.game_active = True

        # delegates game_setup to serverlib proccess, variables retrieved from clients are still stored on gamesetup
        self.connPair.exchange_data()

                



    def request_username(self, conn, message): # Specific sendall for the usernames request
        conn.sendall(json.dumps({"msg_type": "request", "data": message}).encode('utf-8'))


    def broadcast(self, message): # Sends both sockets. Allows for easy access sendall
        self.conn1.sendall(message.encode('utf-8'))
        self.conn2.sendall(message.encode('utf-8'))
        self.logger.info(f"Broadcasting " + " " + message)

    def game_over(self, message): 
        """Game_over catch all, used for when the game is ended prematurely or upon completion
            Sends to all active sockets and allows for the removal of the game from the active games
            """
        self.logger.info(f"Game Over: {message}")
        quit_message = json.dumps({"msg_type": "gameover", "data": message})
        self.game_active = False

        def notify_and_cleanup(conn, player):
            # Threaded method that allows for sending the quit/game_over message concurrently with ending the game
            if conn:
                try:
                    # Attempt to send the game-over message
                    if conn.fileno() != -1:  # Check if the socket is still valid
                        conn.sendall(quit_message.encode('utf-8'))
                        self.logger.info(f"Game-over message sent to {player}")
                except (BrokenPipeError, ConnectionResetError, OSError) as e:
                    self.logger.warning(f"Failed to notify {player}: {e}")
                    self.sel.unregister(conn)
                finally:
                    try:
                        # Unregister and close the socket
                        if conn.fileno() != -1:
                            self.sel.unregister(conn)  # Unregister from the selector
                            self.logger.info(f"Connection closed for {player}")
                    except KeyError:
                        self.logger.warning(f"Socket for {player} was not registered in the selector.")
                    except OSError as e:
                        self.logger.error(f"Error while closing {player}'s connection: {e}")
        notify_and_cleanup(self.conn1, "Player 1")
        notify_and_cleanup(self.conn2, "Player 2")
        self.game_manager.remove_game(self) # removes from active games
        self.logger.info("Game state cleaned up.")



                    
    
    def turn_loop(self): # Main turn loop
        # Assigns which socket is associated with active turn
        turn, p_turn = self.connPair.conn1, self.connPair.conn1_name  
        not_turn, p_not_turn = self.connPair.conn2, self.connPair.conn2_name

        while True:
            """Driver for each turn sequence
                Player 1 starts and is asked for a coordinate
                Player2 is sent the guess and returns and answer
                if the answer contains a gamestate msg_type that indicates that all of their pieces are sunk
                otherwise the answer is sent to player 1 and the loop continues with the roles reversed"""
            self.logger.info(f"{turn}'s turn")
            move_message = json.dumps({"msg_type": "gameplay", "message": "Make your Move!", "data": "turn"})
            self.connPair.send_one(turn, move_message) # Sends turn notification
            guess_unfiltered = self.connPair.wait_for_response(turn) # Waits for results, result of wait_for is send through process_message for any non-game requests
            guess_unfiltered = json.loads(guess_unfiltered)
            guess = guess_unfiltered.get('data')
            self.connPair.send_one(not_turn, json.dumps({"msg_type": "gameplay", "message": guess, "data": "guess"})) # not_turn is sent turn's guess
            answer_unfiltered = self.connPair.wait_for_response(not_turn) # gets reponse on guess
            answer_unfiltered = json.loads(answer_unfiltered)
            if answer_unfiltered.get('msg_type') == "gamestate": # determines if reponse to guess involves a game_over
                over = f"{p_not_turn} has lost all their ships! {p_turn} has won!"
                self.game_over(over) # Ends game if gamestate is detected
                break
            answer = answer_unfiltered.get('data') # if response deosnt result in gameover, is sent to turn
            self.connPair.send_one(turn, json.dumps({"msg_type": "gameplay", "message": answer, "data": "answer", "guess": guess}))
            
            # Roles are reversed 
            turn, not_turn = not_turn, turn
            p_turn, p_not_turn = p_not_turn, p_turn


                                    