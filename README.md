# Battleship Game

This is a simple Tic-Tac-Toe game implemented using Python and sockets.

**How to play:**
1. **Start the server:** Run the `server.py` with the ip and port wanted for the server script.
2. **Connect clients:**  Run the `client.py` script on two different machines or terminals and follow the instructions     **                    to connect and play
3. **Play the game:** Players take turns entering their moves. 

**Technologies used:**
* Python
* Sockets

**Message Protocols**
* chat
  Used to pass non-game or server option messages between clients 
* command
  * quit
    Quits the game, closes connections, sends other player message telling the game has ended and removes game from acti    ve games
  * current_games 
    Lists number of active games and the player names of each game
  * partner_connections
    Lists socket information of both clients in the asking clients game
***FUTURE PROTOCOLS***
  * game
    will tell the server of the update board, guess for ship location and other game specific information
  
**Files Included**
* server.py       -- Acts the middle man between two clients. Takes requests and processes the game.
* serverlib.py    -- Contains methods for use by server.py and gamesetup.py
* gamesetup.py    -- Contains the script for the game
* client.py       -- Contains the main script for sending and receiving information from the sever and displaying it for*                    the user
* clientlib       -- Contains the methods for client.py to run
* clientGameState -- Contains the clients gamestate -- work in progress
* gameStatics     -- Contains statics such as game rules and piece information

**Additional resources:**
* [Link to Python documentation]
* [Link to sockets tutorial]
    
