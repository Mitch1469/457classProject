import logging
import socket
import selectors
import json
import sys
import ipaddress

"""This contains methods relating to the cration of client-server sockets and sending and recieving data, returns
    a socket object to placed in the gameVar object used in the main loop"""

# Selector only for clientlib
sel = selectors.DefaultSelector()


def close_socket(sock): # Closes the socket and exits the game. Ungraceful at the moment
    send_message(sock, {"msg_type": "command", "data": "quit"}) # sends a quit message to the server so it can track the disconnect
    if sock: # helps if the server has already terminated the connection, but still gives heaps of errors
        try:
            sock.shutdown(socket.SHUT_RDWR) # Stops communications
        except (socket.error, OSError): # Ignores errors
            pass  
        finally: # closes socket and exits the program
            sock.close()
            print("Connection Closed!")
            logging.info(f"Connection to server Closed")
            sys.exit(0)
    


def connObject(ip, port):
    def is_ip_address(value): # Determines if the user given ip address is valid
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    try:
        if is_ip_address(ip) == False: # This attempts to resolve the hostname if its not valid ip, if hostname can be resolved returns that for connection. Otherwise closes the program
            try: 
                ip = socket.gethostbyname(ip)
            except socket.gaierror as e:
                print(f"Error: Unable to resolve hostname '{ip}'. {e}")
                logging.error(f"Connection issue")
                print("Connection Issue")
                sock.close()
                sys.exit()
        # Creation of the socket object
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False) # None blocking
        result = sock.connect_ex(addr)

        if result == 115: # Indicates that the connection is non-blocking mode and in progress, for this code that indicates a success
            logging.info(f"Connection established to {ip}:{port}")
            return sock
        
        else: # Closes program if socket failure
            logging.error(f"Connection issue")
            print("Connection Issue")
            sock.close()
            sys.exit()
    except socket.error as e:
        return None




def send_message(sock, message):
    """Method that all messages to the server are sent through"""
    try:
        # Converts to json
        json_message = json.dumps(message)
        try:
            # Attempt to retrieve the socket's key from the selector.
            # If it exists, modify the socket to monitor for write events.
            sel.get_key(sock)
            sel.modify(sock, selectors.EVENT_WRITE)
        except KeyError: # If the socket is not registered, register it for write events.
            sel.register(sock, selectors.EVENT_WRITE)
        # Wait for the socket to be ready for writing.
        events = sel.select()
        for key, mask in events:
            if mask & selectors.EVENT_WRITE:
                # If the socket is ready, send the JSON-encoded message.
                sock.sendall(json_message.encode('utf-8'))
                logging.info(f"Sent: {message}")
        sel.modify(sock, selectors.EVENT_READ)

    except socket.error as e:
        logging.error(f"Error sending message: {e}")


def wait_for_message_signaled(sock, signal_sock):
    """This works with the sub listener. This has the same function as the wait_for_message function
        but will also listen for an internal signal as well. This signal allows this methods main 
        loop to exit """
    # Registers the main socket
    try:
        sel.get_key(sock)
        sel.modify(sock, selectors.EVENT_READ)
    except KeyError:
        sel.register(sock, selectors.EVENT_READ)
    # registers the signal socket
    try:
        sel.get_key(signal_sock)
    except KeyError:
        sel.register(signal_sock, selectors.EVENT_READ)

    try:
        while True: # Wait for events from either the primary socket or the signal socket.
            events = sel.select(timeout=None) # Blocks until an event is detected, will wait indefiently.
            for key, mask in events:
                    if key.fileobj == sock and mask & selectors.EVENT_READ: # Handles main socket events
                        try:
                            data = sock.recv(1024)
                            if data:
                                json_data = json.loads(data.decode('utf-8'))
                                logging.info(f"Received: {data.decode('utf-8')}")
                                return json_data
                            else:
                                logging.warning("Connection closed by server.")
                                return None
                        except socket.error as e:
                            logging.error(f"Socket error: {e}")
                            return None
                        except json.JSONDecodeError as e:
                            logging.error(f"JSON decode error: {e}")
                            return None

                    elif key.fileobj == signal_sock and mask & selectors.EVENT_READ: # Handles signal socket
                        try:
                            # Read the signal and exit the loop
                            signal_sock.recv(1024)
                            logging.info("Received wake-up signal.")
                            return {"msg_type": "signal", "data": "wakeup"}
                        except socket.error as e:
                            logging.error(f"Signal socket error: {e}")
                            return None
    except socket.error as e:
        return None
                        
def wait_for_message(sock):
    """"This is seperate from the wait_for_message_signal to help with thread concurrency. Its main socket
        listening function indentical to the other. However it just doesnt"""
    try:
        sel.get_key(sock)
        sel.modify(sock, selectors.EVENT_READ)
    except KeyError:
        sel.register(sock, selectors.EVENT_READ)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                    if key.fileobj == sock and mask & selectors.EVENT_READ:
                        try:
                            data = sock.recv(1024)
                            if data:
                                json_data = json.loads(data.decode('utf-8'))
                                logging.info(f"Received: {data.decode('utf-8')}")
                                return json_data
                            else:
                                logging.warning("Connection closed by server.")
                                return None
                        except socket.error as e:
                            logging.error(f"Socket error: {e}")
                            return None
                        except json.JSONDecodeError as e:
                            logging.error(f"JSON decode error: {e}")
                            return None
                        except socket.error as e:
                            logging.error(f"Signal socket error: {e}")
                            return None
    except socket.error as e:
        return None

def inputValidation(message, type, s_conn):
    """This detects requests for options or quitting for all input in the main game loop
        Type variable is used for to verify integers"""
    n_message = input(message) # Gets the input
    if n_message.lower() in ["quit", "options"]:
        if n_message.lower() == "quit": # "Gracefully" closes the game
            print("Quitting game...")
            close_socket(s_conn)

        if n_message.lower() == "options": # Shows further options 
                o_message = input("Show Current Games(1)\nShow partner information(2)\n")
                s_message = ""
                if o_message == "1":
                    s_message = {"msg_type": "command", "data": "current_games"}
                if o_message == "2":
                    s_message = {"msg_type": "command", "data": "partner_connections"}
                send_message(s_conn, s_message) #Sends option request to the server
                return inputValidation(message, type, s_conn) # returns to get input for the main the gameloop
        
    if type == "num": # Used if a integer value is expected, verifies that it is valid
        try:
            n_message = int(n_message) 
            return n_message # returns a valid int value
        except ValueError:
            print("Not a valid number")
            return inputValidation(message, type, s_conn) #Asks for reinput
    return

    

