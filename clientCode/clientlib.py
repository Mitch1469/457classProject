import logging
import socket
import selectors

sel = selectors.DefaultSelector()

def connObject():
    server_ip = input("Enter Server IP\n")
    server_port = input("Enter Server port\n")
    server_port = int(server_port)
    try:
        addr = (server_ip, server_port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(addr)
        logging.info(f"Connection established to {server_ip}:{server_port}")
        return sock
    except socket.error as e:
        logging.error(f"Connection issue: {e}")
        return None

def menu():
    logging.info("Displaying menu options")
    print("BATTLESHIPS\nPlay\nNetwork Configuration\nQuit\n")
    selection = input("Make Selection\n")
    if selection == "Play" or "Network Configuration" or "Quit":
        s_conn = menu_handler(selection)
        return s_conn

def menu_handler(selection):
    if selection == "Play":
        logging.info(f"Selected option: {selection}")
        s_conn = connObject()
        return s_conn

def send_message(sock, message):
    try:
        try:
            sel.get_key(sock)
            sel.modify(sock, selectors.EVENT_WRITE)
        except KeyError:
            sel.register(sock, selectors.EVENT_WRITE)
        events = sel.select()
        for key, mask in events:
            if mask & selectors.EVENT_WRITE:
                sock.sendall(message.encode('utf-8'))
                logging.info(f"Sent: {message}")
        sel.modify(sock, selectors.EVENT_READ)

    except socket.error as e:
        logging.error(f"Error sending message: {e}")
        return False
    return True

def wait_for_message(sock):
    try:
        sel.get_key(sock)
        sel.modify(sock, selectors.EVENT_READ)
    except KeyError:
        sel.register(sock, selectors.EVENT_READ)
    events = sel.select()
    for key, mask in events:
        if mask & selectors.EVENT_READ:
            try:
                data = sock.recv(1024)
                if data:
                    logging.info(f"Received: {data.decode('utf-8')}")
                    return data.decode('utf-8')
                else:
                    logging.warning("Connection closed by server.")
                    return None
            except socket.error as e:
                logging.error(f"Socket error: {e}")
                return None
    return None
