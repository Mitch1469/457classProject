import clientlib
import gameStatics
from GameStateClient import GameStateClient
from GameStateClient import GameSession


import logging
import os
import json
import argparse
import threading
import socket
import signal


"""This contains the main game loop. All other classes are called and interacted with from here. This is a 
    response driven program. The gameplay loop will not continue without input from the server. This creates
    some issues with playe actions hat take time and for receiving server commands like game over or 
    other various server information"""

#Creates a variable that will host all GameSession related variables
#gameVars = None


def global_ctrl_c_handler(sig, frame):
    """This function allows for handling the abrubt end of the program, it sets events for threads and sends a quit
        message to the server before closing the socket"""
    logging.info("Ctrl+C detected. Performing global cleanup...")
    gameVar.stop_event.set()
    trigger_signal(gameVar.signal_sock_send)  # Signal any blocking `wait_for_message`.
    clientlib.close_socket(gameVar.conn) # Current iteration does throw errors as server ends the socket before the client


# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, global_ctrl_c_handler)

# This sends an internal signal to wake up the threaded listner method and continue its loop
def trigger_signal(signal_sock_send):
    signal_sock_send.send(b"wakeup")

def listener(gameVar):
    """This is a threaded function that allows for the client to listen for messages from the server
        while the gamesetup loop is running in a sepearte thread. This was put in due to the message_listener
        main loop not proccessing quit messages and options while gamesetup is taking place
    """
    while not gameVar.stop_event.is_set(): # loop continues untill stop_event is set, thus ending the thread
        message = clientlib.wait_for_message_signaled(gameVar.conn, gameVar.signal_sock_recv)#Special wait_for_message, allows for the thread to be terminated through a internal signal
        if message: 
            msg_type = message.get('msg_type')
            if msg_type == 'message': # Proccesses non gameover server messages
                print(message.get('data'))

            if msg_type == 'gameover': # Listens for gameover message, sets variables to let other threads end 
                gameVar.flag = True
                gameVar.stop_event.set()

def game_over(gameVar):
    """"Determines if player wants to play again after the game is over or a disconnected other player"""
    message = input("Play Again? (y or n): ").strip().lower()
    if message == "y":
        try:
            gameVar.set_restart_flag() # Sets the flag so that start() will know to restart
        except Exception as e:
            print(f"Error restarting the game: {e}")
    else: # Closes and exits the game if player doenst choose y
        print("Exiting the game...")
        clientlib.close_socket(gameVar.conn)


def message_listener(gameVar):
    """Main Listening loop that determines actions based on messages from the Server"""
    while True:
        # This is a server driven loop. Loop will only progress when a message is received from the server
        message = clientlib.wait_for_message(gameVar.conn)     
        if message:
            try:
                msg_type = message.get('msg_type') # Gets the message type from the message to determine what to do
                
                #if msg_type == 'quit':
                #    clientlib.close_socket(gameVars.conn)

                if msg_type == "game_init": 
                    """game_init is the setup phase to palce pieces of the game"""
                    print(message['data'])  # "Place Your Pieces" from the server
                    # prints player names
                    players = message.get('players', {})
                    print(f"Player 1: {players.get('player1', 'Unknown')}")
                    print(f"Player 2: {players.get('player2', 'Unknown')}")

                    # Creates a new board and creates a gameState object that will be used for tracking the game boards
                    new_board = gameStatics.create_empty_board()
                    gameVar.gameState = GameStateClient(new_board, gameVar)

                    """Creates two threads, one for placing pieces and the other for listening to server messages.
                        This was done as placing pieces can take a while, and the main listening loop will not 
                        proccess this information until pieces are set""" 
                    placement_thread = threading.Thread(target=gameVar.gameState.place_pieces)
                    listener_thread = threading.Thread(target=listener, args=(gameVar,))
                    placement_thread.start()
                    listener_thread.start()
                    placement_thread.join()
                    gameVar.stop_event.set() # Sets the event after placement is done to tell the Listener to stop
                    trigger_signal(gameVar.signal_sock_send) # Sends a signal to the Listener so the loop will continue and terminate with the event_flag
                    listener_thread.join()

                    #Determines if a gameover was recieved
                    if gameVar.flag == True:
                        game_over(gameVar)
                        break

                    # Sends a signal to the server informing it that the pieces are set and the player is ready
                    clientlib.send_message(gameVar.conn, {"msg_type": "game_init", "data": "set"})
                    print("Please Wait")
                
                # if a gameover is recieved by the main loop, not the sub-listener, end the game
                if msg_type == "gameover":
                    print(message.get('data'))
                    game_over(gameVar)
                    break
    
                if msg_type == "gameplay":
                        """Loop for handling the turns for guessing and checking"""
                        msg_data = message.get('data')
                        json_mess = message.get('message')

                        if msg_data == "turn": # Indicates that is the players turn
                            print(gameStatics.print_board(gameVar.gameState.guess_board)) # Shows where the player has previously guessed
                            while(True):
                                print(json_mess + "\n")
                                # Gets row and column data, checks for an escape command, then verifies that they are legitmate moves
                                guess_column = clientlib.inputValidation("Enter Column Guess\n", "num", gameVar.conn)
                                guess_row = clientlib.inputValidation("Enter Row Guess\n", "num", gameVar.conn)
                                guess_check = gameStatics.guess_checker(gameVar.gameState.guess_board, guess_column, guess_row)
                                
                                if guess_check: # If the move is valid, send to server and breaks the inner loop
                                    guess = str(guess_column) + "," + str(guess_row)
                                    clientlib.send_message(gameVar.conn, {"msg_type": "gameplay", "data": guess})
                                    break

                        if msg_data == "guess": # This tells the player that the other player has guessed and starts the check to determine a hit or miss
                            # Parses the guess which is formated like 1,1
                            guess_array = json_mess.split(",")
                            guess_column = int(guess_array[0])
                            guess_row = int(guess_array[1])
                            # Method to check the guess, provides 
                            gameVar.gameState.board, message, is_over = gameStatics.checker(gameVar.gameState.board, guess_column, guess_row)
                            
                            if is_over == True: # bool returned from the checker indentifying whether all ships have been sunk or not
                                clientlib.send_message(gameVar.conn, {"msg_type": "gamestate", "data": "No More Ships :("})
                            # Sends hit/miss information if the game is not over    
                            clientlib.send_message(gameVar.conn, {"msg_type": "gameplay", "data": message})

                        if msg_data == "answer":
                            # Response containing hit/miss information
                            answer_unfiltered = message
                            guess = answer_unfiltered.get('guess')
                            guess_array = guess.split(",")

                            guess_column = int(guess_array[0])
                            guess_row = int(guess_array[1])
                            answer = answer_unfiltered.get('message')

                            print(answer) # Prints the hit/miss and if a ship has been sunk
                            gameStatics.print_board(gameVar.gameState.board) # Shows the players ship board

                            gameVar.gameState.guess_board = gameStatics.add_to_guess_board(gameVar.gameState.guess_board, guess_column, guess_row, answer) # Adds the hit or miss information to the guess board                   
                else: # Catch for messages that dont fit the format
                    print(f"Server message: {message['data']}")

            # Generic error catches for sockets and json parsing
            except json.JSONDecodeError as e: 
                print(f"Error decoding message from server: {e}")
            except socket.error as e:
                return None
                        
       


id = "127.0.0.1" + ":" + "12345"
id = "~/457/ClassProject/457classProject/logs/" + id
log_path = os.path.expanduser(id)
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[logging.FileHandler(log_path, mode='w')]
)



def start():    
    print(r"""
                                __/___            
                    _____/______|           
            _______/_____\_______\_____     
            \              < < <       |    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    B A T T L E S H I P
    """)

    # Socket Creation from command line input
    ip = args.ip
    port = args.port
    s_conn = clientlib.connObject(ip, port)

    # Sets a object to hold important game_session relate variables, allows accesing by ctl-c method
    global gameVar
    gameVar = GameSession(s_conn, logger)
    print("Waiting for Players")

    # Waits for another player to be connected, currently options and other inputs are not accepted
    message = clientlib.wait_for_message(gameVar.conn)

    # Sends a joing message after user sets their usernamne
    if message:
        name = input(message['data']) 
        clientlib.send_message(s_conn, {"msg_type": "join", "data": name})

    # Starts the main listening loop for communications
    message_listener(gameVar)

    # Determines if game loop should restart after user input at the end of a game
    if gameVar.restart_flag == True:
        gameVar.reset()
        start()


# Sets logging    
logger = logging.getLogger(__name__)

# Parses Command line input
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--ip", required=True)
parser.add_argument("-p", "--port", type=int, required=True)
args = parser.parse_args()

# Start of program
start()
