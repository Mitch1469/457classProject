import sys
import socket
import selectors
import serverlib
import serverlib

def game_setup(connPair, sel):
    message = "Enter a Username\n"
    serverlib.send_all(connPair, message)
    serverlib.wait_for_responses(connPair, sel)
    connPair.conn1name = connPair.responses[connPair.conn1]
    connPair.conn2name = connPair.responses[connPair.conn2]
    message = f"Player 1 username: {connPair.conn1name}\n"
    message += f"Player 2 username: {connPair.conn2name}"
    serverlib.send_all(connPair, message)

