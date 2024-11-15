import logging
import socket
import selectors
import json
import sys
import ipaddress

sel = selectors.DefaultSelector()

def close_socket(sock):
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except (socket.error, OSError):
            pass  
        finally:
            sock.close()
            print("Game is Closing!")
            sys.exit()

def is_ip_address(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False

def connObject(ip, port):
    # server_ip = "127.0.0.1"
    # server_port = 12345
    try:
        if is_ip_address(ip) == False:
            ip = socket.gethostbyname(ip)
        addr = (ip, port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        result = sock.connect_ex(addr)
        if result == 115:
            logging.info(f"Connection established to {ip}:{port}")
            return sock
        else:
            logging.error(f"Connection issue")
            print("Connection Issue")
            sock.close()
            sys.exit()
    except socket.error as e:
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
    

