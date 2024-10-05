# server.py
import sys
import os
import logging
import socket
import selectors
from serverlib import ServerLib 
import serverlib
import gamesetup

ip = sys.argv[1]
port = int(sys.argv[2])

log_path = os.path.expanduser("~/457/ClassProject/457classProject/logs/server.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler(log_path, mode='w'),
    ]
)

logger = logging.getLogger(__name__)

sel = selectors.DefaultSelector()



serverlib.start_server(ip, port, sel)

connections = []

try:
    while True:
        events = sel.select(timeout=None)
        for a, b in events:
            if a.data is None:
                s_sock = a.fileobj
                conn, addr = serverlib.accept_connection(s_sock)
                logger.info(f"Client connected from {addr}")
                connections.append((conn, addr))

                if len(connections) == 2:
                    conn1, addr1 = connections.pop(0)
                    conn2, addr2 = connections.pop(0)
                    connPair = ServerLib(conn1, addr1, conn2, addr2, logger)
                    sel.register(conn1, selectors.EVENT_READ | selectors.EVENT_WRITE, data=connPair)
                    sel.register(conn2, selectors.EVENT_READ | selectors.EVENT_WRITE, data=connPair)
                    gamesetup.game_setup(connPair, sel)
            else:
                connPair = a.data  
                try:
                    connPair.exchange_data(sel)
                except Exception as e:
                    logger.error(f"Error with connection {connPair}: {e}")
                    connPair.close(sel)
                    connPair.close(sel)
                
except KeyboardInterrupt:
    logger.info("Server shutting down")
