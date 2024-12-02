import os
import logging
import selectors
import serverlib
from threading import Thread
import argparse
from gamesetup import GameManager
from collections import deque
from serverlib import ServerLib
from gamesetup import GameSetup


def game_thread(game):
    game.start_game()

def main():
    """Start point for the prgram, sets up socket, logger and creates a listening loop for incoming clients"""
    # Connection variables and socket creation
    ip = "0.0.0.0"
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=True)
    args = parser.parse_args()
    port = args.port

    # Logger creation
    log_path = os.path.expanduser("~/457/ClassProject/457classProject/logs/server.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_path, mode='w')]
    )

    logger = logging.getLogger(__name__)
    
    # Starts the server
    sel = selectors.DefaultSelector()
    serverlib.start_server(ip, port, sel)

    # Object and ques for managing games and connections
    connections = deque() # deque worked better than a simple array, tracks connections waiting for a game
    game_manager = GameManager() 
    

    

    try: # Listening loop
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    # New client connection
                    s_sock = key.fileobj
                    conn, addr = serverlib.accept_connection(s_sock)
                    logger.info(f"Client connected from {addr}")
                    connections.append((conn, addr))  # Add the connection to the queue

            if len(connections) >= 2: # If there are two connections in the que remove them from the connections
                conn1, addr1 = connections.popleft()
                conn2, addr2 = connections.popleft()
                connPair = ServerLib(conn1, addr1, conn2, addr2, logger) # Create a object containing the connection information
                game = GameSetup(connPair, logger, game_manager) # New game object

                connPair.set_game(game) # Circular refrence for connection object and game
                game_manager.add_game(game) # adds to game_manager so games can be accurately tracked by the game_manager
                
                # Starts a thread with connPair and game, allows listening loop it continue
                thread = Thread(target=game_thread, args=(game,))
                thread.start()
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    finally:
        for conn, addr in connections:
            sel.unregister(conn)
            conn.close()
        logger.info("All connections closed.")

if __name__ == "__main__":
    main()
