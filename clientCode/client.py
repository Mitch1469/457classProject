import clientlib
import logging
import sys
import os
import json
import selectors
import threading
import time
import gameStatics

def message_listener(s_conn):
    while True:
        message = clientlib.wait_for_message(s_conn)
        print(message)
        
        if message:
            print(message)
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
                    gameStatics.print_board(new_board)
                    
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
s_conn = clientlib.menu()

if s_conn:
    print("Waiting for Players")
    message = clientlib.wait_for_message(s_conn)
    if message:
        name = input(message['data']) 
        clientlib.send_message(s_conn, {"msg_type": "join", "data": name})
    message_loop(s_conn)

else:
    print("Failed to connect to server.")
