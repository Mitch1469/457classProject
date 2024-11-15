import sys
import os
import logging
import selectors
import serverlib
import argparse
from gamesetup import GameManager
from serverlib import ServerLib
from gamesetup import GameSetup

def main():
    ip = "0.0.0.0"
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=True)
    args = parser.parse_args()
    port = args.port
    log_path = os.path.expanduser("~/457/ClassProject/457classProject/logs/server.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_path, mode='w')]
    )

    logger = logging.getLogger(__name__)
    sel = selectors.DefaultSelector()
    serverlib.start_server(ip, port, sel)
    connections = []
    game_manager = GameManager()
    

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    s_sock = key.fileobj
                    conn, addr = serverlib.accept_connection(s_sock)
                    logger.info(f"Client connected from {addr}")
                    connections.append((conn, addr))
                    if len(connections) == 2:
                        conn1, addr1 = connections.pop(0)
                        conn2, addr2 = connections.pop(0)
                        connPair = ServerLib(conn1, addr1, conn2, addr2, logger)
                        game = GameSetup(connPair, sel, logger, game_manager)  
                        connPair.set_game(game) 
                        sel.register(conn1, selectors.EVENT_READ, data=connPair)
                        sel.register(conn2, selectors.EVENT_READ, data=connPair)
                        game.start_game()  


                else:
                    connPair = key.data  
                    connPair.exchange_data(sel)  
    except KeyboardInterrupt:
        logger.info("Server shutting down")
    finally:
        for conn, addr in connections:
            sel.unregister(conn)
            conn.close()
        logger.info("All connections closed.")

if __name__ == "__main__":
    main()
