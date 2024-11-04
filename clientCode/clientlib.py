import logging
import socket
import selectors
import json

sel = selectors.DefaultSelector()

def connObject(ip, port):
    # server_ip = "127.0.0.1"
    # server_port = 12345
    try:
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(addr)
        logging.info(f"Connection established to {ip}:{port}")
        return sock
    except socket.error as e:
        logging.error(f"Connection issue: {e}")
        return None




def send_message(sock, message):
    try:
        json_message = json.dumps(message)
        try:
            sel.get_key(sock)
            sel.modify(sock, selectors.EVENT_WRITE)
        except KeyError:
            sel.register(sock, selectors.EVENT_WRITE)
        events = sel.select()
        for key, mask in events:
            if mask & selectors.EVENT_WRITE:
                sock.sendall(json_message.encode('utf-8'))
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
    return None
