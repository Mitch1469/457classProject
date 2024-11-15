import clientlib
import logging
import sys
import os
import json

import selectors
import argparse
import threading
import time
import socket
import gameStatics
from GameStateClient import GameStateClient

gameState = None


def message_listener(s_conn):
    tmp = 0
    while True:
        message = clientlib.wait_for_message(s_conn)
        if message != None:
            print(message)      
        if message:
            try:
                message_json = message
                msg_type = message_json.get('msg_type')

                if msg_type == 'chat':
                    print(f"Chat message: {message_json['data']}")
                if msg_type == 'message':
                    print(f"Server_Message: {message_json['data']}")
                if msg_type == 'quit':
                    print(f"Server_Message: {message_json['data']}")
                    s_conn.close()
                    os._exit(0)
                if msg_type == "game_init":
                    new_board = gameStatics.create_empty_board()
                    gameState = GameStateClient(new_board)
                    gameState.place_pieces()
                    clientlib.send_message(s_conn, {"msg_type": "game_init", "data": "set"})
                
                if msg_type == "gameover":
                    print(message_json.get('data'))
                    clientlib.close_socket(s_conn)
                if msg_type == "gameplay":
                        msg_data = message_json.get('data')
                        json_mess = message_json.get('message')
                        if msg_data == "turn":
                            print(gameStatics.print_board(gameState.guess_board))
                            while(True):
                                print(json_mess + "\n")
                                guess_column = int(input("Enter Column Guess\n"))
                                guess_row = int(input("Enter Row Guess\n"))
                                guess_check = gameStatics.guess_checker(gameState.guess_board, guess_column, guess_row)
                                if guess_check:
                                    guess = str(guess_column) + "," + str(guess_row)
                                    clientlib.send_message(s_conn, {"msg_type": "gameplay", "data": guess})
                                    break                        
                        if msg_data == "guess":
                            guess_array = json_mess.split(",")
                            guess_column = int(guess_array[0])
                            guess_row = int(guess_array[1])
                            gameState.board, message, gamestate = gameStatics.checker(gameState.board, guess_column, guess_row)
                            if gamestate == True:
                                clientlib.send_message(s_conn, {"msg_type": "gameplay", "data": message, "gamestate": "gameover"})
                                continue
                            clientlib.send_message(s_conn, {"msg_type": "gameplay", "data": message})
                        if msg_data == "answer":
                            answer_unfiltered = message
                            guess = answer_unfiltered.get('guess')
                            guess_array = guess.split(",")
                            guess_column = int(guess_array[0])
                            guess_row = int(guess_array[1])
                            answer = answer_unfiltered.get('message')
                            print(answer)
                            gameStatics.print_board(gameState.board)
                            gameState.guess_board = gameStatics.add_to_guess_board(gameState.guess_board, guess_column, guess_row, answer)                   
                else:
                    print(f"Server message: {message_json['data']}")

            except json.JSONDecodeError as e:
                print(f"Error decoding message from server: {e}")
       
       

def message_loop(s_conn):
    listener_thread = threading.Thread(target=message_listener, args=(s_conn,))
    listener_thread.daemon = True
    listener_thread.start()
    while True:
        try:
            n_message = input("Enter a command or message:\n")
            if n_message.lower() in ["play", "quit", "options"]:
                if n_message.lower() == "quit":
                    clientlib.send_message(s_conn, {"msg_type": "command", "data": "quit"})
                    print("Quitting game...")
                    break
                if n_message.lower() == "options":
                     o_message = input("Show Current Games\n")
                     s_message = ""
                     if o_message == "current":
                         s_message = {"msg_type": "command", "data": "current_games"}
                     if o_message == "partner":
                         s_message = {"msg_type": "command", "data": "partner_connections"}
                     clientlib.send_message(s_conn, s_message)
            else:
                clientlib.send_message(s_conn, {"msg_type": "chat", "data": n_message})
        except Exception as e:
            print(f"An error occurred: {e}")
            break

id = "127.0.0.1" + ":" + "12345"
id = "~/457/ClassProject/457classProject/logs/" + id
log_path = os.path.expanduser(id)
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[logging.FileHandler(log_path, mode='w')]
)

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--ip", required=True)
parser.add_argument("-p", "--port", type=int, required=True)
args = parser.parse_args()

ip = args.ip


port = args.port
s_conn = clientlib.connObject(ip, port)

if s_conn:
    print(r"""
                                 __/___            
                       _____/______|           
               _______/_____\_______\_____     
               \              < < <       |    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                     B A T T L E S H I P
    """)
    print("Waiting for Players")
    message = clientlib.wait_for_message(s_conn)
    if message:
        name = input(message['data']) 
        clientlib.send_message(s_conn, {"msg_type": "join", "data": name})
    #message_loop(s_conn)
    message_listener(s_conn)

else:
    print("Failed to connect to server.")
