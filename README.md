# Battleship Game

This is a simple Battleship game implemented using Python and sockets.

**Updates**
* Game now accepts inputs of -i and -p from the command line for ports and ips. Hostname also works in place of ip

* Game now properly ends when one player has one. Server sends a gameover message to the clients that allow for a graceful shutdown

* Code runs properly after completely removing refrences to clientGameState

* Menu functions added, however do not work properly


**How to play:**
1. **Start the server:** Run the `server.py` with the port wanted for the server script. e.x python3 server.py -p 12345
2. **Connect clients:**  Run the `client.py` script on two different machines or terminals with the ip and port of the server e.x. python3 client.py -i helena -p 12345
3. **Play the game:** Players take turns entering their moves, after setting their pieces. 

**Technologies used:**
* Python
* Sockets
* Threading

**Message Protocols**
* chat
  Used to pass non-game or server option messages between clients 
* command(WORK IN PROGRESS)
  * quit
    Quits the game, closes connections, sends other player message telling the game has ended and removes game from acti    ve games
  * current_games 
    Lists number of active games and the player names of each game
  * partner_connections
    Lists socket information of both clients in the asking clients game
* gameplay
    will tell the server of the update board, guess for ship location and other game specific information
* game_init 
    The servers sends a game_init message to tell the clients to start a new board and have the players set there pieces  
* game_over
    The losing client sends a game_over message to the server, which relays this to the winning client

**Files Included**
* server.py       -- Acts the middle man between two clients. Takes requests and processes the game.
* serverlib.py    -- Contains methods for use by server.py and gamesetup.py
* gamesetup.py    -- Contains the script for the game
* client.py       -- Contains the main script for sending and receiving information from the sever and displaying it for*                    the user
* clientlib       -- Contains the methods for client.py to run
* clientGameState -- ** REMOVED ** placing, validation and guessing placed in client code
* gameStatics     -- Contains statics such as game rules and piece information and the checking for valid placements and*                    moves
* GameStateClient -- Contains the code for setting peices on the board for the clients

**Additional resources:**
* [Link to Python documentation]
* [Link to sockets tutorial]
    
