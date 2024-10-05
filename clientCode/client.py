import clientlib
import logging
import sys
import os

ip = sys.argv[1]
port = int(sys.argv[2])

id = ip + ":" + str(port)
id = "~/457/ClassProject/457classProject/logs/" + id
log_path = os.path.expanduser(id)
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler(log_path, mode='w'),
    ]
)

logger = logging.getLogger(__name__)
s_conn = clientlib.menu()

if s_conn:
    print("Waiting for Players")
    message = clientlib.wait_for_message(s_conn)
    if message:
        name = input(message)
        clientlib.send_message(s_conn, name) 
    message = clientlib.wait_for_message(s_conn)
    if message:
        print(message) 
else:
    print("Failed to connect to server.")
